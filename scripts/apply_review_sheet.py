"""
Impor lembar verifikasi CSV yang sudah diisi anotator -> blok `verified` + ground truth.

Menulis ke DUA tempat sekaligus supaya tidak hilang:
  1. data/datasets/evidence/<berkas>.json  -> blok `verified` (label di dalam dataset)
  2. app/evaluation/ground_truth.json      -> acuan lama, dipakai benchmark & rebuild

Aturan kelengkapan: sebuah dokumen baru berstatus TERVERIFIKASI bila SEMUA field
punya keputusan (diisi nilainya, atau ditandai `jelas_tidak_ada=ya`). Kalau belum
lengkap, statusnya tetap BELUM_DIVERIFIKASI dan field yang belum diisi dilaporkan —
supaya "setengah diverifikasi" tidak menyamar sebagai selesai.

Pemakaian:
    python scripts/apply_review_sheet.py --masuk review_sheet.csv --anotator MAF
    python scripts/apply_review_sheet.py --masuk review_sheet.csv --anotator MAF --uji   # lihat dulu
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.evaluation.metrics import FIELDS, normalisasi

WITA = timezone(timedelta(hours=8))


def _waktu_sekarang() -> str:
    return datetime.now(WITA).isoformat(timespec="seconds")


def baca_lembar(path: Path) -> dict[str, dict[str, dict]]:
    """CSV -> {filename: {field: {nilai, tidak_ada, catatan}}}"""
    hasil: dict[str, dict[str, dict]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            fname = (row.get("filename") or "").strip()
            field = (row.get("field") or "").strip()
            if not fname or field not in FIELDS:
                continue
            hasil.setdefault(fname, {})[field] = {
                "nilai": (row.get("nilai_benar") or "").strip(),
                "tidak_ada": (row.get("jelas_tidak_ada") or "").strip().lower() in ("ya", "y", "yes", "1", "true"),
                "catatan": (row.get("catatan") or "").strip(),
            }
    return hasil


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

    lembar = baca_lembar(path)
    print(f"Lembar dibaca   : {path.name} ({len(lembar)} dokumen)")

    gt_path = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
    ground_truth = {}
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

    masuk = lengkap = 0
    belum_lengkap: list[tuple[str, list[str]]] = []
    now = _waktu_sekarang()

    for fname, jawaban in lembar.items():
        dok_path = settings.extract_dir / f"{Path(fname).stem}.json"
        if not dok_path.exists():
            print(f"  [skip] dataset tidak ada: {fname}")
            continue

        with open(dok_path, "r", encoding="utf-8") as f:
            dok = json.load(f)

        mesin = dok.get("metadata", {})
        values: dict[str, str] = {}
        tidak_ada_dikonfirmasi: list[str] = []
        sisa: list[str] = []

        for fld in FIELDS:
            jwb = jawaban.get(fld)
            if jwb is None:
                sisa.append(fld)
                values[fld] = ""
                continue
            if jwb["tidak_ada"]:
                values[fld] = ""
                tidak_ada_dikonfirmasi.append(fld)
            elif jwb["nilai"]:
                values[fld] = jwb["nilai"]
            else:
                sisa.append(fld)
                values[fld] = ""

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
            "field_tidak_ada_dikonfirmasi": tidak_ada_dikonfirmasi,
        }

        # Turunkan juga field_tidak_ada pada metadata: alasan yang sudah dipastikan
        fta = dok.get("field_tidak_ada", {})
        for fld in tidak_ada_dikonfirmasi:
            fta[fld] = f"dikonfirmasi TIDAK ADA pada dokumen (anotator {args.anotator})"
        dok["field_tidak_ada"] = fta

        if not args.uji:
            with open(dok_path, "w", encoding="utf-8") as f:
                json.dump(dok, f, ensure_ascii=False, indent=2)

            ground_truth[fname] = {
                fld: (values[fld] if values[fld] else None) for fld in FIELDS
            }

        masuk += 1
        if status == "TERVERIFIKASI":
            lengkap += 1
        else:
            belum_lengkap.append((fname, sisa))

        tanda = "OK " if status == "TERVERIFIKASI" else "setengah"
        print(f"  [{tanda}] {fname[:50]:<50} beda dari mesin: {len(beda)} field")


    if not args.uji and ground_truth:
        gt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, ensure_ascii=False, indent=2)

    print()
    print(f"Dokumen diproses        : {masuk}")
    print(f"Selesai (TERVERIFIKASI) : {lengkap}")
    print(f"Masih setengah          : {len(belum_lengkap)}")
    for fname, sisa in belum_lengkap[:15]:
        print(f"  - {fname[:48]:<48} belum diisi: {', '.join(sisa)}")
    if args.uji:
        print("\n(MODE UJI - tidak ada berkas yang diubah)")
    else:
        print(f"\nGround truth diperbarui: {gt_path.relative_to(settings.BASE_DIR)}")
        print("Langkah berikutnya: python scripts/eval_extraction.py --simpan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
