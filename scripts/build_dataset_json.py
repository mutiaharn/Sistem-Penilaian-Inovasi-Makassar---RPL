"""
Bangun dataset JSON dari berkas bukti PDF  ->  data/datasets/evidence/<nama>.json

Ini menjawab kebutuhan "membuat JSON dari PDF untuk bahan pengembangan ML
penilaian indikator". Keluarannya mengikuti skema:
    data/schemas/idp_extraction.schema.json

Sifat script:
  - IDEMPOTENT & TIDAK menyentuh database. Menjalankan ulang hanya menimpa file
    JSON-nya. (Skrip seed lama menulis ke DB dan meninggalkan baris duplikat.)
  - Jika data/reference/evidence_manifest.json ada, hasil ekstraksi otomatis
    diikat ke innovation_id / indicator_id / evidence_tag.

Pemakaian:
    python scripts/build_dataset_json.py                 # semua PDF
    python scripts/build_dataset_json.py --limit 3       # uji cepat
    python scripts/build_dataset_json.py --force         # timpa file yang ada
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.pipeline.stage1_inspector import Stage1Inspector
from app.pipeline.stage2_preprocessor import Stage2Preprocessor
from app.pipeline.stage3_vision_extractor import Stage3VisionExtractor
from app.pipeline.stage4_qr_detector import Stage4QrDetector
from app.pipeline.stage5_post_validator import Stage5PostValidator
from app.pipeline.ocr import ocr_default

logger = logging.getLogger("idp.dataset_builder")

TEXT_EXCERPT_CHARS = 1500


def pilih_halaman_ocr(page_count: int, batas: int) -> list[int]:
    """Halaman mana yang di-OCR: awal dokumen, ditambah halaman terakhir.

    Nama pejabat/NIP/tanggal hampir selalu di halaman terakhir, sedangkan kop dan
    nomor surat di awal. batas=0 berarti semua halaman.
    """
    if batas <= 0 or batas >= page_count:
        return list(range(page_count))
    awal = list(range(min(batas, page_count)))
    if page_count - 1 not in awal:
        awal.append(page_count - 1)
    return awal


def read_all_text(pdf_path: Path) -> str:
    """Baca teks dari SELURUH halaman.

    Stage 1 (pipeline produksi) sengaja hanya membaca 3 halaman pertama agar cepat,
    tetapi untuk dataset hal itu membuang informasi penting: nama pejabat, NIP, dan
    tanggal tanda tangan hampir selalu berada di halaman terakhir. Membaca semua
    halaman di sini menghilangkan penyebab null yang paling besar.
    """
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(pdf_path))
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    except Exception:  # noqa: BLE001
        return ""


def load_manifest() -> dict[str, dict]:
    """Pemetaan filename -> info indikator, dibaca dari evidence_manifest.json."""
    path = settings.REFERENCE_DIR / "evidence_manifest.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["filename"]: e for e in data.get("evidences", [])}


def load_human_ground_truth() -> dict[str, dict]:
    """Anotasi manusia yang SUDAH ada (app/evaluation/ground_truth.json).

    Dipakai mengisi blok `verified` - bukan hasil karangan, melainkan anotasi
    yang memang sudah dikerjakan tim.
    """
    path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


METADATA_FIELDS = [
    "nomor_surat",
    "instansi",
    "perihal",
    "tanggal_surat",
    "nama_pejabat",
    "jabatan_pejabat",
    "nip_pejabat",
    "verification_url",
]

# Petunjuk mengapa sebuah field wajar tidak ada, supaya alasan tidak sekadar
# "tidak ditemukan" dan reviewer berikutnya tahu apa yang harus diperiksa.
FIELD_HINT = {
    "nomor_surat": "surat pernyataan, berita acara, lampiran, dan sertifikat sering tanpa nomor",
    "nip_pejabat": "surat non-kepegawaian atau naskah lama sering tidak mencantumkan NIP",
    "nama_pejabat": "dokumen tanpa blok tanda tangan (lampiran, tangkapan layar) tidak memuat nama",
    "jabatan_pejabat": "jabatan tidak selalu ditulis di bawah tanda tangan",
    "verification_url": "hanya dokumen ber-TTE/QR yang punya URL verifikasi",
    "instansi": "kop surat tidak terbaca / dokumen tanpa kop",
    "perihal": "banyak nota dinas dan lampiran tidak menuliskan perihal",
    "tanggal_surat": "tanggal tidak selalu tercetak (mis. lampiran, rekapitulasi)",
}


def _teks(nilai) -> str:
    """Normalisasi ke string; None menjadi string kosong (dataset tanpa null)."""
    return "" if nilai is None else str(nilai).strip()


def finalize(payload: dict, gt: dict) -> dict:
    """Rapikan satu record: tanpa null, ada alasan untuk field kosong, ada blok `verified`.

    Pemisahan `metadata` (output mesin) dan `verified` (nilai benar) disengaja:
    tanpa pemisahan itu, akurasi ekstraksi tidak bisa diukur lagi.
    """
    md_mesin = payload.get("metadata", {})
    scanned = bool(payload.get("is_scanned"))

    metadata: dict = {}
    tidak_ada: dict = {}
    for f in METADATA_FIELDS:
        metadata[f] = _teks(md_mesin.get(f))
        if not metadata[f]:
            sebab = (
                "dokumen hasil scan tanpa lapisan teks - belum ada OCR"
                if scanned
                else "tidak ditemukan pada teks dokumen - perlu verifikasi manusia"
            )
            hint = FIELD_HINT.get(f)
            tidak_ada[f] = f"{sebab}. Catatan: {hint}" if hint else sebab
    metadata["ada_stempel_basah"] = bool(md_mesin.get("ada_stempel_basah"))
    metadata["ada_tanda_tangan"] = bool(md_mesin.get("ada_tanda_tangan"))

    payload["metadata"] = metadata
    payload["field_tidak_ada"] = tidak_ada
    payload["document_id"] = payload.get("document_id") if payload.get("document_id") else ""
    payload["text_excerpt"] = payload.get("text_excerpt") or ""
    payload["manifest"] = payload.get("manifest") or {
        "inovasi_id": "",
        "indicator_id": "",
        "evidence_tag": "",
    }

    s4 = payload.get("pipeline", {}).get("stage4_qr", {})
    s4["verification_url"] = _teks(s4.get("verification_url"))
    s4["detector"] = _teks(s4.get("detector"))

    # --- Blok verified: hanya diisi dari anotasi manusia yang sudah ada --------
    if gt:
        values = {f: _teks(gt.get(f)) for f in METADATA_FIELDS}
        beda = [f for f in METADATA_FIELDS if values[f] and values[f] != metadata[f]]
        verified = {
            "status": "TERVERIFIKASI",
            "sumber": "anotasi_manual",
            "verified_by": "",
            "verified_at": "",
            "values": values,
            "berbeda_dari_mesin": beda,
        }
    else:
        verified = {
            "status": "BELUM_TERBACA_SCAN" if scanned else "BELUM_DIVERIFIKASI",
            "sumber": "",
            "verified_by": "",
            "verified_at": "",
            "values": {f: "" for f in METADATA_FIELDS},
            "berbeda_dari_mesin": [],
        }

    payload["verified"] = verified
    return payload


def build_one(
    pdf_path: Path,
    manifest_map: dict[str, dict],
    ocr_aktif: bool = True,
    ocr_halaman: int = 3,
) -> dict:
    """Jalankan pipeline 5 tahap untuk satu PDF dan susun payload sesuai skema."""
    inspector = Stage1Inspector()
    preprocessor = Stage2Preprocessor(target_dpi=300)
    extractor = Stage3VisionExtractor(settings.GEMINI_API_KEY)
    qr_detector = Stage4QrDetector()
    validator = Stage5PostValidator()

    meta = inspector.inspect(pdf_path)

    # Teks seluruh halaman (bukan hanya 3 halaman pertama seperti pipeline produksi)
    full_text = read_all_text(pdf_path) or meta["extracted_text"]
    text_source = "pdf_text_layer" if full_text.strip() else ""
    ocr_engine = ""

    # --- OCR lokal untuk dokumen tanpa lapisan teks (hasil scan) ---------------
    # Hanya dijalankan bila memang tidak ada teks sama sekali, dan hanya pada
    # jendela halaman tertentu (default 3) supaya waktu proses tetap wajar.
    if not full_text.strip() and ocr_aktif:
        ocr = ocr_default()
        if ocr.siap():
            indeks = pilih_halaman_ocr(meta["page_count"], ocr_halaman)
            teks_ocr, gambar_ocr = "", []
            for idx in indeks:
                try:
                    hasil = preprocessor.process(pdf_path, page_index=idx)
                    gambar_ocr.append(hasil["pil_image"])
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"halaman {idx + 1} gagal diraster: {exc}")
            if gambar_ocr:
                keluaran = ocr.proses_banyak(gambar_ocr)
                teks_ocr = keluaran.teks
                ocr_engine = keluaran.mesin
            full_text = teks_ocr.strip()
            text_source = "ocr" if full_text else ""
            meta["_ocr_halaman"] = [i + 1 for i in indeks]

    # --- Stage 2: rasterisasi halaman 1 dan halaman terakhir -------------------
    pages_rasterized: list[int] = [1]
    skew_angles: list[float] = []
    images = []

    p1 = preprocessor.process(pdf_path, page_index=0)
    images.append(p1["pil_image"])
    skew_angles.append(p1.get("skew_angle", 0.0))

    if meta["page_count"] > 1:
        last_idx = meta["page_count"] - 1
        pl = preprocessor.process(pdf_path, page_index=last_idx)
        images.append(pl["pil_image"])
        skew_angles.append(pl.get("skew_angle", 0.0))
        pages_rasterized.append(meta["page_count"])

    # --- Stage 3: ekstraksi semantik -------------------------------------------
    extracted = extractor.extract(
        text=full_text,
        pil_image=images[0] if images else None,
    )

    # --- Stage 4: QR / TTE ------------------------------------------------------
    verification_url = qr_detector.extract_verification_url(images)

    # --- Stage 5: validasi & skor keyakinan ------------------------------------
    is_valid_nip, healed_nip = validator.validate_and_heal_nip(
        raw_nip=extracted.nip_pejabat, full_text=full_text
    )
    iso_date = validator.normalize_indonesian_date(extracted.tanggal_surat)
    confidence, needs_review, flags = validator.evaluate_confidence(
        nomor_surat=extracted.nomor_surat,
        instansi=extracted.instansi,
        perihal=extracted.perihal,
        iso_tanggal=iso_date,
        cleaned_nip=healed_nip,
        is_valid_nip=is_valid_nip,
        verification_url=verification_url,
    )

    manifest = manifest_map.get(pdf_path.name)
    binding = None
    if manifest:
        binding = {
            "inovasi_id": manifest.get("inovasi_id"),
            "indicator_id": manifest.get("indicator_id"),
            "evidence_tag": manifest.get("evidence_tag"),
        }

    excerpt = full_text[:TEXT_EXCERPT_CHARS] or None

    return {
        "document_id": None,  # diisi bila diproses lewat API/DB
        "filename": pdf_path.name,
        "sha256": meta["file_hash"],
        "file_size_bytes": meta["file_size_bytes"],
        "page_count": meta["page_count"],
        "is_scanned": meta["is_scanned"],
        "manifest": binding,
        "pipeline": {
            "stage1_inspector": {
                "words_page_1": meta["words_page_1"],
                "is_scanned": meta["is_scanned"],
                "text_pages_read": meta["page_count"],
            },
            "stage2_preprocessing": {
                "target_dpi": 300,
                "pages_rasterized": pages_rasterized,
                "skew_angle_deg": round(max(skew_angles) if skew_angles else 0.0, 2),
            },
            "stage3_extraction": {
                "engine": extracted.source_engine,
                "text_source": text_source,          # pdf_text_layer | ocr | "" (tanpa teks)
                "ocr_engine": ocr_engine,            # rapidocr | tesseract | ""
                "field_confidence": _field_confidence(extracted, iso_date, healed_nip),
            },
            "stage4_qr": {
                "verification_url": verification_url,
                "detector": "pyzbar/opencv" if verification_url else None,
            },
            "stage5_validation": {
                "is_valid_nip": is_valid_nip,
                "confidence_score": confidence,
                "needs_manual_review": needs_review,
                "validation_flags": flags,
            },
        },
        "metadata": {
            "nomor_surat": extracted.nomor_surat,
            "instansi": extracted.instansi,
            "perihal": extracted.perihal,
            "tanggal_surat": iso_date or extracted.tanggal_surat,
            "nama_pejabat": extracted.nama_pejabat,
            "jabatan_pejabat": extracted.jabatan_pejabat,
            "nip_pejabat": healed_nip or extracted.nip_pejabat,
            "ada_stempel_basah": extracted.ada_stempel_basah,
            "ada_tanda_tangan": extracted.ada_tanda_tangan,
            "verification_url": verification_url,
        },
        "text_excerpt": excerpt,
    }


def _field_confidence(extracted, iso_date, healed_nip) -> dict:
    """Keyakinan kasar per field, diturunkan dari ada/tidaknya nilai hasil ekstraksi."""
    return {
        "nomor_surat": 0.8 if extracted.nomor_surat else 0.0,
        "instansi": 0.8 if extracted.instansi else 0.0,
        "perihal": 0.6 if extracted.perihal else 0.0,
        "tanggal_surat": 0.8 if iso_date else 0.0,
        "nip_pejabat": 0.9 if healed_nip else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF bukti -> dataset JSON")
    parser.add_argument("--limit", type=int, default=0, help="Batasi jumlah berkas (0 = semua)")
    parser.add_argument("--force", action="store_true", help="Proses ulang walau JSON sudah ada")
    parser.add_argument("--dir", default=str(settings.DOCUMENTS_DIR), help="Direktori berkas PDF")
    parser.add_argument("--satu", default="", help="Hanya berkas yang namanya memuat teks ini")
    parser.add_argument("--no-ocr", action="store_true", help="Matikan OCR untuk dokumen scan")
    parser.add_argument("--ocr-halaman", type=int, default=3,
                        help="Jumlah halaman awal yang di-OCR (0 = semua halaman)")
    args = parser.parse_args()

    ocr_aktif = not args.no_ocr

    src_dir = Path(args.dir)
    pdfs = sorted(src_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[!] Tidak ada PDF di {src_dir}")
        print("    Lihat data/raw/README.md untuk cara mendapatkan data bukti.")
        return 1

    if args.limit:
        pdfs = pdfs[: args.limit]
    if args.satu:
        pdfs = [p for p in pdfs if args.satu in p.name]
        if not pdfs:
            print(f"[!] Tidak ada berkas yang cocok dengan --satu '{args.satu}'")
            return 1

    out_dir = settings.extract_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_map = load_manifest()
    gt_map = load_human_ground_truth()
    if ocr_aktif:
        from app.pipeline.ocr import status_ocr

        st = status_ocr()
        print(f"OCR             : {st['mesin'] if st['siap'] else 'TIDAK TERSEDIA (dokumen scan akan dilewati)'}")
    if gt_map:
        print(f"Anotasi manusia terbaca: {len(gt_map)} berkas -> blok `verified` akan diisi")
    if manifest_map:
        print(f"Manifest terbaca: {len(manifest_map)} entri (pemetaan bukti -> indikator aktif)")
    else:
        print("[i] Belum ada data/reference/evidence_manifest.json -> kolom manifest dikosongkan.")
        print("    Jalankan: python scripts/check_data.py --write-draft")

    print("-" * 100)
    print(f"{'#':>3}  {'berkas':<52} {'hlm':>4} {'scan':>5} {'skor':>5} {'tgl':>11}  catatan")
    print("-" * 100)

    ok = skipped = failed = 0
    t0 = time.time()

    for i, pdf in enumerate(pdfs, start=1):
        out_file = out_dir / f"{pdf.stem}.json"
        if out_file.exists() and not args.force:
            skipped += 1
            print(f"{i:>3}  {pdf.name[:52]:<52} {'':>4} {'':>5} {'':>5} {'':>11}  (sudah ada, dilewati)")
            continue
        try:
            payload = finalize(
                build_one(pdf, manifest_map, ocr_aktif=ocr_aktif, ocr_halaman=args.ocr_halaman),
                gt_map.get(pdf.name, {}),
            )
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            md = payload["metadata"]
            st5 = payload["pipeline"]["stage5_validation"]
            stage3 = payload["pipeline"]["stage3_extraction"]
            sumber_teks = stage3.get("text_source", "")
            if payload["is_scanned"] and sumber_teks == "ocr":
                note = f"SCAN -> OCR ({stage3.get('ocr_engine') or '?'})"
            elif payload["is_scanned"]:
                note = "SCAN -> perlu OCR"
            elif st5["needs_manual_review"]:
                note = "perlu review"
            else:
                note = ""
            print(
                f"{i:>3}  {pdf.name[:52]:<52} {payload['page_count']:>4} "
                f"{('ya' if payload['is_scanned'] else 'tidak'):>5} "
                f"{int(st5['confidence_score'] * 100):>4}% "
                f"{(md['tanggal_surat'] or '-'):>11}  {note}"
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"{i:>3}  {pdf.name[:52]:<52} {'':>4} {'':>5} {'':>5} {'':>11}  ERROR: {exc}")

    print("-" * 100)
    print(f"Selesai dalam {time.time() - t0:.1f}s | berhasil: {ok} | dilewati: {skipped} | gagal: {failed}")
    print(f"Output: {out_dir}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
