"""
Test metrik evaluasi (app/evaluation/metrics.py).

Metrik ini penentu seluruh klaim akurasi di laporan, jadi perilakunya dikunci test:
tidak boleh menggelembungkan angka seperti metrik lama.
"""

from app.evaluation.metrics import (
    FIELDS,
    HasilField,
    bandingkan,
    evaluasi,
    normalisasi,
)


def _dok(filename: str, mesin: dict, benar: dict) -> dict:
    return {
        "filename": filename,
        "metadata": {f: mesin.get(f, "") for f in FIELDS},
        "verified": {
            "status": "TERVERIFIKASI",
            "values": {f: benar.get(f, "") for f in FIELDS},
        },
    }


# --- normalisasi ---------------------------------------------------------------

def test_normalisasi_menyamakan_perbedaan_tanda_baca_dan_huruf_besar():
    assert normalisasi("Ernawati, S.Pd.., M.Pd.") == normalisasi("ERNAWATI S Pd M Pd")
    assert normalisasi("421.2/125/KBH/UPT.SPF.SDI.TT2/XII/2024") == normalisasi(
        "421 2 125 KBH UPT SPF SDI TT2 XII 2024"
    )
    assert normalisasi(None) == ""


# --- perbandingan per nilai ----------------------------------------------------

def test_kecocokan_penuh_disebut_tepat():
    assert bandingkan("Ernawati, S.Pd.., M.Pd.", "ERNAWATI S.Pd., M.Pd") == "tepat"


def test_substring_hanya_sebagian_bukan_tepat():
    """Ini pembeda utama dari metrik lama yang menganggap substring = benar."""
    assert bandingkan("Kepala Dinas Pendidikan", "Kepala Dinas Pendidikan Kota Makassar") == "sebagian"


def test_nilai_tidak_ada_di_dokumen_tidak_dihitung():
    assert bandingkan("apa saja", "") == "tanpa_acuan"


def test_mesin_kosong_sedangkan_nilai_benar_ada_dihitung_kosong():
    assert bandingkan("", "Kepala UPT SPF SD Inpres Tallo Tua 2") == "kosong"


def test_nilai_berbeda_disebut_salah():
    assert bandingkan("Dinas Kesehatan", "Dinas Pendidikan") == "salah"


# --- bobot & agregasi ----------------------------------------------------------

def test_bobot_tepat_satu_sebagian_setengah():
    h = HasilField(field="uji", tepat=2, sebagian=2, salah=1, kosong=1)
    assert h.ada_acuan == 6
    assert h.skor == 3.0            # 2*1 + 2*0.5
    assert h.akurasi == 50.0        # 3/6
    assert h.akurasi_ketat == 2 / 6 * 100


def test_field_tanpa_acuan_tidak_masuk_penyebut():
    h = HasilField(field="uji", tepat=1, tanpa_acuan=9)
    assert h.ada_acuan == 1
    assert h.akurasi == 100.0


def test_evaluasi_menggabungkan_dokumen_dan_menghitung_kosong_sebagai_salah():
    dokumen = [
        _dok("a.pdf", {"nomor_surat": "123/AB/2026", "instansi": ""},
             {"nomor_surat": "123/AB/2026", "instansi": "Dinas Pendidikan"}),
        _dok("b.pdf", {"nomor_surat": "999/ZZ/2026", "instansi": "Dinas Pendidikan"},
             {"nomor_surat": "123/AB/2026", "instansi": "Dinas Pendidikan"}),
    ]
    r = evaluasi(dokumen)

    assert r.jumlah_dokumen == 2
    assert r.per_field["nomor_surat"].tepat == 1
    assert r.per_field["nomor_surat"].salah == 1
    assert r.per_field["instansi"].tepat == 1
    assert r.per_field["instansi"].kosong == 1     # <- inti perbaikan metrik

    # 2 tepat + 1 salah + 1 kosong dari 4 titik data
    assert r.total_acuan == 4
    assert r.akurasi == 50.0
    assert r.akurasi_ketat == 50.0


def test_dokumen_tanpa_verified_dilewati():
    dokumen = [{"filename": "c.pdf", "metadata": {f: "x" for f in FIELDS}, "verified": {"values": {}}}]
    r = evaluasi(dokumen)
    assert r.jumlah_dokumen == 0
    assert r.dokumen_terlewat == ["c.pdf"]
    assert r.total_acuan == 0


def test_rincian_dokumen_mencatat_field_bermasalah():
    dokumen = [
        _dok("d.pdf", {"nomor_surat": "", "perihal": "Salah"},
             {"nomor_surat": "1/A/2026", "perihal": "Benar"}),
    ]
    r = evaluasi(dokumen)
    assert r.rincian_dokumen[0]["filename"] == "d.pdf"
    assert "nomor_surat" in r.rincian_dokumen[0]["kosong"]
    assert "perihal" in r.rincian_dokumen[0]["salah"]
