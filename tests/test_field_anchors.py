"""
Test penambatan field (app/pipeline/field_anchors.py).

Semua contoh di sini berasal dari kegagalan NYATA pada audit korpus, bukan karangan:
  - konsiderans peraturan  -> dulu jadi `instansi`
  - tumpukan judul         -> dulu jadi `instansi`
  - header tangkapan layar -> dulu jadi `instansi`
  - batang tubuh "Kepala ..." -> dulu jadi `jabatan_pejabat`
"""

from app.pipeline.field_anchors import (
    instansi_dari_kop,
    jabatan_dari_blok_tanda_tangan,
    wilayah_kop_surat,
)


# --- instansi -------------------------------------------------------------------

def test_instansi_dari_kop_surat_dinas():
    lines = [
        "PEMERINTAH KOTA MAKASSAR",
        "DINAS PENDIDIKAN",
        "Nomor : 421.2/125/KBH/UPT.SPF.SDI.TT2/XII/2024",
        "Perihal : Undangan Bimbingan Teknis",
    ]
    assert instansi_dari_kop(lines) == "PEMERINTAH KOTA MAKASSAR DINAS PENDIDIKAN"


def test_instansi_tidak_mengambil_judul_peraturan():
    """Kasus nyata 103081cb: dulu hasilnya 'WALi KOTA MAKASSAR PERA TU RAN W ALI KOTA...'."""
    lines = [
        "WALIKOTA MAKASSAR",
        "PERATURAN DAERAH KOTA MAKASSAR",
        "NOMOR 33 TAHUN 2025",
        "TENTANG PENYELENGGARAAN INOVASI DAERAH",
    ]
    assert instansi_dari_kop(lines) == "WALIKOTA MAKASSAR"


def test_instansi_tidak_mengambil_konsiderans():
    """Kasus nyata 98ec227: dulu hasilnya 'a. bahwa Rencana Kerja Pemerintah Daerah...'."""
    lines = [
        "a. bahwa Rencana Kerja Pemerintah Daerah Kota dalam Peraturan",
        "b. bahwa untuk melaksanakan ketentuan Pasal 5 ayat (2)",
    ]
    assert instansi_dari_kop(lines) == ""


def test_instansi_tidak_mengambil_header_tangkapan_layar():
    """Kasus nyata 18bfb801: dulu hasilnya 'SDI Tallo Tua 2 Makassar 9/27/25, 6:21 PM ...'."""
    lines = [
        "SDI Tallo Tua 2 Makassar 9/27/25, 6:21 PM Pemilihan Duta G",
        "Beranda Unduh Login Cari",
    ]
    assert instansi_dari_kop(lines) == ""


def test_instansi_tidak_mengambil_judul_dokumen_anggaran():
    """Kasus nyata ac411c1: dulu hasilnya 'KERTAS KERJA RENCANA KEGIATAN DAN ANGGARAN SEKOLAH'."""
    lines = [
        "KERTAS KERJA RENCANA KEGIATAN DAN ANGGARAN SEKOLAH (RKAS)",
        "TAHUN ANGGARAN 2025",
        "SD NEGERI MANGKURA",
    ]
    # judul RKAS ditolak; baris kop sekolah yang benar boleh dipakai
    assert instansi_dari_kop(lines) == "SD NEGERI MANGKURA"


def test_instansi_menolak_baris_alamat():
    lines = [
        "DINAS PENDIDIKAN KOTA MAKASSAR",
        "Jl. Ahmad Yani No. 2 Kota Makassar",
        "Nomor : 421/1/2025",
    ]
    assert instansi_dari_kop(lines) == "DINAS PENDIDIKAN KOTA MAKASSAR"


def test_instansi_kosong_bila_kop_tidak_ada():
    assert instansi_dari_kop(["lampiran tanpa kop", "hanya catatan biasa"]) == ""


def test_wilayah_kop_berhenti_di_baris_nomor():
    lines = ["PEMERINTAH KOTA MAKASSAR", "DINAS PENDIDIKAN", "Nomor : 1/2/2025", "Perihal : x"]
    assert wilayah_kop_surat(lines) == ["PEMERINTAH KOTA MAKASSAR", "DINAS PENDIDIKAN"]


# --- jabatan --------------------------------------------------------------------

def test_jabatan_dari_blok_tanda_tangan():
    lines = [
        "KEPUTUSAN KEPALA DINAS PENDIDIKAN",
        "Menetapkan :",
        "Kepala Sekolah",
        "Hardiyanti, S.Pd.I.",
        "NIP. 199208012020122008",
    ]
    assert jabatan_dari_blok_tanda_tangan(lines, "199208012020122008", "Hardiyanti, S.Pd.I.") == "Kepala Sekolah"


def test_jabatan_tidak_mengambil_fragmen_batang_tubuh():
    """Kasus nyata 103081c/3836d9f: 'kepala daerah dan DPRD dalam penyelenggaraan Urusan'."""
    lines = [
        "kepala daerah dan DPRD dalam penyelenggaraan Urusan",
        "Pemerintahan Daerah dan pembangunan di daerah",
        "Kepala Badan Perencanaan Pembangunan Daerah",
        "Nama Pejabat",
        "NIP. 197002161998031004",
    ]
    assert jabatan_dari_blok_tanda_tangan(lines, "197002161998031004", "Nama Pejabat") == \
        "Kepala Badan Perencanaan Pembangunan Daerah"


def test_jabatan_menolak_kalimat_definisi():
    """Kasus nyata f72169a: 'Kepala Badan Riset dan Inovasi Daerah adalah Kepala'."""
    lines = [
        "Kepala Badan Riset dan Inovasi Daerah adalah Kepala",
        "Perangkat Daerah yang melaksanakan urusan",
    ]
    assert jabatan_dari_blok_tanda_tangan(lines) == ""


def test_jabatan_dengan_dan_tetap_diterima():
    """'dan' itu bagian sah dari nama jabatan - jangan ditolak."""
    assert jabatan_dari_blok_tanda_tangan(["Kepala Badan Riset dan Inovasi Daerah"]) == \
        "Kepala Badan Riset dan Inovasi Daerah"


def test_jabatan_menyambung_baris_yang_terpotong():
    """Kasus nyata dabaa26: jabatan terbelah dua baris oleh tata letak PDF."""
    lines = [
        "Kepala Badan",
        "Perencanaan Pembangunan Daerah",
        "Nama Pejabat",
        "NIP. 197002161998031004",
    ]
    assert jabatan_dari_blok_tanda_tangan(lines, "197002161998031004") == \
        "Kepala Badan Perencanaan Pembangunan Daerah"


def test_jabatan_menolak_fragmen_tentang():
    """Kasus nyata 98ec227: dulu sempat keluar 'Wali Kota Makassar tentang Perubahan...'."""
    lines = [
        "Wali Kota Makassar tentang Perubahan atas Peraturan",
        "Nama Pejabat",
        "NIP. 198610142010012029",
    ]
    assert jabatan_dari_blok_tanda_tangan(lines, "198610142010012029") == ""


def test_instansi_menolak_label_formulir():
    """Kasus nyata ac411c1: 'Nama Sekolah' adalah label formulir RKAS, bukan instansi."""
    lines = [
        "KERTAS KERJA RENCANA KEGIATAN DAN ANGGARAN SEKOLAH (RKAS)",
        "Nama Sekolah",
        "SD NEGERI MANGKURA",
    ]
    assert instansi_dari_kop(lines) == "SD NEGERI MANGKURA"


def test_jabatan_kosong_bila_tidak_ada_yang_layak():
    assert jabatan_dari_blok_tanda_tangan(["isi dokumen biasa tanpa jabatan"]) == ""


def test_placeholder_template_tidak_pernah_jadi_nilai():
    """Kasus nyata f4a30b5/dabaa26/3cade67: dokumen masih berisi ${ttd_pengirim}."""
    assert jabatan_dari_blok_tanda_tangan(["Kepala Badan ${ttd_pengirim}", "NIP. 197002161998031004"]) == ""
    assert jabatan_dari_blok_tanda_tangan(["Kepala Badan", "${ttd}", "NIP. 197002161998031004"]) == "Kepala Badan"
    assert instansi_dari_kop(["PEMERINTAH KOTA MAKASSAR ${nomo}", "Nomor : 1/2/2025"]) == ""


def test_jabatan_menyambung_hanya_satu_kali():
    lines = ["Kepala Badan", "Perencanaan Pembangunan Daerah", "Nama Pejabat", "NIP. 197002161998031004"]
    hasil = jabatan_dari_blok_tanda_tangan(lines, "197002161998031004")
    assert hasil == "Kepala Badan Perencanaan Pembangunan Daerah"
    assert "Nama Pejabat" not in hasil


def test_jabatan_tidak_menangkap_baris_nip():
    lines = ["Kepala Sekolah", "NIP. 198706092010012033"]
    assert jabatan_dari_blok_tanda_tangan(lines, "198706092010012033") == "Kepala Sekolah"
