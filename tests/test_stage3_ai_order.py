"""
Test urutan pemakaian AI di Stage 3 (app/pipeline/stage3_vision_extractor.py).

Aturan yang dikunci test ini:
  1. Heuristik lokal SELALU dijalankan lebih dulu.
  2. Bila hasil lokal sudah memadai -> TIDAK ADA panggilan jaringan sama sekali.
  3. AI hanya dipertimbangkan bila field inti kosong DAN kebijakan privasi mengizinkan.
  4. Kegagalan AI tidak boleh menghilangkan hasil lokal.
  5. Kunci API tidak boleh bocor ke pesan log.

Test memakai jaring pengaman yang GAGAL bila ada panggilan jaringan yang tidak
seharusnya - jadi pelanggaran aturan langsung terlihat.
"""

import pytest
from PIL import Image

from app.core.config import settings
from app.pipeline.stage3_vision_extractor import Stage3VisionExtractor

# Kunci palsu untuk pengujian - JANGAN pernah memakai kunci sungguhan di test.
KUNCI_UJI = "AQ.KUNCI_PALSU_UNTUK_UJI_0000000000"

# Gambar kecil sungguhan (stage 7 heuristik memeriksa stempel lewat OpenCV,
# jadi tidak boleh objek kosong).
GAMBAR_UJI = Image.new("RGB", (8, 8), "white")

TEKS_LENGKAP = """PEMERINTAH KOTA MAKASSAR
DINAS PENDIDIKAN KOTA MAKASSAR
Nomor : 421.2/110/UPT.SPF.SDI.TT.2/TL/IX/2025
Perihal : Undangan Peserta Pelatihan
"""

TEKS_KURANG = "lampiran tanpa kop dan tanpa nomor"


@pytest.fixture()
def tanpa_jaringan(monkeypatch):
    """Segala upaya panggilan jaringan langsung menggagalkan test."""
    def _boom(*_a, **_k):
        raise AssertionError("Tidak boleh ada panggilan jaringan pada kasus ini")

    monkeypatch.setattr("requests.post", _boom, raising=False)
    monkeypatch.delenv("GEMINI_VISION_POLICY", raising=False)
    monkeypatch.delenv("GEMINI_AI_MODE", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", KUNCI_UJI, raising=False)


def test_hasil_lokal_memadai_tidak_menghubungi_ai(tanpa_jaringan):
    """Nomor surat + instansi sudah ada -> AI tidak perlu dipanggil."""
    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_LENGKAP, pil_image=None, meta={"is_scanned": False})
    assert hasil.nomor_surat
    assert hasil.instansi
    assert hasil.source_engine == "smart_heuristics"


def test_dokumen_digital_native_tidak_dikirim_walau_lokal_kurang(monkeypatch):
    """Lokal kurang, tapi dokumen punya lapisan teks -> tetap diproses lokal."""
    dipanggil = {"n": 0}

    def _catat(*_a, **_k):
        dipanggil["n"] += 1
        raise AssertionError("dokumen digital-native tidak boleh dikirim ke AI")

    monkeypatch.setattr("requests.post", _catat, raising=False)
    monkeypatch.delenv("GEMINI_VISION_POLICY", raising=False)

    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta={"is_scanned": False})
    assert dipanggil["n"] == 0
    assert hasil.source_engine == "smart_heuristics"


def test_mode_off_mematikan_ai_sepenuhnya(monkeypatch):
    def _catat(*_a, **_k):
        raise AssertionError("GEMINI_AI_MODE=off tidak boleh memanggil jaringan")

    monkeypatch.setattr("requests.post", _catat, raising=False)
    monkeypatch.setenv("GEMINI_AI_MODE", "off")

    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta={"is_scanned": True})
    assert hasil.source_engine == "smart_heuristics"


def test_dokumen_scan_boleh_dipertimbangkan_ai(monkeypatch):
    """Dokumen scan + lokal kurang -> AI dipanggil (dan hasilnya dipakai bila lebih lengkap)."""
    from app.pipeline.stage3_vision_extractor import ExtractedMetadata

    dipanggil = {"n": 0}

    def _palsu(self, img, ctx):  # noqa: ANN001
        dipanggil["n"] += 1
        return ExtractedMetadata(nomor_surat="999/XX/2026", instansi="DINAS UJI",
                                 source_engine="gemini_flash")

    monkeypatch.setattr(Stage3VisionExtractor, "_extract_via_gemini_vision", _palsu)
    monkeypatch.delenv("GEMINI_VISION_POLICY", raising=False)

    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta={"is_scanned": True})
    assert dipanggil["n"] == 1
    assert hasil.source_engine == "gemini_flash"
    assert hasil.nomor_surat == "999/XX/2026"


def test_kegagalan_ai_tidak_menghilangkan_hasil_lokal(monkeypatch):
    def _gagal(self, img, ctx):  # noqa: ANN001
        raise RuntimeError("jaringan mati")

    monkeypatch.setattr(Stage3VisionExtractor, "_extract_via_gemini_vision", _gagal)
    monkeypatch.delenv("GEMINI_VISION_POLICY", raising=False)

    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta={"is_scanned": True})
    assert hasil.source_engine == "smart_heuristics"  # tetap ada hasil lokal


def test_tanpa_kunci_tidak_ada_panggilan(tanpa_jaringan):
    ex = Stage3VisionExtractor("")
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta={"is_scanned": True})
    assert hasil.source_engine == "smart_heuristics"


def test_meta_tidak_diberikan_berarti_tidak_mengirim(monkeypatch):
    """Fail-safe: tanpa informasi dokumen, jangan kirim apa pun keluar."""
    def _catat(*_a, **_k):
        raise AssertionError("tanpa meta, AI tidak boleh dipanggil")

    monkeypatch.setattr("requests.post", _catat, raising=False)
    ex = Stage3VisionExtractor(KUNCI_UJI)
    hasil = ex.extract(text=TEKS_KURANG, pil_image=GAMBAR_UJI, meta=None)
    assert hasil.source_engine == "smart_heuristics"


def test_pesan_error_menyamarkan_kunci_api():
    rahasia = "AQ.CONTOH_KUNCI_PALSU_ABCDEF1234567890"
    pesan = f"404 Client Error for url: https://.../gemini:generateContent?key={rahasia}"
    aman = Stage3VisionExtractor._pesan_aman(RuntimeError(pesan))
    assert rahasia not in aman
    assert "disamarkan" in aman


def test_pesan_error_menyamarkan_pola_kunci_baru():
    rahasia = "AQ.CONTOH_KUNCI_PALSU_ABCDEF1234567890"
    aman = Stage3VisionExtractor._pesan_aman(RuntimeError(f"gagal kirim {rahasia} ke server"))
    assert rahasia not in aman


def test_model_diambil_dari_konfigurasi_bukan_hardcode():
    import inspect

    from app.pipeline import stage3_vision_extractor as mod

    sumber = inspect.getsource(mod)
    assert "gemini-2.5-flash" not in sumber, "nama model harus dari settings, bukan di-hardcode"
    assert "settings.GEMINI_MODEL" in sumber
