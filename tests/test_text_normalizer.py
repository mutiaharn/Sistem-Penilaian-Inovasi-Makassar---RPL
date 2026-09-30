"""
Test normalisasi teks OCR (app/pipeline/text_normalizer.py).

Contoh UJI DIAMBIL DARI HASIL OCR NYATA pada berkas
kabkota-2026-08-28-kota_makassar-c93b5421.pdf (surat pernyataan scan),
supaya test mencerminkan derau yang benar-benar terjadi, bukan karangan.
"""

from app.pipeline.text_normalizer import (
    koreksi_salah_baca,
    normalisasi_instansi,
    normalisasi_teks,
    pisah_kata_menempel,
    rapikan_nilai,
)


def test_pisah_kata_menempel_bocor_dari_ocr():
    """Nilai nyata dari OCR: 'PEMERINTAHKABUPATENGOWA'."""
    assert pisah_kata_menempel("PEMERINTAHKABUPATENGOWA") == "PEMERINTAH KABUPATEN GOWA"


def test_pisah_beberapa_istilah_dalam_satu_rentetan():
    hasil = pisah_kata_menempel("PEMERINTAHKABUPATENGOWADINASPENDIDIKAN")
    assert hasil == "PEMERINTAH KABUPATEN GOWA DINAS PENDIDIKAN"


def test_kata_yang_sudah_benar_tidak_diubah():
    teks = "DINAS PENDIDIKAN KOTA MAKASSAR"
    assert pisah_kata_menempel(teks) == teks
    assert normalisasi_teks(teks) == teks


def test_koreksi_salah_baca_huruf_r_jadi_c():
    assert koreksi_salah_baca("Dacrah") == "Daerah"
    assert koreksi_salah_baca("DACRAH") == "DAERAH"
    assert koreksi_salah_baca("Peraturan Dacrah") == "Peraturan Daerah"


def test_koreksi_tidak_merusak_kata_di_luar_daftar():
    """Konservatif: kata yang tidak dikenal dibiarkan apa adanya."""
    assert koreksi_salah_baca("Mapparessa") == "Mapparessa"
    assert koreksi_salah_baca("Bontonompo") == "Bontonompo"


def test_rapikan_nilai_buang_sisa_tanda_baca():
    """Nilai nyata dari OCR: ':Mapparessa.S.Pd'."""
    assert rapikan_nilai(":Mapparessa.S.Pd") == "Mapparessa.S.Pd"
    assert rapikan_nilai("  Kepala Sekolah  ") == "Kepala Sekolah"
    assert rapikan_nilai("Romanglasa ,") == "Romanglasa"


def test_normalisasi_instansi_membersihkan_pengulangan():
    assert normalisasi_instansi("DINAS DINAS PENDIDIKAN") == "DINAS PENDIDIKAN"
    assert normalisasi_instansi("PEMERINTAHKABUPATENGOWA DINASPENDIDIKAN") == (
        "PEMERINTAH KABUPATEN GOWA DINAS PENDIDIKAN"
    )


def test_normalisasi_teks_kosong_aman():
    for fungsi in (pisah_kata_menempel, koreksi_salah_baca, normalisasi_teks, normalisasi_instansi, rapikan_nilai):
        assert fungsi("") == ""
