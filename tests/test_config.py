"""Test konfigurasi & tata letak folder data."""

from app.core.config import settings


def test_direktori_data_sesuai_standar_repo():
    assert settings.DOCUMENTS_DIR == settings.BASE_DIR / "data" / "raw" / "evidence", (
        "berkas bukti harus berada di data/raw/evidence (diabaikan .gitignore)"
    )
    assert settings.extract_dir == settings.BASE_DIR / "data" / "datasets" / "evidence"
    assert settings.ground_truth_dir == settings.BASE_DIR / "data" / "datasets" / "ground_truth"
    assert settings.REFERENCE_DIR == settings.BASE_DIR / "data" / "reference"


def test_direktori_dibuat_saat_impor():
    for folder in (settings.STORAGE_DIR, settings.TEMP_DIR, settings.extract_dir):
        assert folder.exists(), f"{folder} seharusnya dibuat otomatis saat konfigurasi dimuat"


def test_berkas_bukti_tidak_di_dalam_root_repo():
    """Bukti PDF tidak boleh lagi berserakan di root repo."""
    root = settings.BASE_DIR
    pdf_di_root = list(root.glob("*.pdf"))
    assert not pdf_di_root, (
        f"PDF ditemukan di root repo: {[p.name for p in pdf_di_root]}. "
        "Pindahkan ke data/raw/evidence/."
    )


def test_active_indicators_mengecualikan_indikator_video():
    aktif = settings.active_indicators()
    assert len(aktif) == 19
    assert all(i["aktif_tahap_1"] for i in aktif)
    assert "IND-20" not in {i["id"] for i in aktif}


def test_env_example_tidak_memuat_kunci_asli():
    """Template .env tidak boleh berisi kunci atau kata sandi sungguhan."""
    teks = (settings.BASE_DIR / ".env.example").read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=" in teks
    for baris in teks.splitlines():
        if baris.startswith("GEMINI_API_KEY="):
            nilai = baris.split("=", 1)[1].strip()
            assert nilai == "", "GEMINI_API_KEY pada .env.example harus dikosongkan"
