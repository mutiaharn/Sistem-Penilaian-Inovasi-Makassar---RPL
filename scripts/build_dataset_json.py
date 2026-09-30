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

TEXT_EXCERPT_CHARS = 1500
TEXT_PAGES_READ = 3  # Stage 1 saat ini membaca maksimum 3 halaman pertama


def load_manifest() -> dict[str, dict]:
    """Pemetaan filename -> info indikator, dibaca dari evidence_manifest.json."""
    path = settings.REFERENCE_DIR / "evidence_manifest.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["filename"]: e for e in data.get("evidences", [])}


def build_one(pdf_path: Path, manifest_map: dict[str, dict]) -> dict:
    """Jalankan pipeline 5 tahap untuk satu PDF dan susun payload sesuai skema."""
    inspector = Stage1Inspector()
    preprocessor = Stage2Preprocessor(target_dpi=300)
    extractor = Stage3VisionExtractor(settings.GEMINI_API_KEY)
    qr_detector = Stage4QrDetector()
    validator = Stage5PostValidator()

    meta = inspector.inspect(pdf_path)

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
        text=meta["extracted_text"],
        pil_image=images[0] if images else None,
    )

    # --- Stage 4: QR / TTE ------------------------------------------------------
    verification_url = qr_detector.extract_verification_url(images)

    # --- Stage 5: validasi & skor keyakinan ------------------------------------
    is_valid_nip, healed_nip = validator.validate_and_heal_nip(
        raw_nip=extracted.nip_pejabat, full_text=meta["extracted_text"]
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

    excerpt = meta["extracted_text"][:TEXT_EXCERPT_CHARS] or None

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
                "text_pages_read": min(TEXT_PAGES_READ, meta["page_count"]),
            },
            "stage2_preprocessing": {
                "target_dpi": 300,
                "pages_rasterized": pages_rasterized,
                "skew_angle_deg": round(max(skew_angles) if skew_angles else 0.0, 2),
            },
            "stage3_extraction": {
                "engine": extracted.source_engine,
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
    args = parser.parse_args()

    src_dir = Path(args.dir)
    pdfs = sorted(src_dir.glob("*.pdf"))
    if not pdfs:
        print(f"[!] Tidak ada PDF di {src_dir}")
        print("    Lihat data/raw/README.md untuk cara mendapatkan data bukti.")
        return 1

    if args.limit:
        pdfs = pdfs[: args.limit]

    out_dir = settings.extract_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_map = load_manifest()
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
            payload = build_one(pdf, manifest_map)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            md = payload["metadata"]
            st5 = payload["pipeline"]["stage5_validation"]
            note = "SCAN -> perlu OCR" if payload["is_scanned"] else ""
            if st5["needs_manual_review"] and not note:
                note = "perlu review"
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
