import gc
import logging
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.models import Document, DocumentExtraction
from app.pipeline.stage1_inspector import Stage1Inspector
from app.pipeline.stage2_preprocessor import Stage2Preprocessor
from app.pipeline.stage3_vision_extractor import Stage3VisionExtractor, ExtractedMetadata
from app.pipeline.stage4_qr_detector import Stage4QrDetector
from app.pipeline.stage5_post_validator import Stage5PostValidator

logger = logging.getLogger("idp.pipeline")

class PipelineRunner:
    """Orchestrates Stages 1 to 5 with sturdy resource isolation and DB persistence."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.inspector = Stage1Inspector()
        self.preprocessor = Stage2Preprocessor(target_dpi=300)
        self.extractor = Stage3VisionExtractor(gemini_api_key or settings.GEMINI_API_KEY)
        self.qr_detector = Stage4QrDetector()
        self.validator = Stage5PostValidator()

    def process_file(self, pdf_path: str | Path, db: Optional[Session] = None) -> dict:
        pdf_path = Path(pdf_path)
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        candidate_images = []
        try:
            # Stage 1: Document Inspection
            logger.info(f"[Stage 1] Inspecting {pdf_path.name}...")
            meta = self.inspector.inspect(pdf_path)

            # Stage 2: High-Resolution Preprocessing (300 DPI + Deskew)
            logger.info(f"[Stage 2] Preprocessing pages for {pdf_path.name}...")
            p1_res = self.preprocessor.process(pdf_path, page_index=0)
            candidate_images.append(p1_res["pil_image"])

            if meta["page_count"] > 1:
                last_page_idx = meta["page_count"] - 1
                plast_res = self.preprocessor.process(pdf_path, page_index=last_page_idx)
                candidate_images.append(plast_res["pil_image"])

            # Stage 3: Vision / Semantic Extraction
            logger.info(f"[Stage 3] Semantic extraction...")
            extracted: ExtractedMetadata = self.extractor.extract(
                text=meta["extracted_text"],
                pil_image=candidate_images[0] if candidate_images else None
            )

            # Stage 4: Heuristic QR & Barcode Detection
            logger.info(f"[Stage 4] Scanning for verification QR codes...")
            verification_url = self.qr_detector.extract_verification_url(candidate_images)

            # Stage 5: Post-Validation & Self-Healing
            logger.info(f"[Stage 5] Deterministic validation & confidence scoring...")
            is_valid_nip, healed_nip = self.validator.validate_and_heal_nip(
                raw_nip=extracted.nip_pejabat,
                full_text=meta["extracted_text"]
            )
            iso_date = self.validator.normalize_indonesian_date(extracted.tanggal_surat)
            
            confidence, needs_review, flags = self.validator.evaluate_confidence(
                nomor_surat=extracted.nomor_surat,
                instansi=extracted.instansi,
                perihal=extracted.perihal,
                iso_tanggal=iso_date,
                cleaned_nip=healed_nip,
                is_valid_nip=is_valid_nip,
                verification_url=verification_url
            )

            # Persistence in Database (PostgreSQL / SQLite)
            existing_doc = db.query(Document).filter(Document.file_hash == meta["file_hash"]).first()
            if not existing_doc:
                existing_doc = Document(
                    original_filename=pdf_path.name,
                    file_path=str(pdf_path),
                    file_hash=meta["file_hash"],
                    file_size_bytes=meta["file_size_bytes"],
                    page_count=meta["page_count"],
                    is_scanned=meta["is_scanned"],
                    status="completed",
                    needs_manual_review=needs_review
                )
                db.add(existing_doc)
                db.flush()
            else:
                existing_doc.status = "completed"
                existing_doc.needs_manual_review = needs_review

            # Save extraction
            raw_payload = {
                "engine": extracted.source_engine,
                "raw_extracted": extracted.model_dump(),
                "validation_flags": flags,
                "skew_angle": p1_res.get("skew_angle", 0.0)
            }

            extraction_record = DocumentExtraction(
                document_id=existing_doc.id,
                nomor_surat=extracted.nomor_surat,
                instansi=extracted.instansi,
                perihal=extracted.perihal,
                tanggal_surat=iso_date or extracted.tanggal_surat,
                nama_pejabat=extracted.nama_pejabat,
                jabatan_pejabat=extracted.jabatan_pejabat,
                nip_pejabat=healed_nip or extracted.nip_pejabat,
                ada_stempel_basah=extracted.ada_stempel_basah,
                ada_tanda_tangan=extracted.ada_tanda_tangan,
                verification_url=verification_url,
                confidence_score=confidence,
                raw_json=raw_payload
            )
            db.add(extraction_record)
            db.commit()

            result = {
                "document_id": existing_doc.id,
                "filename": pdf_path.name,
                "page_count": meta["page_count"],
                "is_scanned": meta["is_scanned"],
                "nomor_surat": extracted.nomor_surat,
                "instansi": extracted.instansi,
                "perihal": extracted.perihal,
                "tanggal_surat": iso_date or extracted.tanggal_surat,
                "nama_pejabat": extracted.nama_pejabat,
                "jabatan_pejabat": extracted.jabatan_pejabat,
                "nip_pejabat": healed_nip or extracted.nip_pejabat,
                "is_valid_nip": is_valid_nip,
                "verification_url": verification_url,
                "confidence_score": confidence,
                "needs_manual_review": needs_review,
                "flags": flags
            }
            return result

        finally:
            # Explicit cleanup of image resources
            candidate_images.clear()
            gc.collect()
            if should_close_db:
                db.close()
