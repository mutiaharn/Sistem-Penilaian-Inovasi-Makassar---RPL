"""
Ekspor lembar verifikasi (review sheet) ke CSV - untuk anotator manusia.

Dua bentuk lembar:

1. LEBAR (bawaan, disarankan untuk manusia)
   Satu baris = satu DOKUMEN. Ada kolom `mesin_<field>` (nilai dugaan sistem) dan
   `nilai_<field>` (yang Anda isi). Jadi Anda membuka PDF, membaca, lalu mengisi
   8 kolom dalam satu baris - tanpa menggulir 8 baris untuk satu dokumen.

   Cara mengisi kolom `nilai_<field>`:
     - tulis nilai benarnya, ATAU
     - tulis `=`  bila nilai mesin sudah benar (tetap wajib dibaca dulu PDF-nya), ATAU
     - tulis `-`  bila field itu memang TIDAK ADA di dokumen, ATAU
     - biarkan kosong bila belum diperiksa (dokumen tetap BELUM_DIVERIFIKASI).

2. PANJANG (--format panjang)
   Satu baris = satu FIELD (8 baris per dokumen). Berguna untuk menelusuri
   per-field, tetapi melelahkan untuk mengisi 33 dokumen.

Pemakaian:
    python scripts/make_review_sheet.py --prioritas          # surat dinas + keputusan
    python scripts/make_review_sheet.py --hanya-belum
    python scripts/make_review_sheet.py --jenis peraturan
    python scripts/make_review_sheet.py --satu c93b5421
    python scripts/make_review_sheet.py --format panjang --status BELUM_TERBACA_SCAN
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

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

# Urutan pengerjaan yang disarankan: jenis dokumen dengan field paling lengkap dulu,
# sehingga setiap dokumen yang selesai langsung menambah banyak titik data penilaian.
PRIORITAS_JENIS = [
    "surat_dinas",
    "keputusan",
    "surat_pernyataan",
    "peraturan",
    "laporan",
    "sertifikat",
    "anggaran",
    "manual_book",
    "bukti_media",
    "tidak_diketahui",
]

KOLOM_LEBAR = (
    ["no", "filename", "jenis_dokumen", "wilayah", "halaman"]
    + [f"mesin_{f}" for f in FIELDS]
    + [f"nilai_{f}" for f in FIELDS]
    + ["catatan", "berkas_pdf"]
)

KOLOM_PANJANG = [
    "no", "filename", "jenis_dokumen", "field", "nilai_mesin",
    "nilai_benar", "jelas_tidak_ada", "catatan", "berkas_pdf",
]

PETUNJUK = {
    "nomor_surat": "Nomor naskah, apa adanya (mis. 421.2/110/DISDIK/2025)",
    "instansi": "Nama instansi penerbit sesuai kop surat",
    "perihal": "Perihal / tentang / judul naskah",
    "tanggal_surat": "Tanggal naskah, format YYYY-MM-DD",
    "nama_pejabat": "Nama penanda tangan",
    "jabatan_pejabat": "Jabatan penanda tangan",
    "nip_pejabat": "NIP penanda tangan (angka saja)",
    "verification_url": "Tautan verifikasi TTE, bila ada di dokumen",
}


def muat_dataset() -> list[dict]:
    hasil = []
    for path in sorted(settings.extract_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            hasil.append(json.load(f))
    return hasil


def urut_prioritas(dok: dict) -> tuple:
    jenis = (dok.get("doc_type") or {}).get("jenis", "tidak_diketahui")
    idx = PRIORITAS_JENIS.index(jenis) if jenis in PRIORITAS_JENIS else len(PRIORITAS_JENIS)
    return (idx, dok.get("filename", ""))


def main() -> int:
    parser = argparse.ArgumentParser(description="Buat lembar verifikasi CSV")
    parser.add_argument("--status", default="", help="Filter verified.status, mis. BELUM_DIVERIFIKASI")
    parser.add_argument("--hanya-belum", action="store_true", help="Hanya berkas yang belum TERVERIFIKASI")
    parser.add_argument("--prioritas", action="store_true",
                        help="Hanya jenis dokumen yang paling cepat menambah titik data (surat dinas + keputusan)")
    parser.add_argument("--jenis", default="", help="Hanya satu jenis dokumen, mis. surat_dinas")
    parser.add_argument("--tanpa-luar-makassar", action="store_true",
                        help="Lewati dokumen di luar Kota Makassar (tidak dipakai sebagai acuan)")
    parser.add_argument("--satu", default="", help="Hanya satu berkas (potongan nama)")
    parser.add_argument("--format", choices=["lebar", "panjang"], default="lebar")
    parser.add_argument("--dengan-duplikat", action="store_true",
                        help="Ikutkan berkas ganda (isi identik). Bawaannya dilewati agar tidak "
                             "mengulang pekerjaan pada dokumen yang sama.")
    parser.add_argument("--keluar", default="", help="Nama berkas keluaran")
    args = parser.parse_args()

    semua = muat_dataset()
    if not semua:
        print(f"[!] Belum ada dataset di {settings.extract_dir}")
        return 1

    dipilih = []
    for dok in semua:
        status = (dok.get("verified") or {}).get("status", "")
        jenis = (dok.get("doc_type") or {}).get("jenis", "tidak_diketahui")
        wilayah = (dok.get("wilayah") or {}).get("kode", "")

        if args.hanya_belum and status == "TERVERIFIKASI":
            continue
        if args.status and status != args.status:
            continue
        if args.prioritas and jenis not in ("surat_dinas", "keputusan"):
            continue
        if args.jenis and jenis != args.jenis:
            continue
        if args.tanpa_luar_makassar and wilayah == "luar_kota_makassar":
            continue
        if args.satu and args.satu not in dok.get("filename", ""):
            continue
        if dok.get("duplikat_dari") and not args.dengan_duplikat:
            continue
        dipilih.append(dok)

    dipilih.sort(key=urut_prioritas)
    if not dipilih:
        print("[i] Tidak ada dokumen yang cocok dengan filter.")
        return 0

    baris: list[dict] = []
    for no, dok in enumerate(dipilih, start=1):
        dt = dok.get("doc_type") or {}
        wl = dok.get("wilayah") or {}
        mesin = dok.get("metadata", {})
        pdf = str(settings.DOCUMENTS_DIR / dok.get("filename", ""))

        if args.format == "lebar":
            baris.append({
                "no": no,
                "filename": dok.get("filename", ""),
                "jenis_dokumen": dt.get("jenis", ""),
                "wilayah": wl.get("kode", ""),
                "halaman": dok.get("page_count", ""),
                **{f"mesin_{f}": mesin.get(f, "") for f in FIELDS},
                **{f"nilai_{f}": "" for f in FIELDS},
                "catatan": "",
                "berkas_pdf": pdf,
            })
        else:
            for f in FIELDS:
                baris.append({
                    "no": no,
                    "filename": dok.get("filename", ""),
                    "jenis_dokumen": dt.get("jenis", ""),
                    "field": f,
                    "nilai_mesin": mesin.get(f, ""),
                    "nilai_benar": "",
                    "jelas_tidak_ada": "",
                    "catatan": PETUNJUK.get(f, ""),
                    "berkas_pdf": pdf,
                })

    bawaan = {
        ("lebar", True): "review_prioritas.csv",
        ("panjang", True): "review_prioritas_panjang.csv",
    }.get((args.format, bool(args.prioritas)), "")
    nama = args.keluar or bawaan or (
        "review_belum_diverifikasi.csv" if args.hanya_belum else "review_sheet.csv"
    )
    keluar = settings.DATASETS_DIR / nama
    keluar.parent.mkdir(parents=True, exist_ok=True)

    kolom = KOLOM_LEBAR if args.format == "lebar" else KOLOM_PANJANG
    # utf-8-sig supaya terbaca benar di Excel (Windows)
    with open(keluar, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=kolom)
        writer.writeheader()
        writer.writerows(baris)

    print(f"Bentuk lembar   : {args.format}")
    print(f"Berkas dokumen  : {len(dipilih)}")
    print(f"Baris           : {len(baris)}")
    print(f"Lembar verifikasi: {keluar.relative_to(settings.BASE_DIR)}")
    print()
    kosong = sum(1 for d in dipilih if not any((d.get("metadata") or {}).values()))
    if kosong:
        print(f"[i] {kosong} dokumen belum punya nilai mesin sama sekali - isi dari nol.")
    if args.format == "lebar":
        print("Cara mengisi (kolom nilai_<field>):")
        print("  - tulis nilai yang benar menurut PDF, ATAU")
        print("  - tulis '=' bila nilai mesin sudah benar (baca PDF-nya dulu), ATAU")
        print("  - tulis '-' bila field itu memang tidak ada di dokumen, ATAU")
        print("  - biarkan kosong bila belum diperiksa.")
        print("Kolom catatan bebas; berkas_pdf memuat lokasi PDF-nya.")
    else:
        print("Cara mengisi: isi kolom `nilai_benar`; tulis `ya` di `jelas_tidak_ada`")
        print("bila field memang tidak ada; biarkan kosong bila belum diperiksa.")
    print()
    print("Simpan sebagai CSV (bukan xlsx), lalu:")
    print(f"  python scripts/apply_review_sheet.py --masuk {nama} --anotator MAF --uji")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
