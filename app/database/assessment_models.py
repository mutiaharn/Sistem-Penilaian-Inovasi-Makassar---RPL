"""
Domain model tahap PENILAIAN indikator (Tahap 1 AI + Tahap 2 Human-in-the-Loop).

Pemisahan domain ini disengaja:
  - app/database/models.py     -> dokumen & hasil ekstraksi IDP (input)
  - app/database/assessment_models.py -> usulan, indikator, parameter, keputusan (proses bisnis)

Prinsip yang dipegang (lihat docs/DATA_MODEL.md):
  1. Hasil AI dan keputusan manusia disimpan di TABEL BERBEDA. Draf AI tidak
     pernah menimpa keputusan manusia, sehingga audit override bisa dibuktikan.
  2. Setiap keputusan manusia menyimpan snapshot rekomendasi AI saat itu
     (ai_rekomendasi_snapshot), agar perubahan model tidak merusak riwayat.
  3. Indikator/parameter tidak di-hardcode di kode: dirujuk dari katalog
     data/reference/indikator_2026.json lewat tabel reference_indicators.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class User(Base):
    """Akun pengguna sistem (Admin / Verifikator BRIDA)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt
    role = Column(String(32), nullable=False, default="verifikator")  # admin | verifikator
    opd = Column(String(160), nullable=True)
    aktif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decisions = relationship("HumanDecision", back_populates="decided_by_user")


class ReferenceIndicator(Base):
    """Katalog indikator resmi (hasil seed data/reference/indikator_2026.json)."""

    __tablename__ = "reference_indicators"

    id = Column(String(16), primary_key=True)  # IND-01
    kode = Column(String(64), nullable=False, unique=True)
    nama = Column(String(255), nullable=False)
    definisi = Column(Text, nullable=True)
    mandatori = Column(Boolean, default=False)
    aktif_tahap_1 = Column(Boolean, default=True)
    urutan = Column(Integer, nullable=False, default=0)
    skor_maksimum = Column(Float, nullable=True)
    evidence_tags = Column(JSON, nullable=True)  # ["regulasi"]
    bukti_dukung = Column(JSON, nullable=True)

    parameters = relationship(
        "ReferenceParameter",
        back_populates="indicator",
        order_by="ReferenceParameter.skor",
    )


class ReferenceParameter(Base):
    """Tingkat parameter (P1/P2/P3) beserta skornya."""

    __tablename__ = "reference_parameters"

    id = Column(String(24), primary_key=True)  # IND-01-P1
    indicator_id = Column(String(16), ForeignKey("reference_indicators.id"), nullable=False)
    nama = Column(Text, nullable=False)
    skor = Column(Float, nullable=False, default=0.0)
    urutan = Column(Integer, nullable=False, default=0)

    indicator = relationship("ReferenceIndicator", back_populates="parameters")


class Innovation(Base):
    """Usulan inovasi daerah (satu baris per inovasi yang dievaluasi)."""

    __tablename__ = "innovations"

    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(64), unique=True, index=True, nullable=False)  # inovasi_id dari formulir
    nama_inovasi = Column(String(255), nullable=False)
    opd = Column(String(255), nullable=False)
    jenis = Column(String(64), nullable=True)
    tahun = Column(Integer, nullable=True)
    deskripsi = Column(Text, nullable=True)

    # MENUNGGU_EVALUASI_AI -> MENUNGGU_KONFIRMASI_MANUSIA -> TERVERIFIKASI_FINAL
    status = Column(String(48), default="MENUNGGU_EVALUASI_AI", index=True)
    skor_total = Column(Float, nullable=True)
    skor_maksimum = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Pengesahan final (UC-06): jejak audit tidak boleh hilang
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String(128), nullable=True)

    indicators = relationship(
        "InnovationIndicator", back_populates="innovation", cascade="all, delete-orphan"
    )
    evidences = relationship(
        "Evidence", back_populates="innovation", cascade="all, delete-orphan"
    )


class InnovationIndicator(Base):
    """Status evaluasi satu indikator di dalam satu usulan inovasi."""

    __tablename__ = "innovation_indicators"
    __table_args__ = (UniqueConstraint("innovation_id", "indicator_id", name="uq_inovasi_indikator"),)

    id = Column(Integer, primary_key=True, index=True)
    innovation_id = Column(Integer, ForeignKey("innovations.id", ondelete="CASCADE"), nullable=False)
    indicator_id = Column(String(16), ForeignKey("reference_indicators.id"), nullable=False)

    # Tingkat yang DIKLAIM pengaju; AI memverifikasi klaim ini (bukan menebak dari nol)
    klaim_parameter_id = Column(String(24), ForeignKey("reference_parameters.id"), nullable=True)
    # Tingkat yang akhirnya disetujui reviewer
    disetujui_parameter_id = Column(String(24), ForeignKey("reference_parameters.id"), nullable=True)

    status = Column(String(48), default="MENUNGGU_EVALUASI_AI", index=True)  # ... | SELESAI
    reviewer_note = Column(Text, nullable=True)
    finalized_at = Column(DateTime, nullable=True)

    innovation = relationship("Innovation", back_populates="indicators")
    assessments = relationship(
        "ParameterAssessment", back_populates="innovation_indicator", cascade="all, delete-orphan"
    )
    decisions = relationship(
        "HumanDecision", back_populates="innovation_indicator", cascade="all, delete-orphan"
    )


class Evidence(Base):
    """Berkas bukti pendukung, terikat ke satu indikator (pemetaan dari formulir).

    Bukti fisiknya sendiri (PDF) tetap dilacak oleh tabel `documents`; tabel ini
    menyimpan PERAN bukti tersebut dalam penilaian.
    """

    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(32), unique=True, index=True, nullable=False)  # EVD-0001
    innovation_id = Column(Integer, ForeignKey("innovations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    indicator_id = Column(String(16), ForeignKey("reference_indicators.id"), nullable=True)
    evidence_tag = Column(String(64), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=True, index=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    verification_url = Column(Text, nullable=True)
    catatan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    innovation = relationship("Innovation", back_populates="evidences")


class ParameterAssessment(Base):
    """DRAF rekomendasi AI untuk satu parameter indikator (Tahap 1).

    Hanya AI yang menulis di tabel ini. Reviewer tidak pernah mengubah baris ini.
    """

    __tablename__ = "parameter_assessments"

    id = Column(Integer, primary_key=True, index=True)
    innovation_indicator_id = Column(
        Integer, ForeignKey("innovation_indicators.id", ondelete="CASCADE"), nullable=False
    )
    parameter_id = Column(String(24), ForeignKey("reference_parameters.id"), nullable=False)

    rekomendasi = Column(String(24), nullable=False)  # LOLOS | PERLU_REVISI | TIDAK_LOLOS
    confidence_score = Column(Float, default=0.0)
    ai_catatan = Column(Text, nullable=True)
    evidence_ids = Column(JSON, nullable=True)  # bukti yang benar-benar dibaca AI
    kutipan = Column(JSON, nullable=True)       # kutipan teks/halaman sebagai justifikasi

    # Gagal evaluasi (UC-03 alur alternatif 3a) -> reviewer menilai manual
    status = Column(String(32), default="OK")  # OK | EVALUASI_AI_GAGAL
    engine = Column(String(48), nullable=True)  # gemini_flash | rule_based | manual
    attempt_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    innovation_indicator = relationship("InnovationIndicator", back_populates="assessments")


class HumanDecision(Base):
    """KEPUTUSAN reviewer manusia per parameter (Tahap 2).

    `is_override` dihitung & disimpan agar laporan audit bisa menunjukkan berapa
    kali manusia mengoreksi AI (kebutuhan non-fungsional 3.3.2 audit log).
    """

    __tablename__ = "human_decisions"

    id = Column(Integer, primary_key=True, index=True)
    innovation_indicator_id = Column(
        Integer, ForeignKey("innovation_indicators.id", ondelete="CASCADE"), nullable=False
    )
    parameter_id = Column(String(24), ForeignKey("reference_parameters.id"), nullable=False)

    keputusan = Column(String(24), nullable=False)  # LOLOS | REVISI | TOLAK
    catatan = Column(Text, nullable=True)

    ai_rekomendasi_snapshot = Column(String(24), nullable=True)
    ai_confidence_snapshot = Column(Float, nullable=True)
    is_override = Column(Boolean, default=False)

    decided_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_by_nama = Column(String(128), nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    innovation_indicator = relationship("InnovationIndicator", back_populates="decisions")
    decided_by_user = relationship("User", back_populates="decisions")


class AuditLog(Base):
    """Jejak audit seluruh aksi yang mengubah state (khususnya override nilai AI)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(128), nullable=True)
    actor_role = Column(String(32), nullable=True)
    action = Column(String(64), nullable=False)  # CREATE | UPDATE | DECIDE | FINALIZE | EXPORT
    entity = Column(String(64), nullable=False)  # innovation_indicator | human_decision | ...
    entity_id = Column(String(64), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
