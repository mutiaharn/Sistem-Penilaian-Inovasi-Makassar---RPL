"""
Test aturan pemilihan hasil OCR multi-prapemrosesan (app/pipeline/ocr.py).

Yang dikunci di sini adalah pelajaran dari pengujian nyata pada berkas scan sulit:

1. Versi pertama menggabungkan bacaan PER BARIS berdasarkan posisi. Itu membuat teks
   menyusut dari 264 menjadi 104 karakter - isi hilang tanpa jejak. Pemilihan sekarang
   dilakukan UTUH per varian.
2. Keyakinan tinggi tidak boleh menang kalau teksnya lebih sedikit. RapidOCR bisa
   melaporkan keyakinan 98% hanya untuk 5 baris sementara bacaan lain 96% untuk 11
   baris; memilih yang 98% berarti membuang enam baris teks.
3. Halaman yang sudah terbaca baik tidak perlu diulang (3-5x lebih lambat tanpa manfaat).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline.ocr import HasilOcr, OcrLokal, _varian_gambar  # noqa: E402


def _ocr_palsu(hasil_per_varian: dict[str, HasilOcr], monkeypatch) -> OcrLokal:
    """OcrLokal dengan mesin OCR dipalsukan, tanpa memuat model onnx."""
    ocr = OcrLokal(mesin="none")
    ocr.mesin_aktif = "rapidocr"
    ocr._rapid = object()          # cukup supaya siap() mengembalikan True

    # Varian palsu: (nama, gambar, skala). Gambarnya diberi penanda unik per varian
    # supaya mesin OCR palsu bisa membedakan varian mana yang sedang dibaca.
    monkeypatch.setattr(
        "app.pipeline.ocr._varian_gambar",
        lambda gambar: [(nama, f"{gambar}#{nama}", 1.0) for nama in hasil_per_varian],
    )

    def baca(gambar):
        return hasil_per_varian[str(gambar).split("#", 1)[1]]

    monkeypatch.setattr(ocr, "_pakai_rapidocr", baca)
    return ocr


def test_multi_varian_tidak_menang_dengan_membuang_teks(monkeypatch):
    """Keyakinan 99% untuk teks pendek TIDAK boleh mengalahkan 90% untuk teks panjang."""
    pendek = HasilOcr(teks="x" * 100, baris=["x"], rata_keyakinan=0.99, mesin="rapidocr")
    panjang = HasilOcr(teks="y" * 400, baris=["y"], rata_keyakinan=0.90, mesin="rapidocr")
    ocr = _ocr_palsu({"asli": panjang, "upscale_abu": pendek}, monkeypatch)

    hasil = ocr.proses_terbaik("gambar")
    assert len(hasil.teks) == 400
    assert hasil.rata_keyakinan == 0.90


def test_multi_varian_memilih_yang_paling_yakin_bila_cakupan_sebanding(monkeypatch):
    a = HasilOcr(teks="a" * 400, baris=["a"], rata_keyakinan=0.90, mesin="rapidocr")
    b = HasilOcr(teks="b" * 398, baris=["b"], rata_keyakinan=0.97, mesin="rapidocr")
    ocr = _ocr_palsu({"asli": a, "upscale_biner": b}, monkeypatch)

    hasil = ocr.proses_terbaik("gambar")
    assert hasil.teks.startswith("b")
    assert "upscale_biner" in hasil.mesin


def test_halaman_yang_sudah_baik_tidak_diulang(monkeypatch):
    """: halaman berkualitas baik harus memakai jalur cepat tanpa varian tambahan."""
    baik = HasilOcr(teks="z" * 300, baris=["1", "2", "3", "4", "5"], rata_keyakinan=0.95)
    ocr = OcrLokal(mesin="none")
    ocr.mesin_aktif = "rapidocr"
    monkeypatch.setattr(ocr, "proses", lambda g: baik)

    def jangan_dipanggil(_g):
        raise AssertionError("proses_terbaik() tidak boleh dipanggil untuk halaman yang sudah baik")

    monkeypatch.setattr(ocr, "proses_terbaik", jangan_dipanggil)
    assert ocr.proses_adaptif("gambar") is baik


def test_varian_gambar_mengembalikan_faktor_skala():
    """Varian 2x wajib melaporkan skala, kalau tidak koordinat baris salah gabung."""
    from PIL import Image

    varian = _varian_gambar(Image.new("RGB", (100, 100), "white"))
    nama = [v[0] for v in varian]
    assert nama[0] == "asli"
    assert all(len(v) == 3 for v in varian), "setiap varian harus (nama, gambar, skala)"
    assert varian[0][2] == 1.0
    assert any(skala > 1.0 for _, _, skala in varian), "varian upscale harus punya skala > 1"
