"""
Audit nilai ekstraksi terhadap ISI dokumen (tidak butuh anotasi manusia).

Kenapa alat ini ada: akurasi ekstraksi hanya bisa dihitung pada dokumen yang sudah
dianotasi (6 dari 28). Untuk 22 dokumen sisanya tidak ada acuan, jadi tidak ada angka
akurasi. Namun masih ada pertanyaan yang BISA dijawab tanpa label:

    "Nilai yang dikeluarkan mesin itu benar-benar ada di dokumennya, atau dikarang?"

Alat ini mencari setiap nilai pada teks dokumen:
  ADA             - ditemukan persis (setelah normalisasi) di dalam teks dokumen
  MIRIP           - hanya sebagian besar cocok (mis. beda tanda baca / satu kata salah)
  TIDAK DITEMUKAN - tidak ada di dokumen

Batasannya harus dipahami:
  - ADA bukan berarti BENAR. Nilai bisa muncul di dokumen tetapi bukan sebagai nilai
    field itu (mis. nomor surat lain yang dikutip di badan surat).
  - TIDAK DITEMUKAN adalah sinyal kuat nilai itu salah/karangan - inilah gunanya.
  - Untuk dokumen scan, teks yang dibandingkan adalah hasil OCR. Nilai yang "tidak
    ditemukan" bisa jadi hanya salah baca OCR, bukan salah mesin pengekstrak.

Pemakaian:
    python scripts/audit_nilai_ekstraksi.py                 # semua dokumen
    python scripts/audit_nilai_ekstraksi.py --hanya-uji     # hanya yang belum dianotasi
    python scripts/audit_nilai_ekstraksi.py --rinci         # tampilkan tiap sel
"""

import argparse
import difflib
import json
import re
import sys
from collections import Counter, defaultdict
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

BULAN = {
    1: "januari", 2: "februari", 3: "maret", 4: "april", 5: "mei", 6: "juni",
    7: "juli", 8: "agustus", 9: "september", 10: "oktober", 11: "november", 12: "desember",
}


def normalisasi(teks: str) -> str:
    teks = (teks or "").lower()
    teks = teks.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    teks = re.sub(r"[^a-z0-9/]+", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def angka_saja(teks: str) -> str:
    return re.sub(r"\D", "", teks or "")


def varian_tanggal(iso: str) -> list[str]:
    """Bentuk-bentuk tanggal yang mungkin tertulis di dokumen."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return []
    y, bl, tg = int(m.group(1)), int(m.group(2)), int(m.group(3))
    nama = BULAN.get(bl, "")
    keluar = [
        f"{tg} {nama} {y}", f"{tg:02d} {nama} {y}", f"{nama} {tg} {y}",
        f"{tg}-{bl:02d}-{y}", f"{tg:02d}-{bl:02d}-{y}",
        f"{tg}/{bl:02d}/{y}", f"{tg:02d}/{bl:02d}/{y}",
    ]
    return [normalisasi(v) for v in keluar if nama]


def cari(nilai: str, teks_norm: str) -> str:
    """ADA / MIRIP / TIDAK DITEMUKAN."""
    n = normalisasi(nilai)
    if not n:
        return "KOSONG"
    if n in teks_norm:
        return "ADA"

    # Coba tanpa spasi (teks OCR sering kehilangan spasi)
    if n.replace(" ", "") in teks_norm.replace(" ", ""):
        return "ADA"

    sm = difflib.SequenceMatcher(None, teks_norm, n)
    blok = sm.find_longest_match(0, len(teks_norm), 0, len(n))
    if blok.size / max(len(n), 1) >= 0.85:
        return "MIRIP"
    return "TIDAK DITEMUKAN"


def periksa_nilai(field: str, nilai: str, teks_norm: str) -> str:
    if field == "tanggal_surat":
        for v in varian_tanggal(nilai):
            if v in teks_norm:
                return "ADA"
        # tanggal gaya lain: cari hari dan tahunnya berdekatan
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", nilai or "")
        if m:
            tg, y = str(int(m.group(3))), m.group(1)
            if re.search(rf"\b{tg}\b.{{0,20}}{y}", teks_norm):
                return "MIRIP"
        return "TIDAK DITEMUKAN"

    if field == "nip_pejabat":
        d = angka_saja(nilai)
        if d and d in angka_saja(teks_norm):
            return "ADA"
        if len(d) >= 12 and d[:8] in angka_saja(teks_norm):
            return "MIRIP"
        return "TIDAK DITEMUKAN"

    if field == "nomor_surat":
        # nomor surat sering dipecah baris; bandingkan deretan angka+slash saja
        inti = re.sub(r"[^0-9/]", "", nilai or "")
        if len(inti) >= 5 and inti in re.sub(r"[^0-9/]", "", teks_norm):
            return "ADA"
        return cari(nilai, teks_norm)

    return cari(nilai, teks_norm)


def teks_dokumen(dok: dict, documents_dir: Path) -> tuple[str, str]:
    """Seluruh teks dokumen + sumbernya.

    PENTING: jangan memakai `text_excerpt` saja. Cuplikan itu hanya 1500 karakter
    pertama, sehingga NIP/jabatan di blok tanda tangan (halaman akhir) selalu
    dianggap "tidak ditemukan" - angka audit jadi terlalu pesimis.
    """
    pdf = documents_dir / dok.get("filename", "")
    if pdf.exists():
        try:
            import pypdf

            teks = " ".join((p.extract_text() or "") for p in pypdf.PdfReader(str(pdf)).pages)
            if len(normalisasi(teks)) >= 200:
                return teks, "lapisan_pdf"
        except Exception:  # noqa: BLE001
            pass
    return dok.get("text_excerpt") or "", "cuplikan_ocr"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit nilai ekstraksi vs isi dokumen")
    parser.add_argument("--hanya-uji", action="store_true",
                        help="Hanya dokumen yang belum dianotasi (kandidat set uji)")
    parser.add_argument("--rinci", action="store_true", help="Tampilkan setiap sel yang bermasalah")
    args = parser.parse_args()

    gt = {}
    gt_path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            gt = json.load(f)

    hitung: dict[str, Counter] = defaultdict(Counter)
    hitung_sumber: Counter = Counter()
    contoh_buruk: dict[str, list[str]] = defaultdict(list)
    jumlah_dok = 0

    for path in sorted(settings.extract_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            dok = json.load(f)
        if dok.get("duplikat_dari"):
            continue
        if args.hanya_uji and dok["filename"] in gt:
            continue

        teks, sumber_teks = teks_dokumen(dok, settings.DOCUMENTS_DIR)
        if not teks.strip():
            continue
        teks_norm = normalisasi(teks)
        jumlah_dok += 1
        hitung_sumber[sumber_teks] += 1

        for field in FIELDS:
            nilai = dok.get("metadata", {}).get(field, "")
            if not nilai:
                hitung[field]["KOSONG"] += 1
                continue
            if field not in (dok.get("field_relevan") or []) and dok.get("field_relevan"):
                hitung[field]["DI LUAR RELEVAN"] += 1
            hasil = periksa_nilai(field, nilai, teks_norm)
            hitung[field][hasil] += 1
            if hasil == "TIDAK DITEMUKAN":
                contoh_buruk[field].append(
                    f"{dok['filename'][-12:-5]} [{sumber_teks}] {nilai[:58]}"
                )

    if not jumlah_dok:
        print("[!] Tidak ada dokumen dengan teks untuk diperiksa.")
        return 1

    print("=" * 92)
    print("AUDIT NILAI EKSTRAKSI TERHADAP ISI DOKUMEN")
    print(f"{'Dokumen diperiksa':<24}: {jumlah_dok}"
          f"{' (hanya yang belum dianotasi)' if args.hanya_uji else ''}")
    print(f"{'Sumber teks':<24}: " + ", ".join(f"{k}={v}" for k, v in hitung_sumber.items()))
    print("=" * 92)
    print(f"{'field':<18}{'ADA':>6}{'MIRIP':>7}{'TIDAK':>7}{'kosong':>8}{'luar relevan':>14}")
    print("-" * 92)

    total = Counter()
    for field in FIELDS:
        c = hitung[field]
        total.update(c)
        print(f"{field:<18}{c['ADA']:>6}{c['MIRIP']:>7}{c['TIDAK DITEMUKAN']:>7}"
              f"{c['KOSONG']:>8}{c['DI LUAR RELEVAN']:>14}")
    print("-" * 92)
    ada = total["ADA"]
    mirip = total["MIRIP"]
    tidak = total["TIDAK DITEMUKAN"]
    berisi = ada + mirip + tidak
    print(f"{'TOTAL':<18}{ada:>6}{mirip:>7}{tidak:>7}")
    if berisi:
        print()
        print(f"  Nilai yang keluar dari mesin : {berisi}")
        print(f"  Terbukti ada di dokumen      : {ada} ({ada / berisi * 100:.1f}%)")
        print(f"  Mirip (beda tanda baca/kata) : {mirip} ({mirip / berisi * 100:.1f}%)")
        print(f"  TIDAK ditemukan di dokumen   : {tidak} ({tidak / berisi * 100:.1f}%)  <-- sinyal salah")

    if args.rinci and contoh_buruk:
        print()
        print("Nilai yang tidak ditemukan di dokumen:")
        for field, daftar in contoh_buruk.items():
            print(f"  {field}:")
            for baris in daftar[:6]:
                print(f"    - {baris}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
