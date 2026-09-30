"""
Test lembar verifikasi (scripts/make_review_sheet.py & apply_review_sheet.py).

Yang dikunci di sini adalah hal-hal yang pernah menggagalkan anotasi:
  - Excel bahasa Indonesia menyimpan CSV dengan pemisah ';'
  - Excel mengubah 2024-12-17 menjadi 17/12/2024 atau "1 September 2024"
  - tanda '=' (nilai mesin sudah benar) dan '-' (field memang tidak ada)
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.apply_review_sheet import (  # noqa: E402
    TANDA_SAMA_MESIN,
    TANDA_TIDAK_ADA,
    baca_lembar,
    deteksi_pemisah,
    rapikan_tanggal,
)


def test_tanggal_gaya_excel_dikembalikan_ke_iso():
    assert rapikan_tanggal("17/12/2024") == ("2024-12-17", True)
    assert rapikan_tanggal("1 September 2024") == ("2024-09-01", True)
    assert rapikan_tanggal("17-12-2024") == ("2024-12-17", True)
    assert rapikan_tanggal("1 Des 2024") == ("2024-12-01", True)


def test_tanggal_yang_tidak_berubah_tidak_ditandai_berubah():
    assert rapikan_tanggal("2024-12-17") == ("2024-12-17", False)
    assert rapikan_tanggal("") == ("", False)
    assert rapikan_tanggal("tidak tertulis") == ("tidak tertulis", False)


def test_tanggal_tertukar_gaya_amerika_diperbaiki():
    # 09/25/2024 jelas bukan tanggal-bulan; arahnya harus ditukar
    assert rapikan_tanggal("09/25/2024") == ("2024-09-25", True)


def test_pemisah_excel_indonesia_terdeteksi():
    assert deteksi_pemisah("a;b;c;d") == ";"
    assert deteksi_pemisah("a,b,c,d") == ","
    assert deteksi_pemisah("a\tb\tc\td") == "\t"
    # hanya satu kolom: pakai bawaan
    assert deteksi_pemisah("kolom") == ","


def _tulis(tmp_path: Path, kolom: list[str], baris: list[list[str]], pemisah: str) -> Path:
    p = tmp_path / "lembar.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=pemisah)
        w.writerow(kolom)
        w.writerows(baris)
    return p


def test_lembar_bentuk_lebar_dengan_pemisah_titik_koma(tmp_path):
    kolom = ["filename", "nilai_nomor_surat", "nilai_instansi", "catatan"]
    baris = [["surat.pdf", "421.2/125/2024", "=", "catatan saya"]]
    bentuk, hasil = baca_lembar(_tulis(tmp_path, kolom, baris, ";"))

    assert bentuk == "lebar"
    jawaban = hasil["surat.pdf"]
    assert jawaban["nomor_surat"]["mentah"] == "421.2/125/2024"
    assert jawaban["instansi"]["dari_mesin"] is True
    assert jawaban["instansi"]["tidak_ada"] is False


def test_lembar_bentuk_lebar_mengenali_tanda_tidak_ada(tmp_path):
    kolom = ["filename", "nilai_verification_url"]
    baris = [["surat.pdf", "-"]]
    _, hasil = baca_lembar(_tulis(tmp_path, kolom, baris, ","))

    jawaban = hasil["surat.pdf"]["verification_url"]
    assert jawaban["tidak_ada"] is True
    assert jawaban["mentah"].lower() in TANDA_TIDAK_ADA


def test_lembar_bentuk_panjang_tetap_didukung(tmp_path):
    kolom = ["filename", "field", "nilai_benar", "jelas_tidak_ada"]
    baris = [
        ["surat.pdf", "nomor_surat", "421.2/125/2024", ""],
        ["surat.pdf", "nip_pejabat", "", "ya"],
    ]
    bentuk, hasil = baca_lembar(_tulis(tmp_path, kolom, baris, ","))

    assert bentuk == "panjang"
    assert hasil["surat.pdf"]["nomor_surat"]["mentah"] == "421.2/125/2024"
    assert hasil["surat.pdf"]["nip_pejabat"]["tidak_ada"] is True


def test_kepala_kolom_tidak_dikenali_menghasilkan_pesan_jelas(tmp_path):
    kolom = ["filename", "entah"]
    baris = [["surat.pdf", "x"]]
    try:
        baca_lembar(_tulis(tmp_path, kolom, baris, ","))
    except ValueError as e:
        assert "nilai_benar" in str(e) or "nilai_<field>" in str(e)
    else:  # pragma: no cover
        raise AssertionError("seharusnya menolak kepala kolom yang tidak dikenali")


def test_tanda_sama_dengan_mesin_dikenali():
    assert "=" in TANDA_SAMA_MESIN
