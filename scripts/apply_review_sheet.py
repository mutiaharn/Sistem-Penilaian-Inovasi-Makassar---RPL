"""
Impor lembar verifikasi CSV yang sudah diisi anotator -> blok `verified` + ground truth.

Menulis ke DUA tempat sekaligus supaya tidak hilang:
  1. data/datasets/evidence/<berkas>.json  -> blok `verified` (label di dalam dataset)
  2. app/evaluation/ground_truth.json      -> acuan lama, dipakai benchmark & rebuild

Mendukung dua bentuk lembar (dibaca otomatis dari kepala kolom):
  - LEBAR : satu baris = satu dokumen, kolom `nilai_<field>`
  - PANJANG: satu baris = satu field, kolom `nilai_benar` + `jelas_tidak_ada`

Tahan terhadap Excel lokal:
  - pemisah kolom dideteksi otomatis (`,` / `;` / tab) - Excel Indonesia memakai `;`
  - tanggal yang diubah Excel (01/09/2025, 1 September 2025) dikembalikan ke YYYY-MM-DD
    dan setiap perubahan diberitahukan agar bisa diperiksa mata

Aturan kelengkapan: dokumen berstatus TERVERIFIKASI hanya bila SEMUA field punya
keputusan (diisi nilainya, ditandai `-`/`ya` karena tidak ada, atau `=`/nilai sama
dengan mesin). Kalau belum lengkap, statusnya tetap BELUM_DIVERIFIKASI dan field yang
belum diisi dilaporkan - supaya "setengah diverifikasi" tidak menyamar sebagai selesai.

Pemakaian:
    python scripts/apply_review_sheet.py --masuk review_prioritas.csv --anotator MAF --uji
    python scripts/apply_review_sheet.py --masuk review_prioritas.csv --anotator MAF
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.evaluation.metrics import FIELDS, normalisasi

WITA = timezone(timedelta(hours=8))

BULAN = {
    "januari": "01", "februari": "02", "maret": "03", "april": "04", "mei": "05",
    "juni": "06", "juli": "07", "agustus": "08", "september": "09", "oktober": "10",
    "november": "11", "desember": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "jun": "06", "jul": "07",
    "agu": "08", "agt": "08", "sep": "09", "okt": "10", "nov": "11", "des": "12",
}

TANDA_TIDAK_ADA = {"-", "--", "tidak ada", "tidak_ada", "n/a", "na"}
TANDA_SAMA_MESIN = {"=", "sama", "sama dengan mesin"}


def _waktu_sekarang() -> str:
    return datetime.now(WITA).isoformat(timespec="seconds")


def rapikan_tanggal(nilai: str) -> tuple[str, bool]:
    """Ubah tanggal gaya Excel menjadi YYYY-MM-DD. Mengembalikan (nilai, berubah)."""
    s = (nilai or "").strip()
    if not s:
        return s, False

    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, bl, tg = m.groups()
        baru = f"{y}-{int(bl):02d}-{int(tg):02d}"
        return baru, baru != s

    # 01/09/2025 atau 1-9-2025 -> konvensi Indonesia: TANGGAL/BULAN/TAHUN
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", s)
    if m:
        a, b, y = m.groups()
        tg, bl = int(a), int(b)
        if bl > 12 and tg <= 12:      # jelas tertukar (gaya Amerika)
            tg, bl = bl, tg
        return f"{y}-{bl:02d}-{tg:02d}", True

    # 1 September 2025 / 01-09-2025 yang ditulis dengan nama bulan
    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        tg, nama, y = m.groups()
        bl = BULAN.get(nama.lower())
        if bl:
            return f"{y}-{bl}-{int(tg):02d}", True

    return s, False


def deteksi_pemisah(baris_kepala: str) -> str:
    """Excel Indonesia menyimpan CSV dengan pemisah ';'."""
    hitung = {p: baris_kepala.count(p) for p in [",", ";", "\t"]}
    terbaik = max(hitung, key=lambda p: hitung[p])
    return terbaik if hitung[terbaik] > 0 else ","


def baca_lembar(path: Path) -> tuple[str, dict[str, dict[str, dict]]]:
    """CSV -> (bentuk, {filename: {field: {nilai, tidak_ada, catatan, dari_mesin}}})."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        kepala = f.readline()
        f.seek(0)
        pembaca = csv.DictReader(f, delimiter=deteksi_pemisah(kepala))
        kolom = pembaca.fieldnames or []

        if "nilai_benar" in kolom:
            bentuk = "panjang"
        elif any(f"nilai_{fld}" in kolom for fld in FIELDS):
            bentuk = "lebar"
        else:
            raise ValueError(
                "Kepala kolom tidak dikenali. Butuh `nilai_benar` (bentuk panjang) "
                f"atau `nilai_<field>` (bentuk lebar). Kolom terbaca: {kolom}"
            )

        hasil: dict[str, dict[str, dict]] = {}
        for row in pembaca:
            fname = (row.get("filename") or "").strip()
            if not fname:
                continue
            catatan_dok = (row.get("catatan") or "").strip()
            per_field = hasil.setdefault(fname, {})

            if bentuk == "panjang":
                fld = (row.get("field") or "").strip()
                if fld not in FIELDS:
                    continue
                mentah = (row.get("nilai_benar") or "").strip()
                tandai_tidak_ada = (row.get("jelas_tidak_ada") or "").strip().lower() in (
                    "ya", "y", "yes", "1", "true"
                )
                per_field[fld] = {
                    "mentah": mentah,
                    "tidak_ada": tandai_tidak_ada or mentah.lower() in TANDA_TIDAK_ADA,
                    "dari_mesin": mentah.lower() in TANDA_SAMA_MESIN,
                    "catatan": catatan_dok,
                }
            else:
                for fld in FIELDS:
                    mentah = (row.get(f"nilai_{fld}") or "").strip()
                    per_field[fld] = {
                        "mentah": mentah,
                        "tidak_ada": mentah.lower() in TANDA_TIDAK_ADA,
                        "dari_mesin": mentah.lower() in TANDA_SAMA_MESIN,
                        "catatan": catatan_dok,
                    }
    return bentuk, hasil


def main() -> int:
    parser = argparse.ArgumentParser(description="Impor lembar verifikasi CSV")
    parser.add_argument("--masuk", required=True, help="Nama/berkas CSV")
    parser.add_argument("--anotator", required=True, help="Inisial anotator, mis. MAF")
    parser.add_argument("--uji", action="store_true", help="Tampilkan rencana perubahan, jangan tulis")
    args = parser.parse_args()

    path = Path(args.masuk)
    if not path.is_absolute():
        kandidat = settings.DATASETS_DIR / args.masuk
        path = kandidat if kandidat.exists() else Path.cwd() / args.masuk
    if not path.exists():
        print(f"[!] Berkas lembar tidak ditemukan: {path}")
        return 1

    try:
        bentuk, lembar = baca_lembar(path)
    except ValueError as e:
        print(f"[!] {e}")
        return 1

    print(f"Lembar dibaca   : {path.name} ({len(lembar)} dokumen, bentuk {bentuk})")

    gt_path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    ground_truth = {}
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

    masuk = lengkap = 0
    belum_lengkap: list[tuple[str, list[str]]] = []
    semua_ubah_tanggal: list[str] = []
    semua_perlu_diisi: list[str] = []
    total_manual = total_mesin = total_tidak_ada = 0
    now = _waktu_sekarang()

    for fname, jawaban in lembar.items():
        dok_path = settings.extract_dir / f"{Path(fname).stem}.json"
        if not dok_path.exists():
            print(f"  [skip] dataset tidak ada: {fname}")
            continue

        with open(dok_path, "r", encoding="utf-8") as f:
            dok = json.load(f)

        if dok.get("duplikat_dari"):
            print(f"  [skip] berkas ganda (isi sama dengan {dok['duplikat_dari'][:44]})")
            continue

        mesin = dok.get("metadata", {})
        values: dict[str, str] = {}
        tidak_ada: list[str] = []
        dari_mesin: list[str] = []
        diisi_manual: list[str] = []
        sisa: list[str] = []
        perlu_diisi: list[str] = []   # '=' dipakai padahal mesin tidak punya nilai apa pun

        for fld in FIELDS:
            jwb = jawaban.get(fld)
            if jwb is None or not jwb["mentah"]:
                sisa.append(fld)
                values[fld] = ""
                continue

            if jwb["tidak_ada"]:
                values[fld] = ""
                tidak_ada.append(fld)
                continue

            if jwb["dari_mesin"]:
                nilai = mesin.get(fld, "")
                if not nilai:
                    # '=' dipakai padahal mesin tidak punya nilai apa pun -> tidak bisa
                    # dicatat sebagai "sama dengan mesin". Minta nilai sebenarnya.
                    sisa.append(fld)
                    values[fld] = ""
                    perlu_diisi.append(fld)
                    continue
                values[fld] = nilai
                dari_mesin.append(fld)
                continue

            nilai = jwb["mentah"]
            if fld == "tanggal_surat":
                nilai, berubah = rapikan_tanggal(nilai)
                if berubah:
                    semua_ubah_tanggal.append(f"{fname[:40]}: {jwb['mentah']} -> {nilai}")
            values[fld] = nilai
            if normalisasi(nilai) == normalisasi(mesin.get(fld, "")):
                dari_mesin.append(fld)
            else:
                diisi_manual.append(fld)

        beda = [
            fld for fld in FIELDS
            if values[fld] and normalisasi(values[fld]) != normalisasi(mesin.get(fld, ""))
        ]

        status = "TERVERIFIKASI" if not sisa else "BELUM_DIVERIFIKASI"
        dok["verified"] = {
            "status": status,
            "sumber": "anotasi_manual",
            "verified_by": args.anotator,
            "verified_at": now,
            "values": values,
            "berbeda_dari_mesin": beda,
            "field_tidak_ada_dikonfirmasi": tidak_ada,
            # Jejak mutu: berapa yang benar-benar diketik manusia vs yang dikonfirmasi
            # sama dengan nilai mesin. Berguna saat evaluasi (menilai sistem dengan
            # label yang sebagian berasal dari sistem harus disadari).
            "diisi_manual": diisi_manual,
            "dikonfirmasi_sama_dengan_mesin": dari_mesin,
        }

        fta = dok.get("field_tidak_ada", {})
        for fld in tidak_ada:
            fta[fld] = f"dikonfirmasi TIDAK ADA pada dokumen (anotator {args.anotator})"
        dok["field_tidak_ada"] = fta

        if not args.uji:
            with open(dok_path, "w", encoding="utf-8") as f:
                json.dump(dok, f, ensure_ascii=False, indent=2)
            ground_truth[fname] = {
                fld: (values[fld] if values[fld] else None) for fld in FIELDS
            }

        masuk += 1
        total_manual += len(diisi_manual)
        total_mesin += len(dari_mesin)
        total_tidak_ada += len(tidak_ada)
        if status == "TERVERIFIKASI":
            lengkap += 1
        else:
            belum_lengkap.append((fname, sisa))

        tanda = "OK " if status == "TERVERIFIKASI" else "setengah"
        print(f"  [{tanda}] {fname[:44]:<44} manual {len(diisi_manual)} | "
              f"konfirmasi mesin {len(dari_mesin)} | tidak ada {len(tidak_ada)}")
        for fld in perlu_diisi:
            semua_perlu_diisi.append(f"{fname[:40]} : {fld}")

    if semua_perlu_diisi:
        print()
        print(f"PERLU DIPERBAIKI - tanda '=' dipakai pada {len(semua_perlu_diisi)} sel yang "
              f"nilai mesinnya KOSONG:")
        for baris in semua_perlu_diisi[:15]:
            print(f"  - {baris}")
        print("  Isi nilai yang benar dari PDF, atau tulis '-' bila field itu memang tidak ada.")

    if semua_ubah_tanggal:
        print()
        print(f"Tanggal dirapikan otomatis ({len(semua_ubah_tanggal)}) - periksa kebenarannya:")
        for baris in semua_ubah_tanggal[:12]:
            print(f"  - {baris}")

    if not args.uji and ground_truth:
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print()
    print(f"Dokumen diproses        : {masuk}")
    print(f"Selesai (TERVERIFIKASI) : {lengkap}")
    print(f"Masih setengah          : {len(belum_lengkap)}")
    print(f"Field diketik manusia   : {total_manual}")
    print(f"Field dikonfirmasi (sama dengan mesin): {total_mesin}")
    print(f"Field dinyatakan tidak ada: {total_tidak_ada}")
    for fname, sisa in belum_lengkap[:15]:
        print(f"  - {fname[:44]:<44} belum diisi: {', '.join(sisa)}")
    if args.uji:
        print("\n(MODE UJI - tidak ada berkas yang diubah)")
    else:
        print(f"\nGround truth diperbarui: {gt_path.relative_to(settings.BASE_DIR)}")
        print("Langkah berikutnya: python scripts/eval_extraction.py --simpan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
