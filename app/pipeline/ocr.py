"""
Mesin OCR lokal - dipasang DI DALAM virtual environment, tanpa binary sistem.

Kenapa begini: seluruh berkas proyek bisa dihapus tanpa meninggalkan sisa di sistem.
Tidak ada data yang keluar dari laptop (offline penuh).

Urutan mesin yang dicoba:
  1. rapidocr-onnxruntime  - murni pip, model PP-OCR (latin+china) sudah di dalam wheel
  2. pytesseract           - dipakai hanya bila binary tesseract tersedia
  3. none                  - OCR tidak tersedia; pemanggil harus menanganinya dengan jujur

Hasil OCR dipakai sebagai MASUKAN teks untuk Stage 3 (heuristik) yang sudah ada,
sehingga tidak ada logika ekstraksi yang terduplikasi.
"""

import logging
import shutil
from dataclasses import dataclass, field
from functools import lru_cache

from PIL import Image

logger = logging.getLogger("idp.ocr")


@dataclass
class HasilOcr:
    teks: str = ""
    baris: list[str] = field(default_factory=list)
    rata_keyakinan: float = 0.0
    mesin: str = "none"

    @property
    def ada_isi(self) -> bool:
        return bool(self.teks.strip())


class OcrLokal:
    """Pembungkus mesin OCR lokal dengan pemilihan mesin otomatis."""

    def __init__(self, mesin: str = "auto"):
        self.diminta = mesin
        self._rapid = None
        self._tesseract_cmd = None
        self.mesin_aktif = "none"
        self._inisialisasi()

    # --- pemilihan mesin -------------------------------------------------------

    def _inisialisasi(self) -> None:
        if self.diminta in ("auto", "rapidocr"):
            if self._coba_rapidocr():
                return
        if self.diminta in ("auto", "tesseract"):
            if self._coba_tesseract():
                return
        if self.diminta != "none":
            logger.warning("Tidak ada mesin OCR yang siap. OCR dilewati.")

    def _coba_rapidocr(self) -> bool:
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore

            self._rapid = RapidOCR()
            self.mesin_aktif = "rapidocr"
            logger.info("OCR siap: rapidocr (onnxruntime, di dalam venv)")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"rapidocr tidak tersedia: {exc}")
            return False

    def _coba_tesseract(self) -> bool:
        """Cari binary tesseract: di dalam venv dulu, baru di sistem."""
        from pathlib import Path

        dari_venv = Path(__file__).resolve().parent.parent.parent / ".venv" / "tesseract" / "tesseract.exe"
        kandidat = [
            str(dari_venv) if dari_venv.exists() else None,   # dipasang di dalam venv
            shutil.which("tesseract"),                        # terpasang di sistem
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        ]
        for kandidat_path in filter(None, kandidat):
            try:
                import pytesseract  # type: ignore

                pytesseract.pytesseract.tesseract_cmd = kandidat_path
                pytesseract.get_tesseract_version()
                self._tesseract_cmd = kandidat_path
                self.mesin_aktif = "tesseract"
                logger.info(f"OCR siap: tesseract ({kandidat_path})")
                return True
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"tesseract tidak siap di {kandidat_path}: {exc}")
        return False

    # --- pemakaian -------------------------------------------------------------

    def siap(self) -> bool:
        return self.mesin_aktif != "none"

    def proses(self, gambar: Image.Image) -> HasilOcr:
        if not self.siap():
            return HasilOcr(mesin="none")

        if self.mesin_aktif == "rapidocr":
            return self._pakai_rapidocr(gambar)
        if self.mesin_aktif == "tesseract":
            return self._pakai_tesseract(gambar)
        return HasilOcr(mesin="none")

    def proses_banyak(self, gambar_list: list[Image.Image]) -> HasilOcr:
        """OCR beberapa halaman lalu gabungkan teksnya."""
        baris_semua: list[str] = []
        skor: list[float] = []
        mesin = self.mesin_aktif
        for g in gambar_list:
            hasil = self.proses(g)
            baris_semua.extend(hasil.baris)
            if hasil.rata_keyakinan:
                skor.append(hasil.rata_keyakinan)
        return HasilOcr(
            teks="\n".join(baris_semua),
            baris=baris_semua,
            rata_keyakinan=(sum(skor) / len(skor)) if skor else 0.0,
            mesin=mesin,
        )

    def _pakai_rapidocr(self, gambar: Image.Image) -> HasilOcr:
        import numpy as np

        hasil, _waktu = self._rapid(np.array(gambar))  # type: ignore[misc]
        if not hasil:
            return HasilOcr(mesin="rapidocr")
        baris = [b[1] for b in hasil if len(b) > 1 and b[1]]
        keyakinan = [float(b[2]) for b in hasil if len(b) > 2 and b[2] is not None]
        return HasilOcr(
            teks="\n".join(baris),
            baris=baris,
            rata_keyakinan=(sum(keyakinan) / len(keyakinan)) if keyakinan else 0.0,
            mesin="rapidocr",
        )

    def _pakai_tesseract(self, gambar: Image.Image) -> HasilOcr:
        import pytesseract  # type: ignore

        teks = pytesseract.image_to_string(gambar, lang="ind+eng")
        baris = [b.strip() for b in teks.splitlines() if b.strip()]
        return HasilOcr(teks=teks, baris=baris, rata_keyakinan=0.0, mesin="tesseract")


@lru_cache(maxsize=1)
def ocr_default() -> OcrLokal:
    """Satu instance OCR untuk seluruh proses (muat model hanya sekali)."""
    return OcrLokal(mesin="auto")


def status_ocr() -> dict:
    """Ringkasan untuk laporan/CLI tanpa harus memproses gambar."""
    mesin = ocr_default()
    return {
        "siap": mesin.siap(),
        "mesin": mesin.mesin_aktif,
        "offline": True,
        "catatan": "OCR berjalan lokal di dalam venv; tidak ada data keluar dari perangkat",
    }
