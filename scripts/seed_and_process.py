import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.database.connection import create_tables, SessionLocal
from app.database.models import Document
from app.evaluation.dataset import get_all_pdfs
from app.pipeline.runner import PipelineRunner

def main():
    print("=" * 70)
    print("Ingesting and processing all PDFs into database...")
    print("=" * 70)
    create_tables()

    pdf_files = get_all_pdfs()
    print(f"Total PDFs found: {len(pdf_files)}")

    runner = PipelineRunner()
    db = SessionLocal()

    success_count = 0
    scanned_count = 0

    try:
        for idx, fname in enumerate(pdf_files, 1):
            fpath = settings.DOCUMENTS_DIR / fname
            # Check if already processed
            existing = db.query(Document).filter(Document.original_filename == fname).first()
            if existing and existing.status == "completed":
                print(f"[{idx}/{len(pdf_files)}] [ALREADY PROCESSED] {fname}")
                success_count += 1
                if existing.is_scanned:
                    scanned_count += 1
                continue

            print(f"[{idx}/{len(pdf_files)}] Processing {fname}...")
            try:
                res = runner.process_file(fpath, db=db)
                print(f"    -> Nomor: {res.get('nomor_surat') or '-'} | Tanggal: {res.get('tanggal_surat') or '-'} | Skor: {int(res['confidence_score']*100)}%")
                success_count += 1
                if res.get("is_scanned"):
                    scanned_count += 1
            except Exception as e:
                print(f"    -> [ERROR] Failed to process {fname}: {e}")

        print("\n" + "=" * 70)
        print(f"Processing Complete: {success_count}/{len(pdf_files)} documents processed successfully!")
        print(f"Scanned Documents Handled: {scanned_count}")
        print("=" * 70)
    finally:
        db.close()

if __name__ == "__main__":
    main()
