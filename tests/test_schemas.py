"""
Test skema JSON di data/schemas/ dan konsistensinya dengan katalog indikator.
"""

import json

import pytest

from app.core.config import settings

SKEMA = [
    "idp_extraction.schema.json",
    "inovasi_submission.schema.json",
    "evidence_manifest.schema.json",
    "assessment_ground_truth.schema.json",
]


@pytest.fixture(scope="module")
def schemas() -> dict[str, dict]:
    out = {}
    for nama in SKEMA:
        path = settings.BASE_DIR / "data" / "schemas" / nama
        assert path.exists(), f"skema hilang: {nama}"
        with open(path, "r", encoding="utf-8") as f:
            out[nama] = json.load(f)
    return out


@pytest.mark.parametrize("nama", SKEMA)
def test_skema_json_valid(schemas, nama):
    schema = schemas[nama]
    assert schema["$schema"].startswith("http")
    assert schema["title"]
    assert schema["type"] == "object"
    assert schema.get("required"), f"{nama} harus mendeklarasikan field wajib"


def test_indikator_pada_skema_ground_truth_sesuai_katalog(schemas):
    """Pola ID di skema harus cocok dengan pola ID di katalog."""
    catalog = settings.load_indicator_catalog()
    aktif = [i for i in catalog["indicators"] if i.get("aktif_tahap_1")]

    pola_ind = schemas["assessment_ground_truth.schema.json"]["properties"]["annotations"][
        "items"
    ]["properties"]["indicator_id"]["pattern"]
    pola_par = schemas["assessment_ground_truth.schema.json"]["properties"]["annotations"][
        "items"
    ]["properties"]["parameter_id"]["pattern"]

    import re

    for ind in aktif:
        assert re.fullmatch(pola_ind, ind["id"]), f"{ind['id']} tidak cocok pola skema"
        for p in ind["parameters"]:
            assert re.fullmatch(pola_par, p["id"]), f"{p['id']} tidak cocok pola skema"


def test_label_ground_truth_selaras_dengan_alur_keputusan(schemas):
    """Label TERPENUHI/TIDAK_TERPENUHI/TIDAK_DAPAT_DINILAI harus konsisten.

    Label pada GT (apakah bukti mendukung klaim) sengaja berbeda dari keputusan
    reviewer (LOLOS/REVISI/TOLAK) - keduanya mengukur hal berbeda.
    """
    label = schemas["assessment_ground_truth.schema.json"]["properties"]["annotations"][
        "items"
    ]["properties"]["label"]["enum"]
    assert set(label) == {"TERPENUHI", "TIDAK_TERPENUHI", "TIDAK_DAPAT_DINILAI"}

    sumber = schemas["assessment_ground_truth.schema.json"]["properties"]["annotations"][
        "items"
    ]["properties"]["sumber"]["enum"]
    assert "anotasi_manual" in sumber, "harus bisa membedakan label manual dari label hasil AI"


def test_contoh_payload_extraction_lolos_validasi(schemas):
    """Payload contoh sesuai skema harus lolos (menjaga skema tetap bisa dipakai)."""
    jsonschema = pytest.importorskip("jsonschema")

    contoh = {
        "document_id": "",
        "filename": "contoh.pdf",
        "sha256": "a" * 64,
        "file_size_bytes": 1024,
        "page_count": 1,
        "is_scanned": False,
        "doc_type": {"jenis": "surat_dinas", "label": "Surat Dinas / Undangan / Nota Dinas", "keyakinan": 0.65},
        "wilayah": {"kode": "kota_makassar", "nama": "KOTA MAKASSAR"},
        "field_relevan": [
            "nomor_surat", "instansi", "perihal", "tanggal_surat",
            "nama_pejabat", "jabatan_pejabat", "nip_pejabat", "verification_url",
        ],
        "manifest": {"inovasi_id": "", "indicator_id": "", "evidence_tag": ""},
        "pipeline": {
            "stage1_inspector": {"words_page_1": 120, "is_scanned": False, "text_pages_read": 1},
            "stage2_preprocessing": {"target_dpi": 300, "pages_rasterized": [1], "skew_angle_deg": 0.0},
            "stage3_extraction": {"engine": "smart_heuristics", "field_confidence": {}},
            "stage4_qr": {"verification_url": "", "detector": ""},
            "stage5_validation": {
                "is_valid_nip": False,
                "confidence_score": 0.5,
                "needs_manual_review": True,
                "validation_flags": ["Missing Perihal"],
            },
        },
        "metadata": {
            "nomor_surat": "",
            "instansi": "",
            "perihal": "",
            "tanggal_surat": "",
            "nama_pejabat": "",
            "jabatan_pejabat": "",
            "nip_pejabat": "",
            "verification_url": "",
            "ada_stempel_basah": False,
            "ada_tanda_tangan": False,
        },
        "field_tidak_ada": {"nomor_surat": "tidak ditemukan pada teks dokumen - perlu verifikasi manusia"},
        "verified": {
            "status": "BELUM_DIVERIFIKASI",
            "sumber": "",
            "verified_by": "",
            "verified_at": "",
            "values": {f: "" for f in [
                "nomor_surat", "instansi", "perihal", "tanggal_surat",
                "nama_pejabat", "jabatan_pejabat", "nip_pejabat", "verification_url",
            ]},
            "berbeda_dari_mesin": [],
        },
        "text_excerpt": "",
    }

    jsonschema.Draft7Validator(schemas["idp_extraction.schema.json"]).validate(contoh)


def test_dataset_tidak_memuat_nilai_null(schemas):
    """Aturan tim: dataset tidak boleh berisi null.

    Field kosong harus berupa string kosong supaya 'kosong' tidak ambigu, dan
    alasannya wajib tercatat di field_tidak_ada.
    """
    jsonschema = pytest.importorskip("jsonschema")

    def cari_null(obj, jalur="") -> list[str]:
        temuan = []
        if obj is None:
            temuan.append(jalur or "<root>")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                temuan += cari_null(v, f"{jalur}.{k}" if jalur else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                temuan += cari_null(v, f"{jalur}[{i}]")
        return temuan

    diperiksa = 0
    for file in sorted(settings.extract_dir.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        nulls = cari_null(payload)
        assert not nulls, f"{file.name} masih memuat null di: {nulls[:5]}"

        # setiap field kosong harus punya alasan
        kosong = [f for f in payload["metadata"] if f not in ("ada_stempel_basah", "ada_tanda_tangan") and payload["metadata"][f] == ""]
        for f in kosong:
            assert f in payload["field_tidak_ada"], f"{file.name}: field '{f}' kosong tapi tanpa alasan"
        diperiksa += 1

    if diperiksa == 0:
        pytest.skip("belum ada dataset untuk diperiksa")


def test_dataset_yang_ada_sesuai_skema(schemas):
    """Semua dataset JSON yang sudah di-commit harus sah menurut skemanya."""
    jsonschema = pytest.importorskip("jsonschema")

    pasangan = [
        (settings.extract_dir, "idp_extraction.schema.json"),
        (settings.ground_truth_dir, "assessment_ground_truth.schema.json"),
    ]

    diperiksa = 0
    for folder, nama_skema in pasangan:
        if not folder.exists():
            continue
        validator = jsonschema.Draft7Validator(schemas[nama_skema])
        for file in sorted(folder.glob("*.json")):
            with open(file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            error = sorted(validator.iter_errors(payload), key=lambda e: e.path)
            assert not error, f"{file.name}: {error[0].message if error else ''}"
            diperiksa += 1

    if diperiksa == 0:
        pytest.skip("belum ada dataset untuk diperiksa")
