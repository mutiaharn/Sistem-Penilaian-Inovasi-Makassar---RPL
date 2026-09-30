import hashlib
from pathlib import Path
from pypdf import PdfReader

class Stage1Inspector:
    """Stage 1: Fast Document Inspection (Digital Native vs Scanned PDF)."""

    def __init__(self, min_word_threshold: int = 30):
        self.min_word_threshold = min_word_threshold

    def inspect(self, pdf_path: str | Path) -> dict:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Compute SHA-256 hash
        sha256 = hashlib.sha256()
        file_size = pdf_path.stat().st_size
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        file_hash = sha256.hexdigest()

        reader = PdfReader(str(pdf_path))
        num_pages = len(reader.pages)
        
        # Read page 1 text
        first_page_text = reader.pages[0].extract_text() or ""
        words = first_page_text.split()
        word_count = len(words)

        is_scanned = word_count < self.min_word_threshold

        # If digital, extract text from up to first 3 pages
        extracted_text = ""
        if not is_scanned:
            for i in range(min(3, num_pages)):
                extracted_text += (reader.pages[i].extract_text() or "") + "\n"

        return {
            "file_path": str(pdf_path),
            "filename": pdf_path.name,
            "file_hash": file_hash,
            "file_size_bytes": file_size,
            "page_count": num_pages,
            "words_page_1": word_count,
            "is_scanned": is_scanned,
            "extracted_text": extracted_text.strip()
        }
