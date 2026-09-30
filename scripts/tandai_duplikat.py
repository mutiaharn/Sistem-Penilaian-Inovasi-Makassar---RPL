"""
Deteksi berkas bukti yang ISINYA sama (bukan hanya byte-nya sama).

Kenapa perlu: korpus dari portal SIGAP memuat satu dokumen yang diunduh/discan
berulang. Deteksi lama hanya membandingkan sha256 BERKAS, sehingga lolos:
  - satu SK discan 4 kali  -> 4 berkas berbeda byte, isi identik
  - satu berkas diunduh 2x -> 2 berkas byte-identik (nama berakhiran " (1)")

Akibatnya satu dokumen dihitung berkali-kali: beban anotasi membengkak dan angka
akurasi terdistorsi (satu dokumen yang sama menyumbang beberapa kali kesalahan sama).

Dua kriteria, dijalankan dari nol setiap kali (idempoten - penanda lama diabaikan,
jadi menjalankan dua kali tidak mengubah apa pun):

  1. Nomor surat sama + teks >= 95% mirip. Dua dokumen BERBEDA tidak mungkin punya
     nomor surat yang sama; kriteria ini menangkap scan ulang yang hasil OCR-nya
     berbeda satu-dua karakter sehingga sidik jarinya tidak persis sama.
  2. Isi identik setelah normalisasi (sha256 teks) - untuk dokumen tanpa nomor surat
     (mis. bukti media, tangkapan layar).

Berkas utama sebuah kelompok = nama terpendek tanpa akhiran ganda " (1)".
Berkas lain ditandai `duplikat_dari` = nama berkas utama.

Pemakaian:
    python scripts/tandai_duplikat.py              # tandai, tulis ke dataset
    python scripts/tandai_duplikat.py --periksa    # lihat saja, jangan tulis
"""

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

AMBANG_MIRIP = 0.95


def normalisasi(teks: str) -> str:
    teks = (teks or "").lower()
    teks = re.sub(r"[^a-z0-9 ]+", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def teks_isi(dok: dict, documents_dir: Path) -> tuple[str, str]:
    """Teks dokumen + sumbernya ('lapisan_pdf' atau 'cuplikan_ocr')."""
    pdf = documents_dir / dok.get("filename", "")
    if pdf.exists():
        try:
            import pypdf

            pembaca = pypdf.PdfReader(str(pdf))
            teks = normalisasi(" ".join((p.extract_text() or "") for p in pembaca.pages))
            if len(teks) >= 200:
                return teks, "lapisan_pdf"
        except Exception:  # noqa: BLE001 - berkas rusak bukan urusan skrip ini
            pass
    return normalisasi(dok.get("text_excerpt") or ""), "cuplikan_ocr"


def tandai(extract_dir: Path, documents_dir: Path, tulis: bool = True) -> list[tuple[str, str, str]]:
    """Tandai duplikat isi. Mengembalikan [(berkas_utama, salinan, alasan)]."""
    dokumen: dict[str, dict] = {}
    jalur: dict[str, Path] = {}
    teks: dict[str, str] = {}
    sumber: dict[str, str] = {}

    for path in sorted(extract_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            dok = json.load(f)
        nama = dok["filename"]
        dok.pop("duplikat_dari", None)      # hitung dari nol, jangan warisi penanda lama
        t, s = teks_isi(dok, documents_dir)
        dok["text_sha256"] = hashlib.sha256(t.encode("utf-8")).hexdigest() if len(t) >= 50 else ""
        dokumen[nama], jalur[nama], teks[nama], sumber[nama] = dok, path, t, s

    penunjuk: dict[str, str] = {}
    alasan: dict[str, str] = {}

    def tunjuk_ke(utama: str, salinan: str, sebab: str) -> None:
        penunjuk[salinan] = utama
        alasan[salinan] = sebab

    # --- Kriteria 1: nomor surat sama + teks hampir identik -------------------
    per_nomor: dict[str, list[str]] = {}
    for nama, dok in dokumen.items():
        nomor = normalisasi(dok.get("metadata", {}).get("nomor_surat", ""))
        if len(nomor) >= 6 and len(teks[nama]) >= 200:
            per_nomor.setdefault(nomor, []).append(nama)

    for _, anggota in per_nomor.items():
        if len(anggota) < 2:
            continue
        anggota.sort(key=lambda n: ("(" in n, len(n), n))
        utama = anggota[0]
        for nama in anggota[1:]:
            mirip = difflib.SequenceMatcher(None, teks[utama], teks[nama]).ratio()
            if mirip >= AMBANG_MIRIP:
                tunjuk_ke(utama, nama, f"nomor surat sama, teks {mirip * 100:.1f}% mirip")

    # --- Kriteria 2: isi identik (sha256 teks) --------------------------------
    per_isi: dict[str, list[str]] = {}
    for nama, dok in dokumen.items():
        if nama in penunjuk or not dok["text_sha256"]:
            continue
        per_isi.setdefault(dok["text_sha256"], []).append(nama)

    for _, anggota in per_isi.items():
        if len(anggota) < 2:
            continue
        anggota.sort(key=lambda n: ("(" in n, len(n), n))
        utama = anggota[0]
        for nama in anggota[1:]:
            tunjuk_ke(utama, nama, f"isi identik ({sumber[nama]}, {len(teks[nama])} karakter)")

    # --- Rantai diratakan: semua penunjuk mengarah ke berkas akar -------------
    def akar(nama: str) -> str:
        dilihat: set[str] = set()
        while nama in penunjuk and nama not in dilihat:
            dilihat.add(nama)
            nama = penunjuk[nama]
        return nama

    rapi = {salinan: akar(salinan) for salinan in penunjuk}

    if tulis:
        for nama, dok in dokumen.items():
            baru = rapi.get(nama, "")
            if (dok.get("duplikat_dari") or "") != baru:
                if baru:
                    dok["duplikat_dari"] = baru
                else:
                    dok.pop("duplikat_dari", None)
            with open(jalur[nama], "w", encoding="utf-8") as f:
                json.dump(dok, f, ensure_ascii=False, indent=2)

    return [(rapi[salinan], salinan, alasan[salinan]) for salinan in sorted(rapi)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Tandai dokumen dengan isi identik")
    parser.add_argument("--periksa", action="store_true", help="Tampilkan saja, jangan tulis")
    args = parser.parse_args()

    berkas = sorted(settings.extract_dir.glob("*.json"))
    hasil = tandai(settings.extract_dir, settings.DOCUMENTS_DIR, tulis=not args.periksa)

    print(f"Berkas diperiksa      : {len(berkas)}")
    print(f"Dokumen unik          : {len(berkas) - len(hasil)}")
    print(f"Berkas salinan        : {len(hasil)}")
    print()
    for utama, salinan, sebab in hasil:
        print(f"  {salinan}")
        print(f"     -> salinan dari {utama}  ({sebab})")
    print()
    print(f"Korpus yang benar-benar unik: {len(berkas) - len(hasil)} dokumen")
    if args.periksa:
        print("(MODE PERIKSA - tidak ada berkas yang diubah)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
