"""
Ekspor lembar verifikasi (review sheet) ke CSV - untuk anotator manusia.

Kenapa CSV, bukan JSON langsung: 41 berkas x 8 field = 328 baris. Mengedit JSON
satu per satu rawan salah dan melelahkan; CSV bisa dibuka di Excel/LibreOffice/
Google Sheets, diisi cepat, lalu diimpor kembali oleh apply_review_sheet.py.

Isi lembar:
  filename, field, nilai_mesin, nilai_benar(kosong), catatan(kosong)
  + kolom bantu: halaman_dokumen, teks_cuplikan (petunjuk saat mengisi)

Pemakaian:
    python scripts/make_review_sheet.py                    # semua berkas
    python scripts/make_review_sheet.py --hanya-belum      # hanya yang belum diverifikasi
    python scripts/make_review_sheet.py --status BELUM_DIVERIFIKASI
    python scripts/make_review_sheet.py --satu nama.pdf    # satu berkas saja
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

KOLOM = [
    "filename",
    "field",
    "nilai_mesin",
    "nilai_benar",       # <- DIISI ANOTATOR
    "jelas_tidak_ada",   # <- isi "ya" bila field memang tidak ada di dokumen
    "catatan",           # <- DIISI ANOTATOR
]

FIELDS = [
    "nomor_surat",
    "instansi",
    "perihal",
    "tanggal_surat",
    "nama_pejabat",
    "jabatan_pejabat",
    "nip_pejabat",
    "verification_url",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Buat lembar verifikasi CSV")
    parser.add_argument("--status", default="", help="Filter verified.status, mis. BELUM_DIVERIFIKASI")
    parser.add_argument("--hanya-belum", action="store_true", help="Hanya berkas yang belum TERVERIFIKASI")
    parser.add_argument("--satu", default="", help="Hanya satu berkas (nama file JSON/PDF)")
    parser.add_argument("--keluar", default="", help="Nama berkas keluaran")
    args = parser.parse_args()

    berkas = sorted(settings.extract_dir.glob("*.json"))
    if not berkas:
        print(f"[!] Belum ada dataset di {settings.extract_dir}")
        return 1

    baris: list[dict] = []
    diikutkan = 0

    for path in berkas:
        import json

        with open(path, "r", encoding="utf-8") as f:
            dok = json.load(f)

        status = (dok.get("verified") or {}).get("status", "")
        if args.hanya_belum and status == "TERVERIFIKASI":
            continue
        if args.status and status != args.status:
            continue
        if args.satu and args.satu not in dok["filename"]:
            continue

        diikutkan += 1
        cuplikan = " ".join((dok.get("text_excerpt") or "").split())[:180]
        for f in FIELDS:
            baris.append({
                "filename": dok["filename"],
                "field": f,
                "nilai_mesin": dok.get("metadata", {}).get(f, ""),
                "nilai_benar": "",
                "jelas_tidak_ada": "",
                "catatan": f"hlm={dok.get('page_count')} scan={'ya' if dok.get('is_scanned') else 'tidak'} | {cuplikan}",
            })

    if not baris:
        print("[i] Tidak ada baris yang cocok dengan filter.")
        return 0

    nama = args.keluar or ("review_sheet_belum_diverifikasi.csv" if args.hanya_belum else "review_sheet.csv")
    keluar = settings.DATASETS_DIR / nama
    keluar.parent.mkdir(parents=True, exist_ok=True)

    # utf-8-sig supaya terbaca benar di Excel (Windows)
    with open(keluar, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KOLOM)
        writer.writeheader()
        writer.writerows(baris)

    print(f"Berkas dokumen  : {diikutkan}")
    print(f"Baris (field)   : {len(baris)}")
    print(f"Lembar verifikasi: {keluar.relative_to(settings.BASE_DIR)}")
    print()
    print("Cara mengisi:")
    print("  1. Buka dengan Excel/LibreOffice/Google Sheets.")
    print("  2. Isi kolom `nilai_benar` dengan nilai yang benar menurut PDF-nya")
    print("     (bukti PDF ada di data/raw/evidence/).")
    print("  3. Bila field MEMANG tidak ada di dokumen, tulis `ya` di kolom")
    print("     `jelas_tidak_ada` dan biarkan `nilai_benar` kosong.")
    print("  4. Kolom `catatan` untuk keraguan/kasus batas.")
    print("  5. Simpan sebagai CSV (jangan .xlsx), lalu jalankan:")
    print(f"     python scripts/apply_review_sheet.py --masuk {nama}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
