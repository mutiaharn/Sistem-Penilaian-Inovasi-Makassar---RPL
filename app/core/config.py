import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    APP_NAME: str = "Sturdy IDP Engine"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Database configuration (PostgreSQL by default)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/idp_db"
    )
    # Fallback SQLite if PostgreSQL server is not yet booted
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'idp_local.db'}"
    
    # Gemini Flash AI Studio API Key (Free tier)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Kebijakan privasi pengiriman ke AI Vision: scanned_only | off | all
    # (lihat app/pipeline/vision_ai.py - dokumen digital-native tidak dikirim)
    GEMINI_VISION_POLICY: str = os.getenv("GEMINI_VISION_POLICY", "scanned_only")

    # Mesin OCR lokal: auto | rapidocr | tesseract | none
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "auto")

    # Storage & directories
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    TEMP_DIR: Path = BASE_DIR / "storage" / "temp"

    # Direktori data (dapat dioverride dari .env)
    DOCUMENTS_DIR: Path = BASE_DIR / os.getenv("DOCUMENTS_DIR", "data/raw/evidence")
    DATASETS_DIR: Path = BASE_DIR / os.getenv("DATASETS_DIR", "data/datasets")
    REFERENCE_DIR: Path = BASE_DIR / os.getenv("REFERENCE_DIR", "data/reference")
    SAMPLES_DIR: Path = BASE_DIR / "data" / "samples"

    @property
    def evidence_dir(self) -> Path:
        return self.DOCUMENTS_DIR

    @property
    def extract_dir(self) -> Path:
        return self.DATASETS_DIR / "evidence"

    @property
    def ground_truth_dir(self) -> Path:
        return self.DATASETS_DIR / "ground_truth"

    @property
    def indicator_catalog_path(self) -> Path:
        return self.REFERENCE_DIR / "indikator_2026.json"

    def load_indicator_catalog(self) -> dict:
        """Baca katalog indikator resmi (19 indikator aktif + 1 dikecualikan)."""
        import json

        with open(self.indicator_catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def active_indicators(self) -> list[dict]:
        """Indikator yang dinilai pada Tahap 1."""
        return [i for i in self.load_indicator_catalog()["indicators"] if i["aktif_tahap_1"]]

settings = Settings()

# Ensure required directories exist
for _dir in (
    settings.STORAGE_DIR,
    settings.TEMP_DIR,
    settings.DOCUMENTS_DIR,
    settings.extract_dir,
    settings.ground_truth_dir,
):
    _dir.mkdir(parents=True, exist_ok=True)

