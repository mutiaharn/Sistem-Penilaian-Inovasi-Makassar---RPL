import os
import glob
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR

def get_all_pdfs() -> list[str]:
    files = sorted(glob.glob(str(PDF_DIR / "*.pdf")))
    # Return filenames
    return [os.path.basename(f) for f in files]

def create_or_load_split() -> dict:
    split_file = BASE_DIR / "storage" / "dataset_split.json"
    if split_file.exists():
        with open(split_file, "r", encoding="utf-8") as f:
            return json.load(f)

    all_pdfs = get_all_pdfs()
    # Deterministic seed for reproducible split
    rng = random.Random(42)
    shuffled = list(all_pdfs)
    rng.shuffle(shuffled)

    # 60% train, 40% test
    split_idx = int(len(shuffled) * 0.60)
    train_files = sorted(shuffled[:split_idx])
    test_files = sorted(shuffled[split_idx:])

    split_data = {
        "train": train_files,
        "test": test_files,
        "total": len(shuffled),
        "train_count": len(train_files),
        "test_count": len(test_files)
    }

    split_file.parent.mkdir(parents=True, exist_ok=True)
    with open(split_file, "w", encoding="utf-8") as f:
        json.dump(split_data, f, indent=2)

    return split_data

if __name__ == "__main__":
    split = create_or_load_split()
    print(f"Dataset split created: {split['train_count']} train, {split['test_count']} test.")
