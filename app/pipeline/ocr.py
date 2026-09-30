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


def _varian_gambar(gambar: Image.Image) -> list[tuple[str, Image.Image, float]]:
    """Beberapa prapemrosesan dari halaman yang sama + faktor skala masing-masing.

    Semuanya tetap berasal dari dokumen asli - tidak ada nilai yang ditambahkan.
    Faktor skala WAJIB dikembalikan: varian 2x menghasilkan koordinat y dua kali
    lipat, sehingga tanpa koreksi baris dari skala berbeda akan salah digabung
    (pernah membuat 36 baris menyusut jadi 20 - teks hilang).
    """
    import numpy as np
    from PIL import ImageEnhance, ImageFilter, ImageOps

    keluar: list[tuple[str, Image.Image, float]] = [("asli", gambar, 1.0)]

    # 2x upscale + skala abu: membantu huruf kecil dan hasil scan rapat
    besar = gambar.resize((gambar.width * 2, gambar.height * 2), Image.LANCZOS)
    abu = ImageOps.grayscale(besar)
    skala2 = besar.width / max(gambar.width, 1)
    keluar.append(("upscale_abu", abu, skala2))

    # + penajaman kontras: membantu scan buram/pudar
    tajam = ImageEnhance.Contrast(abu).enhance(1.8).filter(
        ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)
    )
    keluar.append(("upscale_tajam", tajam.convert("RGB"), skala2))

    # + ambang adaptif: membantu kertas kotor, bayangan, dan derau
    try:
        import cv2

        arr = np.array(abu)
        biner = cv2.adaptiveThreshold(
            arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
        )
        keluar.append(("upscale_biner", Image.fromarray(biner).convert("RGB"), skala2))
    except Exception:  # noqa: BLE001 - cv2 tidak wajib ada
        pass

    return keluar


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

    # --- OCR multi-prapemrosesan (mutu lebih tinggi) ---------------------------

    def proses_terbaik(self, gambar: Image.Image) -> HasilOcr:
        """OCR dengan beberapa prapemrosesan, lalu pilih SATU hasil terbaik secara utuh.

        Riwayat penting: versi pertama menggabungkan bacaan PER BARIS antar varian
        berdasarkan posisi. Itu terbukti MERUGI - penggabungan posisi membuat baris
        yang berdekatan menyatu, dan teks menyusut dari 264 menjadi 104 karakter pada
        dokumen uji: sebagian isi hilang tanpa jejak. Pemilihan utuh tidak bisa
        menghilangkan baris seperti itu.

        Aturannya: hanya varian yang cakupan teksnya sebanding (>= 95% varian terpanjang)
        yang boleh menang, lalu dipilih yang keyakinannya tertinggi. Jadi keyakinan
        tinggi TIDAK bisa menang dengan cara membuang teks.
        """
        if not self.siap():
            return HasilOcr(mesin="none")
        if self.mesin_aktif != "rapidocr":
            return self.proses(gambar)      # mesin lain tidak memberi skor keyakinan

        bacaan: list[tuple[str, HasilOcr]] = []
        for nama, img, _skala in _varian_gambar(gambar):
            hasil = self._pakai_rapidocr(img)
            if hasil.ada_isi:
                bacaan.append((nama, hasil))
        if not bacaan:
            return HasilOcr(mesin="rapidocr")

        terpanjang = max(len(h.teks) for _, h in bacaan)
        layak = [(n, h) for n, h in bacaan if len(h.teks) >= 0.95 * terpanjang]
        nama, terbaik = max(layak, key=lambda nh: nh[1].rata_keyakinan)
        return HasilOcr(
            teks=terbaik.teks,
            baris=terbaik.baris,
            rata_keyakinan=terbaik.rata_keyakinan,
            mesin=f"rapidocr+{nama}",
        )

    def proses_terbaik_banyak(self, gambar_list: list[Image.Image]) -> HasilOcr:
        """proses_terbaik() untuk beberapa halaman sekaligus."""
        baris_semua: list[str] = []
        skor: list[float] = []
        mesin = self.mesin_aktif
        for g in gambar_list:
            hasil = self.proses_terbaik(g)
            baris_semua.extend(hasil.baris)
            if hasil.rata_keyakinan:
                skor.append(hasil.rata_keyakinan)
            if "+" in hasil.mesin:
                mesin = hasil.mesin
        return HasilOcr(
            teks="\n".join(baris_semua),
            baris=baris_semua,
            rata_keyakinan=(sum(skor) / len(skor)) if skor else 0.0,
            mesin=mesin,
        )

    def proses_adaptif(self, gambar: Image.Image, ambang_yakin: float = 0.80) -> HasilOcr:
        """proses() dulu (cepat); hanya bila hasilnya lemah, coba prapemrosesan lain.

        Multi-varian sekitar 3-4x lebih lambat, jadi memakainya untuk semua halaman
        membuat rebuild korpus berjam-jam. Halaman yang sudah terbaca baik dengan
        sekali jalan tidak perlu diulang.

        Aturan pemilihan: varian alternatif hanya menang bila cakupan teksnya tidak
        berkurang (>= 90% teks hasil cepat) DAN keyakinannya lebih tinggi. Ini mencegah
        "menang dengan keyakinan tinggi" padahal teksnya justru berkurang.
        """
        dasar = self.proses(gambar)
        if dasar.rata_keyakinan >= ambang_yakin and len(dasar.baris) >= 5:
            return dasar
        lanjutan = self.proses_terbaik(gambar)
        if not lanjutan.ada_isi:
            return dasar
        if len(lanjutan.teks) < 0.90 * max(len(dasar.teks), 1):
            return dasar
        if lanjutan.rata_keyakinan > dasar.rata_keyakinan or len(lanjutan.teks) > len(dasar.teks):
            return lanjutan
        return dasar

    def proses_adaptif_banyak(self, gambar_list: list[Image.Image]) -> HasilOcr:
        """proses_adaptif() untuk beberapa halaman sekaligus."""
        baris_semua: list[str] = []
        skor: list[float] = []
        mesin = self.mesin_aktif
        for g in gambar_list:
            hasil = self.proses_adaptif(g)
            baris_semua.extend(hasil.baris)
            if hasil.rata_keyakinan:
                skor.append(hasil.rata_keyakinan)
            if "multipass" in hasil.mesin:
                mesin = hasil.mesin
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
