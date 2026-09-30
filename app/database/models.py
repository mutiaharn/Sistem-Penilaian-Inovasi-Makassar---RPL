from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, 
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), index=True, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    is_scanned = Column(Boolean, default=False)
    status = Column(String(32), default="pending")  # pending, processing, completed, failed
    needs_manual_review = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    extractions = relationship("DocumentExtraction", back_populates="document", cascade="all, delete-orphan")

class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    nomor_surat = Column(String(255), index=True, nullable=True)
    instansi = Column(Text, nullable=True)
    perihal = Column(Text, nullable=True)
    tanggal_surat = Column(String(32), nullable=True)  # ISO-8601 YYYY-MM-DD
    nama_pejabat = Column(String(255), nullable=True)
    jabatan_pejabat = Column(String(255), nullable=True)
    nip_pejabat = Column(String(32), nullable=True)
    ada_stempel_basah = Column(Boolean, default=False)
    ada_tanda_tangan = Column(Boolean, default=False)
    verification_url = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0)
    raw_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="extractions")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    iteration_name = Column(String(64), nullable=False)
    dataset_split = Column(String(32), default="test")
    total_documents = Column(Integer, default=0)
    accuracy_overall = Column(Float, default=0.0)
    field_accuracies = Column(JSON, nullable=True)
    metrics_detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
