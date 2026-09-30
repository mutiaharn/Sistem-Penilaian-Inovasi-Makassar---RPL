"""Konfigurasi bersama untuk seluruh test."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Pastikan `app` dan `scripts` bisa diimpor walau pytest dijalankan dari lokasi lain
for path in (BASE_DIR, BASE_DIR / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
