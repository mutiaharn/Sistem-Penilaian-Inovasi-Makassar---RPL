"""
Validasi dataset terhadap JSON Schema + cek kelengkapan anotasi.

Jalankan SEBELUM commit dataset atau sebelum memakai data untuk evaluasi model.
Gagal di sini jauh lebih murah daripada gagal di sidang.

Pemakaian:
    python scripts/validate_dataset.py            # validasi semua
    python scripts/validate_dataset.py --strict   # label kosong dianggap error
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

SCHEMA_DIR = settings.BASE_DIR / "data" / "schemas"

# Pemetaan folder/target -> file skema
TARGETS = [
    ("datasets/evidence", "idp_extraction.schema.json"),
    ("datasets/submissions", "inovasi_submission.schema.json"),
    ("datasets/ground_truth", "assessment_ground_truth.schema.json"),
    ("reference/evidence_manifest.json", "evidence_manifest.schema.json"),
]


def load_validator(schema_name: str):
    """Pakai jsonschema bila terpasang; jika tidak, lakukan validasi struktur dasar."""
    schema_path = SCHEMA_DIR / schema_name
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    try:
        import jsonschema  # type: ignore

        return jsonschema.Draft7Validator(schema), True
    except ImportError:
        return schema, False


def basic_required_check(schema: dict, payload: dict) -> list[str]:
    errors = []
    for key in schema.get("required", []):
        if key not in payload or payload[key] in ("", None, []):
            errors.append(f"field wajib kosong/hilang: {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validasi dataset SIP-BRIDA")
    parser.add_argument("--strict", action="store_true", help="Label anotasi kosong = error")
    args = parser.parse_args()

    total_files = 0
    total_errors = 0

    for target, schema_name in TARGETS:
        path = settings.BASE_DIR / "data" / target
        validator, has_jsonschema = load_validator(schema_name)

        if path.is_dir():
            files = sorted(path.glob("*.json"))
        elif path.exists():
            files = [path]
        else:
            print(f"[skip] {target} (belum ada)")
            continue

        print(f"\n=== {target} ({len(files)} berkas, skema {schema_name}) ===")
        if not files:
            print("  [i] folder kosong")
            continue

        for file in files:
            total_files += 1
            errors: list[str] = []
            try:
                with open(file, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except json.JSONDecodeError as exc:
                print(f"  [X] {file.name}: JSON tidak valid -> {exc}")
                total_errors += 1
                continue

            if has_jsonschema:
                errors += [f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
                           for e in validator.iter_errors(payload)]
            else:
                # validator berisi dict skema saat jsonschema tidak terpasang
                errors += basic_required_check(validator, payload)

            if args.strict and "ground_truth" in target:
                for ann in payload.get("annotations", []):
                    if not ann.get("label"):
                        errors.append(f"label kosong: {ann.get('parameter_id')}")

            if errors:
                total_errors += len(errors)
                print(f"  [X] {file.name}: {len(errors)} masalah")
                for err in errors[:5]:
                    print(f"        - {err}")
                if len(errors) > 5:
                    print(f"        ... dan {len(errors) - 5} lagi")
            else:
                print(f"  [OK] {file.name}")

    print("\n" + "=" * 60)
    print(f"Berkas diperiksa: {total_files} | masalah: {total_errors}")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
