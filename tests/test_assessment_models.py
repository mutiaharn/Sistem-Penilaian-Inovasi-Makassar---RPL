"""
Test domain penilaian (app/database/assessment_models.py).

Yang diuji bukan sekadar "tabel bisa dibuat", melainkan INVARIAN yang menjadi
alasan desainnya: draf AI dan keputusan manusia terpisah, dan override bisa
dibuktikan.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.assessment_models import (
    AuditLog,
    Evidence,
    HumanDecision,
    Innovation,
    InnovationIndicator,
    ParameterAssessment,
    ReferenceIndicator,
    ReferenceParameter,
    User,
)
from app.database.connection import Base

# Model dokumen juga diimpor supaya foreign key ke tabel documents terdaftar
from app.database import models as document_models  # noqa: F401


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _siapkan_indikator(db) -> None:
    db.add(
        ReferenceIndicator(
            id="IND-01",
            kode="regulasi_inovasi",
            nama="Regulasi Inovasi Daerah",
            mandatori=True,
            aktif_tahap_1=True,
            urutan=1,
            skor_maksimum=9.0,
            evidence_tags=["regulasi"],
            bukti_dukung=["Naskah regulasi"],
        )
    )
    for i, skor in enumerate((3.0, 6.0, 9.0), start=1):
        db.add(
            ReferenceParameter(
                id=f"IND-01-P{i}",
                indicator_id="IND-01",
                nama=f"Tingkat {i}",
                skor=skor,
                urutan=i,
            )
        )
    db.flush()


def test_tabel_terbentuk(db):
    from sqlalchemy import inspect

    nama_tabel = set(inspect(db.get_bind()).get_table_names())
    for tabel in (
        "users",
        "reference_indicators",
        "reference_parameters",
        "innovations",
        "innovation_indicators",
        "evidences",
        "parameter_assessments",
        "human_decisions",
        "audit_logs",
    ):
        assert tabel in nama_tabel, f"tabel {tabel} tidak terbentuk"


def test_draf_ai_dan_keputusan_manusia_terpisah_dan_dapat_dibandingkan(db):
    """Skenario inti: AI merekomendasikan LOLOS, manusia mengubahnya menjadi TOLAK."""
    _siapkan_indikator(db)

    inovasi = Innovation(kode="INV-2026-001", nama_inovasi="GENTING", opd="UPT SDI Tallo Tua 2")
    db.add(inovasi)
    db.flush()

    indikator = InnovationIndicator(
        innovation_id=inovasi.id,
        indicator_id="IND-01",
        klaim_parameter_id="IND-01-P2",
        status="MENUNGGU_EVALUASI_AI",
    )
    db.add(indikator)
    db.flush()

    db.add(
        ParameterAssessment(
            innovation_indicator_id=indikator.id,
            parameter_id="IND-01-P2",
            rekomendasi="LOLOS",
            confidence_score=0.87,
            ai_catatan="Nomor 400.3.10/2/S.Kep/Disdik/VIII/2026 terbaca lengkap.",
            evidence_ids=["EVD-0001"],
            engine="rule_based",
        )
    )

    db.add(
        HumanDecision(
            innovation_indicator_id=indikator.id,
            parameter_id="IND-01-P2",
            keputusan="TOLAK",
            catatan="Yang dilampirkan hanya SK OPD, bukan Keputusan Kepala Daerah.",
            ai_rekomendasi_snapshot="LOLOS",
            ai_confidence_snapshot=0.87,
            is_override=True,
            decided_by_nama="Verifikator BRIDA",
        )
    )
    db.commit()

    draf = db.query(ParameterAssessment).one()
    keputusan = db.query(HumanDecision).one()

    # Draf AI tetap utuh walau manusia menolak -> override bisa diaudit
    assert draf.rekomendasi == "LOLOS"
    assert keputusan.keputusan == "TOLAK"
    assert keputusan.is_override is True
    assert keputusan.ai_rekomendasi_snapshot == "LOLOS"


def test_indikator_tidak_boleh_duplikat_dalam_satu_usulan(db):
    from sqlalchemy.exc import IntegrityError

    _siapkan_indikator(db)
    inovasi = Innovation(kode="INV-2026-002", nama_inovasi="Uji", opd="OPD Uji")
    db.add(inovasi)
    db.flush()

    db.add(InnovationIndicator(innovation_id=inovasi.id, indicator_id="IND-01"))
    db.add(InnovationIndicator(innovation_id=inovasi.id, indicator_id="IND-01"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_bukti_terikat_ke_indikator_dan_dokumen(db):
    _siapkan_indikator(db)
    inovasi = Innovation(kode="INV-2026-003", nama_inovasi="Uji Bukti", opd="OPD Uji")
    db.add(inovasi)
    db.flush()

    dokumen = document_models.Document(
        original_filename="kabkota-2026-08-28-kota_makassar-3cade67d.pdf",
        file_path="data/raw/evidence/kabkota-2026-08-28-kota_makassar-3cade67d.pdf",
        file_hash="f" * 64,
    )
    db.add(dokumen)
    db.flush()

    db.add(
        Evidence(
            evidence_id="EVD-0001",
            innovation_id=inovasi.id,
            document_id=dokumen.id,
            indicator_id="IND-01",
            evidence_tag="regulasi",
            filename=dokumen.original_filename,
            sha256=dokumen.file_hash,
        )
    )
    db.commit()

    bukti = db.query(Evidence).one()
    assert bukti.indicator_id == "IND-01"
    assert bukti.innovation.kode == "INV-2026-003"
    assert bukti.document_id == dokumen.id


def test_audit_log_menyimpan_payload_perubahan(db):
    db.add(
        AuditLog(
            actor="verifikator@brida.makassarkota.go.id",
            actor_role="verifikator",
            action="DECIDE",
            entity="human_decision",
            entity_id="17",
            payload={"parameter_id": "IND-01-P2", "dari_ai": "LOLOS", "menjadi": "TOLAK"},
        )
    )
    db.commit()

    log = db.query(AuditLog).one()
    assert log.payload["menjadi"] == "TOLAK"


def test_pengguna_menyimpan_peran(db):
    db.add(
        User(
            nama="Verifikator BRIDA",
            email="verifikator@brida.makassarkota.go.id",
            password_hash="$2b$12$hashbcrypt",
            role="verifikator",
        )
    )
    db.add(
        User(
            nama="Admin SIP-BRIDA",
            email="admin@brida.makassarkota.go.id",
            password_hash="$2b$12$hashbcrypt",
            role="admin",
        )
    )
    db.commit()

    peran = {u.email: u.role for u in db.query(User).all()}
    assert set(peran.values()) == {"admin", "verifikator"}
