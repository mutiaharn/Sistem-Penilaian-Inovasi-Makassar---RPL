"""
Test katalog indikator: data/reference/indikator_2026.json.

Katalog ini adalah sumber kebenaran penilaian. Kesalahan di sini akan menular ke
seluruh sistem, jadi dikunci dengan test.
"""

import re

import pytest

from app.core.config import settings

PANJANG_AKTIF = 19
PANJANG_TOTAL = 20


@pytest.fixture(scope="module")
def catalog() -> dict:
    return settings.load_indicator_catalog()


@pytest.fixture(scope="module")
def aktif(catalog) -> list[dict]:
    return [i for i in catalog["indicators"] if i.get("aktif_tahap_1")]


def test_berkas_katalog_ada():
    assert settings.indicator_catalog_path.exists(), (
        "Katalog indikator tidak ditemukan: " f"{settings.indicator_catalog_path}"
    )


def test_jumlah_indikator(catalog):
    assert len(catalog["indicators"]) == PANJANG_TOTAL
    aktif = [i for i in catalog["indicators"] if i.get("aktif_tahap_1")]
    assert len(aktif) == PANJANG_AKTIF, "Tahap 1 menilai 19 indikator (indikator video dikecualikan)"


def test_id_indikator_unik_dan_berpola(catalog):
    ids = [i["id"] for i in catalog["indicators"]]
    assert len(ids) == len(set(ids)), "ada ID indikator duplikat"
    for i in ids:
        assert re.fullmatch(r"IND-\d{2}", i), f"ID tidak sesuai pola IND-XX: {i}"


def test_id_parameter_unik_dan_berpola(catalog):
    semua = [p["id"] for i in catalog["indicators"] for p in i.get("parameters") or []]
    assert len(semua) == len(set(semua)), "ada ID parameter duplikat"
    for p in semua:
        assert re.fullmatch(r"IND-\d{2}-P[1-3]", p), f"ID parameter tidak sesuai pola: {p}"


def test_indikator_aktif_punya_tiga_parameter(aktif):
    for ind in aktif:
        params = ind.get("parameters") or []
        assert len(params) == 3, f"{ind['id']} harus punya 3 tingkat parameter, ditemukan {len(params)}"


def test_skor_parameter_menaik(aktif):
    for ind in aktif:
        skor = [p["skor"] for p in ind["parameters"]]
        assert skor == sorted(skor), f"{ind['id']}: skor parameter harus menaik dari P1 ke P3"
        assert len(set(skor)) == len(skor), f"{ind['id']}: skor parameter tidak boleh kembar"


def test_skor_maksimum_indikator_sesuai_parameter_tertinggi(aktif):
    for ind in aktif:
        tertinggi = max(p["skor"] for p in ind["parameters"])
        assert ind["skor_maksimum"] == tertinggi, (
            f"{ind['id']}: skor_maksimum ({ind['skor_maksimum']}) != "
            f"parameter tertinggi ({tertinggi})"
        )


def test_skor_maksimum_total_sesuai_jumlah_indikator_aktif(catalog, aktif):
    total = sum(i["skor_maksimum"] for i in aktif)
    assert catalog["skor_maksimum_total"] == total, (
        f"skor_maksimum_total ({catalog['skor_maksimum_total']}) tidak sama dengan "
        f"jumlah skor indikator aktif ({total})"
    )


def test_setiap_indikator_aktif_punya_definisi_dan_bukti(aktif):
    for ind in aktif:
        assert ind.get("definisi", "").strip(), f"{ind['id']} tanpa definisi"
        assert ind.get("bukti_dukung"), f"{ind['id']} tanpa daftar bukti dukung"
        assert ind.get("nama", "").strip(), f"{ind['id']} tanpa nama"


def test_evidence_tag_unik_antar_indikator(catalog):
    """Satu tag bukti hanya boleh menunjuk satu indikator.

    Kalau tidak, usulan pemetaan otomatis di scripts/check_data.py menjadi ambigu.
    """
    pemilik: dict[str, str] = {}
    for ind in catalog["indicators"]:
        for tag in ind.get("evidence_tags") or []:
            assert tag not in pemilik, (
                f"tag '{tag}' dipakai {pemilik[tag]} dan {ind['id']} — harus unik"
            )
            pemilik[tag] = ind["id"]


def test_tag_pada_check_data_terdaftar_di_katalog(catalog):
    """Setiap tag yang bisa ditebak check_data.py harus ada pemiliknya di katalog."""
    import check_data  # dari folder scripts/

    pemilik = {tag for ind in catalog["indicators"] for tag in ind.get("evidence_tags") or []}
    dipakai = {tag for tag, _ in check_data.TAG_KEYWORDS}
    tak_terdaftar = dipakai - pemilik
    assert not tak_terdaftar, f"tag di TAG_KEYWORDS tanpa indikator pemilik: {sorted(tak_terdaftar)}"


def test_indikator_mandatori_sesuai_pedoman(catalog):
    """Yang ditandai Mandatori pada pedoman: 1, 2, 16, 17, 19."""
    mandatori = {i["id"] for i in catalog["indicators"] if i.get("mandatori")}
    assert mandatori == {"IND-01", "IND-02", "IND-16", "IND-17", "IND-19"}


def test_indikator_nonaktif_tanpa_parameter(catalog):
    nonaktif = [i for i in catalog["indicators"] if not i.get("aktif_tahap_1")]
    assert len(nonaktif) == 1
    assert nonaktif[0]["id"] == "IND-20"
    assert not nonaktif[0].get("parameters")
    assert nonaktif[0].get("alasan_tidak_aktif")
