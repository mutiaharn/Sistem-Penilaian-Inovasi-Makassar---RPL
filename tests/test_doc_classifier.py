"""
Test klasifikasi jenis dokumen & deteksi wilayah
(app/pipeline/doc_classifier.py).

Contoh teks diambil dari dokumen nyata di data/raw/evidence/ supaya test
mencerminkan korpus yang sebenarnya, bukan karangan.
"""

from app.pipeline.doc_classifier import (
    FIELD_SURAT,
    JENIS,
    WILAYAH_ACUAN,
    deteksi_wilayah,
    klasifikasi,
)


# --- deteksi wilayah ------------------------------------------------------------

def test_dokumen_kota_makassar():
    h = deteksi_wilayah("PEMERINTAH KOTA MAKASSAR\nDINAS PENDIDIKAN\nNomor: 421.2/47/SDN")
    assert h.kode == WILAYAH_ACUAN
    assert "MAKASSAR" in h.nama


def test_wilayah_tetap_terdeteksi_walau_spasi_ocr_hilang():
    """Kasus nyata: hasil OCR berkas c93b5421 - 'PEMERINTAHKABUPATENGOWA'."""
    h = deteksi_wilayah(
        "PEMERINTAHKABUPATENGOWA\nDINASPENDIDIKAN\nUPT SDNEGERIROMANGLASA\n"
        "Alamat:Romanglasa Desa Romanglasa Kec.Bontonompo"
    )
    assert h.kode == "luar_kota_makassar"
    assert "GOWA" in h.nama


def test_dokumen_kabupaten_gowa_terdeteksi_luar_makassar():
    """Nilai nyata dari berkas scan kabkota-...-c93b5421.pdf."""
    h = deteksi_wilayah(
        "PEMERINTAH KABUPATEN GOWA\nDINAS PENDIDIKAN\nUPT SD NEGERI ROMANGLASA\n"
        "Alamat: Romanglasa Desa Romanglasa Kec. Bontonompo"
    )
    assert h.kode == "luar_kota_makassar"
    assert "GOWA" in h.nama


def test_dokumen_morowali_terdeteksi_luar_makassar():
    h = deteksi_wilayah("PEMERINTAH KABUPATEN MOROWALI\nDINAS PENDIDIKAN DAN KEBUDAYAAN")
    assert h.kode == "luar_kota_makassar"
    assert "MOROWALI" in h.nama


def test_dokumen_mamuju_terdeteksi_luar_makassar():
    h = deteksi_wilayah("PEMERINTAH KABUPATEN MAMUJU\nBADAN PERENCANAAN PEMBANGUNAN")
    assert h.kode == "luar_kota_makassar"


def test_teks_kosong_tidak_diketahui():
    assert deteksi_wilayah("").kode == "tidak_diketahui"


def test_penyebutan_makassar_tanpa_pola_pemerintah():
    h = deteksi_wilayah("Surat permohonan replikasi inovasi dari Kotamadya Makassar")
    assert h.kode == WILAYAH_ACUAN


# --- klasifikasi jenis dokumen --------------------------------------------------

def test_keputusan_dikenali():
    k = klasifikasi("KEPUTUSAN KEPALA DINAS PENDIDIKAN\nNomor: 400.3.10/2/S.Kep\nMenimbang:")
    assert k.jenis == "keputusan"
    assert "nomor_surat" in k.field_relevan


def test_rkas_dikenali_dan_nomor_surat_tidak_relevan():
    """Inti temuan: dokumen anggaran tidak punya nomor surat/NIP."""
    k = klasifikasi("KERTAS KERJA RENCANA KEGIATAN DAN ANGGARAN SEKOLAH (RKAS)\n"
                    "Kode Rekening\nBelanja Modal")
    assert k.jenis == "anggaran"
    assert "nomor_surat" not in k.field_relevan
    assert "nip_pejabat" not in k.field_relevan
    assert "nomor_surat" in k.field_tidak_relevan


def test_manual_book_dikenali():
    k = klasifikasi("MANUAL BOOK GENTING UPT SPF SD INPRES TALLO TUA 2\nCara Penggunaan")
    assert k.jenis == "manual_book"
    assert "nip_pejabat" not in k.field_relevan


def test_peraturan_dikenali():
    k = klasifikasi("PERATURAN WALI KOTA MAKASSAR\nNOMOR 15 TAHUN 2025\nTENTANG\nRENCANA KERJA")
    assert k.jenis == "peraturan"


def test_teks_tanpa_penanda_tidak_dipaksa_menebak():
    k = klasifikasi("lorem ipsum dolor sit amet")
    assert k.jenis == "tidak_diketahui"
    assert k.field_relevan == []


def test_semua_jenis_punya_label_dan_definisi():
    for nama, info in JENIS.items():
        assert info["label"], f"{nama} tanpa label"
        for f in info["field_relevan"]:
            assert f in FIELD_SURAT, f"{nama} memuat field tak dikenal: {f}"
