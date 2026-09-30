"""
Buat kerangka submission + ground truth dari hasil ekstraksi IDP.

Menghasilkan dua berkas:
  1. data/datasets/submissions/inovasi_<kode>.json  (kerangka, siap diisi manusia)
  2. data/datasets/ground_truth/gt_<kode>.json      (kerangka label parameter)

Keduanya mengikuti skema di data/schemas/. Kerangkanya sengaja berisi SEMUA
parameter indikator aktif dengan label kosong (""), supaya anotator tidak bisa
"lupa" mengisi parameter tertentu - kelalaian itu sendiri akan terdeteksi saat
validasi (lihat scripts/validate_dataset.py).

Pemakaian:
    python scripts/make_annotation_template.py --kode INV-2026-001 \
        --nama "GENTING - Gerakan Anti Bullying" --opd "UPT SPF SD Inpres Tallo Tua 2"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Kerangka anotasi submission + ground truth")
    parser.add_argument("--kode", required=True, help="Kode inovasi, contoh INV-2026-001")
    parser.add_argument("--nama", required=True, help="Nama inovasi")
    parser.add_argument("--opd", required=True, help="OPD pengusul")
    parser.add_argument("--tahun", type=int, default=2026)
    parser.add_argument("--annotator", default="ISI_NAMA")
    args = parser.parse_args()

    catalog = settings.load_indicator_catalog()
    aktif = [i for i in catalog["indicators"] if i.get("aktif_tahap_1")]

    submission = {
        "inovasi_id": args.kode,
        "nama_inovasi": args.nama,
        "opd": args.opd,
        "jenis": "Lainnya",
        "tahun": args.tahun,
        "status": "MENUNGGU_EVALUASI_AI",
        "deskripsi": "",
        "indikator": [
            {
                "indicator_id": ind["id"],
                "klaim_parameter_id": "",
                "evidence_ids": [],
                "naskah_naratif": "",
            }
            for ind in aktif
        ],
    }

    gt = {
        "inovasi_id": args.kode,
        "pedoman_version": catalog["version"],
        "annotations": [
            {
                "indicator_id": ind["id"],
                "parameter_id": param["id"],
                "label": "",
                "skor_diberikan": None,
                "evidence_ids": [],
                "alasan": "",
                "annotator": args.annotator,
                "annotated_at": "",
                "sumber": "anotasi_manual",
                "double_annotated_by": None,
                "label_annotator_2": None,
            }
            for ind in aktif
            for param in ind.get("parameters") or []
        ],
    }

    sub_dir = settings.DATASETS_DIR / "submissions"
    sub_dir.mkdir(parents=True, exist_ok=True)
    sub_path = sub_dir / f"inovasi_{args.kode}.json"
    gt_path = settings.ground_truth_dir / f"gt_{args.kode}.json"

    for path, payload in ((sub_path, submission), (gt_path, gt)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Submission   : {sub_path.relative_to(settings.BASE_DIR)}  ({len(aktif)} indikator)")
    print(f"Ground truth : {gt_path.relative_to(settings.BASE_DIR)}  ({len(gt['annotations'])} label parameter)")
    print("\nSelanjutnya: isi label memakai panduan docs/ANNOTATION_GUIDE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
