"""
Test penjaga privasi AI Vision (app/pipeline/vision_ai.py).

Ini bagian paling sensitif: dokumen dinas BRIDA tidak boleh keluar dari perangkat
tanpa dasar yang jelas. Perilaku `boleh_kirim()` dikunci test supaya perubahan
kode di kemudian hari tidak diam-diam mengirim data digital-native ke API.
"""

import json

import pytest

from app.core.config import settings
from app.pipeline import vision_ai


@pytest.fixture(autouse=True)
def _bersihkan_lingkungan(monkeypatch, tmp_path):
    """Setiap test memakai kunci API palsu & file audit terpisah."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "kunci-uji", raising=False)
    monkeypatch.setattr(vision_ai, "AUDIT_FILE", tmp_path / "audit.jsonl")
    monkeypatch.delenv("GEMINI_VISION_POLICY", raising=False)
    yield


def test_dokumen_digital_native_tidak_boleh_dikirim():
    """Ini aturan utama yang diminta tim: PDF yang teksnya terbaca tetap di lokal."""
    boleh, alasan = vision_ai.boleh_kirim({"is_scanned": False, "page_count": 4})
    assert boleh is False
    assert "digital-native" in alasan


def test_dokumen_scan_boleh_dikirim():
    boleh, alasan = vision_ai.boleh_kirim({"is_scanned": True, "page_count": 20})
    assert boleh is True
    assert "scan" in alasan


def test_kebijakan_off_menolak_semua(monkeypatch):
    monkeypatch.setenv("GEMINI_VISION_POLICY", "off")
    for meta in ({"is_scanned": True}, {"is_scanned": False}):
        boleh, alasan = vision_ai.boleh_kirim(meta)
        assert boleh is False
        assert "off" in alasan


def test_kebijakan_all_hanya_bila_diminta_eksplisit(monkeypatch):
    monkeypatch.setenv("GEMINI_VISION_POLICY", "all")
    boleh, alasan = vision_ai.boleh_kirim({"is_scanned": False})
    assert boleh is True
    assert "persetujuan eksplisit" in alasan


def test_tanpa_kunci_api_tidak_pernah_mengirim(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "", raising=False)
    boleh, alasan = vision_ai.boleh_kirim({"is_scanned": True})
    assert boleh is False
    assert "GEMINI_API_KEY" in alasan


def test_penolakan_dicatat_ke_audit_tanpa_panggilan_jaringan(monkeypatch):
    """Dokumen digital-native: harus ditolak DAN tercatat, tanpa menyentuh jaringan."""
    def _jangan_panggil(*_a, **_k):  # pragma: no cover - hanya jaring pengaman
        raise AssertionError("Tidak boleh ada panggilan jaringan untuk dokumen digital-native")

    monkeypatch.setattr("requests.post", _jangan_panggil, raising=False)

    hasil = vision_ai.ekstrak_dengan_vision(
        nama_berkas="kabkota-uji.pdf",
        sha256="a" * 64,
        meta={"is_scanned": False, "page_count": 3},
        gambar_halaman=[],
        prompt="uji",
    )
    assert hasil["ditolak"] is True
    assert hasil["hasil"] is None

    entri = [json.loads(x) for x in vision_ai.AUDIT_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert entri[-1]["aksi"] == "TOLAK_KIRIM"
    assert entri[-1]["berkas"] == "kabkota-uji.pdf"


def test_ringkasan_audit_menghitung_kirim_dan_tolak():
    vision_ai._catat_audit({"aksi": "KIRIM", "berkas": "a.pdf"})
    vision_ai._catat_audit({"aksi": "KIRIM", "berkas": "a.pdf"})
    vision_ai._catat_audit({"aksi": "TOLAK_KIRIM", "berkas": "b.pdf"})
    vision_ai._catat_audit({"aksi": "GAGAL", "berkas": "c.pdf"})

    r = vision_ai.ringkasan_audit()
    assert r["kirim"] == 2
    assert r["tolak"] == 1
    assert r["gagal"] == 1
    assert r["berkas_dikirim"] == ["a.pdf"]


def test_batas_halaman_per_pengiriman_wajar():
    """Tidak boleh mengirim dokumen 22 halaman sekaligus."""
    assert 1 <= vision_ai.MAKS_HALAMAN_PER_KIRIM <= 8
