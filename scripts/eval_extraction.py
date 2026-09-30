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
from app.evaluation.metrics import evaluasi, laporan_teks, nilai_benar

LAPORAN = settings.DATASETS_DIR / "EVAL_EKSTRAKSI.md"


def muat_dokumen() -> list[dict]:
    """Gabungkan dataset dengan cadangan ground_truth.json bila verified masih kosong."""
    cadangan = {}
    gt_path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            cadangan = json.load(f)

    # Jenis dokumen (dari report_doc_types.py) -> field yang relevan saja yang dinilai
    jenis: dict = {}
    cache = settings.DATASETS_DIR / "doc_types.json"
    if cache.exists():
        with open(cache, "r", encoding="utf-8") as f:
            jenis = json.load(f)

    dokumen = []
    for file in sorted(settings.extract_dir.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            dok = json.load(f)
        if not nilai_benar(dok)["sumber"] and dok.get("filename") in cadangan:
            dok["_ground_truth"] = cadangan[dok["filename"]]
        info = jenis.get(dok["filename"])
        if info and info.get("field_relevan"):
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
