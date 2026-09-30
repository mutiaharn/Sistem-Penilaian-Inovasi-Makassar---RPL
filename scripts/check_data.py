"""
Periksa ketersediaan data bukti + bantu pemetaan bukti -> indikator.

Untuk setiap PDF di data/raw/evidence/, script ini melaporkan:
  - sha256, ukuran, jumlah halaman, status scan
  - usulan evidence_tag berdasarkan kata kunci teks dokumen
  - usulan indicator_id yang cocok dengan tag tersebut (dari katalog indikator)

Usulan ini HANYA alat bantu. Pemetaan final tetap harus dikonfirmasi manusia
lewat formulir pengajuan, lalu disimpan di data/reference/evidence_manifest.json.

Pemakaian:
    python scripts/check_data.py
    python scripts/check_data.py --write-draft   # tulis evidence_manifest.draft.json
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader

from app.core.config import settings

# Kata kunci -> tag bukti. Urutan penting: yang lebih spesifik diletakkan lebih dulu.
TAG_KEYWORDS: list[tuple[str, list[str]]] = [
    ("rkpd", ["rencana kerja pemerintah daerah", "rkpd"]),
    ("dpa_rka", ["dokumen pelaksanaan anggaran", "rkas", "rencana kerja dan anggaran", "rka skpd"]),
    ("regulasi", ["peraturan wali kota", "peraturan daerah", "perwali", "perda", "peraturan bupati"]),
    ("sk_tim", ["tim inovasi", "susunan tim", "tim kerja", "tim efektif", "pembentukan tim"]),
    ("sk_pelaksana", ["pelaksana operasional", "penetapan pelaksana"]),
    ("skb_jejaring", ["keputusan bersama", "skb", "lintas dinas", "berita acara pemanfaatan"]),
    ("pks_mou", ["perjanjian kerja sama", "naskah perjanjian", "nota kesepahaman", "memorandum", "mou"]),
    ("replikasi", ["replikasi", "kaji tiru", "alih teknologi"]),
    ("notula_bimtek", ["bimbingan teknis", "bimtek", "notula", "daftar hadir", "workshop", "fgd"]),
    ("sop_sla", ["standar pelayanan", "standar operasional prosedur", "sla", "flowchart", "waktu penyelesaian"]),
    ("sop_manual", ["manual book", "manual", "petunjuk teknis", "petunjuk operasional", "sop"]),
    ("portal_informasi", ["layanan informasi", "portal", "website", "hotline"]),
    ("rekap_pengaduan", ["pengaduan", "komplain", "sp4n", "lapor"]),
    ("integrasi_sistem", ["integrasi", "interoperabilitas", "single sign", "sso", "rest api"]),
    ("sosialisasi_media", ["sosialisasi", "undangan", "publikasi"]),
    ("laporan_monev", ["monitoring dan evaluasi", "monev", "survei kepuasan", "skm"]),
    ("rekap_penerima", ["buku tamu", "penerima manfaat", "register penerima", "jumlah pengguna"]),
    ("milestone", ["milestone", "kronologi", "uji coba", "peluncuran"]),
    ("rancang_bangun", ["rancang bangun", "proposal inovasi", "latar belakang masalah"]),
]

SKIP_KEYWORDS = ["logo", "ppt", "presentasi kelompok"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path, max_pages: int = 4) -> str:
    try:
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages[:max_pages]:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception:  # noqa: BLE001
        return ""


def suggest_tag(text: str) -> tuple[str | None, str | None]:
    low = text.lower()
    for tag, keywords in TAG_KEYWORDS:
        for kw in keywords:
            if kw in low:
                return tag, kw
    return None, None


def tag_to_indicator(catalog: dict) -> dict[str, str]:
    mapping = {}
    for ind in catalog["indicators"]:
        for tag in ind.get("evidence_tags") or []:
            mapping.setdefault(tag, ind["id"])
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Cek data bukti & usulan pemetaan indikator")
    parser.add_argument("--dir", default=str(settings.DOCUMENTS_DIR))
    parser.add_argument("--write-draft", action="store_true",
                        help="Tulis data/reference/evidence_manifest.draft.json")
    args = parser.parse_args()

    src = Path(args.dir)
    files = sorted([p for p in src.iterdir() if p.suffix.lower() in (".pdf", ".png")]) if src.exists() else []

    print(f"Direktori        : {src}")
    print(f"Berkas ditemukan : {len(files)}")
    if not files:
        print("\n[!] Data bukti belum ada. Lihat data/raw/README.md untuk cara mendapatkannya.")
        return 1

    catalog = settings.load_indicator_catalog()
    tag_map = tag_to_indicator(catalog)

    print(f"Katalog indikator: versi {catalog['version']} ({len(catalog['indicators'])} entri)")
    print("-" * 108)
    print(f"{'#':>3}  {'berkas':<50} {'hlm':>4} {'scan':>5}  {'tag usulan':<18} {'indikator':<9} kata kunci")
    print("-" * 108)

    evidences = []
    tanpa_tag = 0
    for i, path in enumerate(files, start=1):
        if any(s in path.name.lower() for s in SKIP_KEYWORDS):
            continue
        text = read_text(path)
        pages = 0
        try:
            pages = len(PdfReader(str(path)).pages)
        except Exception:  # noqa: BLE001
            pages = 1
        scanned = len(text.split()) < 30
        tag, kw = suggest_tag(text)
        if not tag:
            tanpa_tag += 1
        ind_id = tag_map.get(tag) if tag else None

        print(
            f"{i:>3}  {path.name[:50]:<50} {pages:>4} {('ya' if scanned else 'tidak'):>5}  "
            f"{(tag or '-'):<18} {(ind_id or '-'):<9} {kw or ''}"
        )

        evidences.append({
            "evidence_id": f"EVD-{len(evidences) + 1:04d}",
            "filename": path.name,
            "indicator_id": ind_id,
            "evidence_tag": tag,
            "sha256": sha256_of(path),
            "usulan_dari": kw,
            "perlu_konfirmasi_manusia": True,
            "catatan_pengaju": "",
        })

    print("-" * 108)
    print(f"Total terpetakan otomatis: {len(evidences) - tanpa_tag} | perlu dipetakan manual: {tanpa_tag}")

    if args.write_draft:
        draft = {
            "inovasi_id": "GANTI_DENGAN_ID_INOVASI",
            "manifest_version": "0.1-draft",
            "catatan": (
                "DRAFT OTOMATIS. indicator_id hasil tebak kata kunci BELUM DIVERIFIKASI. "
                "Wajib dikonfirmasi manusia dari formulir pengajuan, lalu disimpan sebagai "
                "data/reference/evidence_manifest.json"
            ),
            "evidences": evidences,
        }
        out = settings.REFERENCE_DIR / "evidence_manifest.draft.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
        print(f"\nDraft manifest ditulis ke: {out}")
        print("Langkah berikutnya: konfirmasi tiap baris, lalu simpan sebagai evidence_manifest.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
