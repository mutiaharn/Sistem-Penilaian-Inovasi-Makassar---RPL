"""
Evaluasi akurasi ekstraksi terhadap nilai yang sudah diverifikasi manusia.

Ini BENCHMARK YANG BENAR: memakai app/evaluation/metrics.py (exact match, field
kosong dihitung salah, dilaporkan per field). Membandingkan hasil `metadata`
(output mesin) dengan `verified.values` (nilai benar).

Sumber acuan, berurutan:
  1. blok `verified` di data/datasets/evidence/*.json
  2. cadangan: app/evaluation/ground_truth.json (untuk berkas yang belum punya verified)

Pemakaian:
    python scripts/eval_extraction.py
    python scripts/eval_extraction.py --json
    python scripts/eval_extraction.py --simpan     # tulis data/datasets/EVAL_EKSTRAKSI.md
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.evaluation.metrics import evaluasi, laporan_teks, nilai_benar, sumber_acuan
from collections import Counter

LAPORAN = settings.DATASETS_DIR / "EVAL_EKSTRAKSI.md"

# Dokumen yang dikeluarkan dari evaluasi karena bukan Kota Makassar.
# Diisi saat pemuatan; dilaporkan supaya terlihat, bukan disembunyikan.
DIKECUALIKAN: list[str] = []

# Berkas dengan isi identik (sha256 sama) - dihitung sekali saja.
DOKUMEN_GANDA: list[tuple[str, str]] = []


def muat_dokumen() -> list[dict]:
    """Gabungkan dataset dengan cadangan ground_truth.json bila verified masih kosong.

    Dokumen dari luar Kota Makassar sengaja DIKELUARKAN: ground truth proyek ini
    hanya Kota Makassar (keputusan tim), supaya angka akurasi tidak tercampur
    karakteristik daerah lain.
    """
    cadangan = {}
    gt_path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            cadangan = json.load(f)

    # Jenis dokumen + wilayah (dari report_doc_types.py)
    jenis: dict = {}
    cache = settings.DATASETS_DIR / "doc_types.json"
    if cache.exists():
        with open(cache, "r", encoding="utf-8") as f:
            jenis = json.load(f)

    dokumen = []
    for file in sorted(settings.extract_dir.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            dok = json.load(f)
        info = jenis.get(dok["filename"]) or {}
        if info.get("wilayah") == "luar_kota_makassar":
            DIKECUALIKAN.append(dok["filename"])
            continue
        if dok.get("duplikat_dari"):
            DOKUMEN_GANDA.append((dok["filename"], dok["duplikat_dari"]))
            continue
        if not nilai_benar(dok)["sumber"] and dok.get("filename") in cadangan:
            dok["_ground_truth"] = cadangan[dok["filename"]]
        if info.get("field_relevan"):
            dok["_field_relevan"] = info["field_relevan"]
        dokumen.append(dok)
    return dokumen


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluasi akurasi ekstraksi (metrik jujur)")
    parser.add_argument("--json", action="store_true", help="Keluaran JSON saja")
    parser.add_argument("--simpan", action="store_true", help="Simpan laporan markdown")
    args = parser.parse_args()

    dokumen = muat_dokumen()
    if not dokumen:
        print(f"[!] Belum ada dataset di {settings.extract_dir}")
        print("    Jalankan: python scripts/build_dataset_json.py")
        return 1

    ringkasan = evaluasi(dokumen)

    if args.json:
        print(json.dumps(
            {
                "dokumen_dievaluasi": ringkasan.jumlah_dokumen,
                "dokumen_tanpa_acuan": len(ringkasan.dokumen_terlewat),
                "titik_data": ringkasan.total_acuan,
                "akurasi": round(ringkasan.akurasi, 2),
                "akurasi_ketat": round(ringkasan.akurasi_ketat, 2),
                "per_field": {
                    f: {
                        "acuan": h.ada_acuan,
                        "tepat": h.tepat,
                        "sebagian": h.sebagian,
                        "salah": h.salah,
                        "kosong": h.kosong,
                        "akurasi": round(h.akurasi, 2),
                        "akurasi_ketat": round(h.akurasi_ketat, 2),
                    }
                    for f, h in ringkasan.per_field.items()
                    if h.ada_acuan
                },
            },
            indent=2,
            ensure_ascii=False,
        ))
        return 0

    teks = laporan_teks(ringkasan, "Akurasi Ekstraksi IDP (metrik jujur)")
    print(teks)

    # Dari mana acuan berasal - ini menentukan bagaimana angka di atas boleh dibaca.
    asal: Counter = Counter(sumber_acuan(d) for d in dokumen)
    if asal["pre_label"]:
        print("PERINGATAN METODOLOGI")
        print(f"  {asal['pre_label']} dokumen acuannya adalah PRE-LABEL mesin (nilai awal dari")
        print("  ground_truth.json lama, tanpa identitas anotator). Mengukur akurasi terhadap")
        print("  pre-label semacam ini sebagian melingkar - mesin dinilai dengan keluarannya")
        print("  sendiri - sehingga angka di atas cenderung OPTIMISTIS. Angka ini baru sah")
        print("  dilaporkan setelah anotator manusia mengisi lembar verifikasi")
        print("  (docs/LANGKAH_ANOTASI.md), yang menandai dokumen dengan identitas anotator.")
    if asal["manusia"]:
        print(f"  Acuan yang sudah diverifikasi manusia: {asal['manusia']} dokumen")
    if DOKUMEN_GANDA:
        print(f"Berkas ganda (dihitung sekali): {len(DOKUMEN_GANDA)}")
        for nama, utama in DOKUMEN_GANDA:
            print(f"  - {nama}  = salinan dari {utama}")
    if DIKECUALIKAN:
        print(f"Dikecualikan (bukan Kota Makassar): {len(DIKECUALIKAN)} berkas")
        for nama in DIKECUALIKAN:
            print(f"  - {nama}")
        print()

    if args.simpan:
        md = ["# Akurasi Ekstraksi IDP", "",
              "> Dihasilkan otomatis oleh `python scripts/eval_extraction.py --simpan`.",
              "> Metrik: exact match setelah normalisasi; field kosong dihitung SALAH.",
              ""]
        md.append(f"- Dokumen dievaluasi: **{ringkasan.jumlah_dokumen}**")
        md.append(f"- Dokumen tanpa acuan (dilewati): **{len(ringkasan.dokumen_terlewat)}**")
        md.append(f"- Titik data: **{ringkasan.total_acuan}**")
        md.append(f"- Akurasi: **{ringkasan.akurasi:.1f}%** · Akurasi ketat: **{ringkasan.akurasi_ketat:.1f}%**")
        md.append("")
        md.append("| Field | Acuan | Tepat | Sebagian | Salah | Kosong | Akurasi | Ketat |")
        md.append("|---|---|---|---|---|---|---|---|")
        for f, h in ringkasan.per_field.items():
            if not h.ada_acuan:
                continue
            md.append(
                f"| `{f}` | {h.ada_acuan} | {h.tepat} | {h.sebagian} | {h.salah} | {h.kosong} "
                f"| {h.akurasi:.1f}% | {h.akurasi_ketat:.1f}% |"
            )
        md.append(f"| **TOTAL** | **{ringkasan.total_acuan}** | | | | | **{ringkasan.akurasi:.1f}%** | **{ringkasan.akurasi_ketat:.1f}%** |")
        md.append("")
        if ringkasan.rincian_dokumen:
            md.append("## Dokumen dengan kesalahan")
            md.append("")
            md.append("| Berkas | Salah | Kosong |")
            md.append("|---|---|---|")
            for r in ringkasan.rincian_dokumen:
                md.append(f"| `{r['filename']}` | {', '.join(r['salah']) or '—'} | {', '.join(r['kosong']) or '—'} |")
            md.append("")
        if ringkasan.dokumen_terlewat:
            md.append("## Dokumen tanpa acuan (belum diverifikasi manusia)")
            md.append("")
            for nama in ringkasan.dokumen_terlewat:
                md.append(f"- `{nama}`")
            md.append("")
        LAPORAN.parent.mkdir(parents=True, exist_ok=True)
        with open(LAPORAN, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        print(f"\nLaporan disimpan: {LAPORAN.relative_to(settings.BASE_DIR)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
