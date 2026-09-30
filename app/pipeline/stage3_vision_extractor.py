import io
import re
import base64
import logging
import requests
import cv2
import numpy as np
from PIL import Image
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("idp.stage3")

# Kata yang menandakan potongan ALAMAT/kop, bukan nomor naskah dinas.
# Nomor naskah dinas Indonesia hampir selalu berbentuk kode berslash seperti
# 421.2/125/KBH/UPT.SPF.SDI.TT2/XII/2024 - bukan angka pendek atau nama jalan.
_ADDRESS_WORDS = re.compile(
    r"(kelurahan|kel\.|kecamatan|kec\.|jalan|jl\.|kota|kabupaten|provinsi|"
    r"telepon|telp\.?|fax|email|pos-el|kode\s*pos|website|www\.|http|"
    r"\brt\b|\brw\b|\bnpsn\b|nip\b)",
    re.IGNORECASE,
)


def looks_like_document_number(candidate: str) -> bool:
    """Saring kandidat nomor surat: harus berkode resmi, bukan potongan alamat.

    Contoh yang DITERIMA : 421.2/125/KBH/UPT.SPF.SDI.TT2/XII/2024
                           400.3.10/2/S.Kep/Disdik/VIII/2026
                           500.10.30.3/2/VII/2026
    Contoh yang DITOLAK  : "16", "2 Makassar 90111",
                           "16 Kelurahan Tallo Kecamatan Tallo Kota Makassar"
    """
    if not candidate:
        return False
    nilai = candidate.strip(" .;,")
    if len(nilai) > 80 or len(nilai) < 5:
        return False
    # Nomor naskah dinas wajib memuat garis miring sebagai pemisah kode
    if "/" not in nilai:
        return False
    if _ADDRESS_WORDS.search(nilai):
        return False
    # Harus ada angka DAN huruf (kode instansi/kategori), bukan sekadar "12/34"
    if not re.search(r"\d", nilai) or not re.search(r"[A-Za-z]", nilai):
        return False
    # Nomor naskah dinas memuat kode berhuruf besar (SDN, KBH, UPT.SPF, VIII, S.Kep).
    # Pola serba huruf kecil seperti "sdi-tallo-tua-2-makassar-hadirkan" adalah
    # potongan URL berita, bukan nomor surat.
    if not re.search(r"[A-Z]", nilai):
        return False
    if re.search(r"[a-z]{3,}-[a-z]{3,}", nilai):
        return False
    return True

class ExtractedMetadata(BaseModel):
    nomor_surat: Optional[str] = None
    instansi: Optional[str] = None
    perihal: Optional[str] = None
    tanggal_surat: Optional[str] = None
    nama_pejabat: Optional[str] = None
    jabatan_pejabat: Optional[str] = None
    nip_pejabat: Optional[str] = None
    ada_stempel_basah: bool = False
    ada_tanda_tangan: bool = False
    source_engine: str = "smart_heuristics"

class Stage3VisionExtractor:
    """Stage 3: High-Accuracy Semantic & Visual Extraction via Gemini Flash or Smart Heuristics."""

    def __init__(self, gemini_api_key: str = ""):
        self.api_key = gemini_api_key

    def extract(self, text: str, pil_image: Optional[Image.Image] = None) -> ExtractedMetadata:
        """Attempt extraction using Gemini API if key is available, else use smart heuristics."""
        if self.api_key and pil_image:
            try:
                res = self._extract_via_gemini_vision(pil_image, text)
                if res and res.nomor_surat:
                    return res
            except Exception as e:
                logger.warning(f"Gemini API extraction failed ({e}), falling back to smart heuristics.")

        return self._extract_via_heuristics(text, pil_image)

    def _extract_via_gemini_vision(self, pil_image: Image.Image, context_text: str) -> ExtractedMetadata:
        """Call Gemini Flash Free Tier API with image & strict schema."""
        img_copy = pil_image.copy()
        img_copy.thumbnail((1600, 1600))
        buffer = io.BytesIO()
        img_copy.save(buffer, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        prompt = (
            "Kamu adalah sistem Intelligent Document Processing (IDP) spesialis dokumen naskah dinas resmi Indonesia. "
            "Ekstrak data berikut secara teliti dari gambar dokumen dalam format JSON ketat:\n"
            "{\n"
            '  "nomor_surat": "nomor surat dinas/SK lengkap (bukan alamat/jalan)",\n'
            '  "instansi": "nama instansi/pemerintah/dinas/unit kerja pengirim pada kop surat",\n'
            '  "perihal": "perihal surat atau judul SK / tentang",\n'
            '  "tanggal_surat": "tanggal surat/dokumen (format ISO YYYY-MM-DD jika memungkinkan)",\n'
            '  "nama_pejabat": "nama lengkap pejabat penandatangan",\n'
            '  "jabatan_pejabat": "jabatan pejabat penandatangan",\n'
            '  "nip_pejabat": "NIP pejabat 18 digit angka jika tertulis",\n'
            '  "ada_stempel_basah": true/false,\n'
            '  "ada_tanda_tangan": true/false\n'
            "}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        raw_content = data["candidates"][0]["content"]["parts"][0]["text"]

        import json
        parsed = json.loads(raw_content)
        return ExtractedMetadata(
            nomor_surat=parsed.get("nomor_surat"),
            instansi=parsed.get("instansi"),
            perihal=parsed.get("perihal"),
            tanggal_surat=parsed.get("tanggal_surat"),
            nama_pejabat=parsed.get("nama_pejabat"),
            jabatan_pejabat=parsed.get("jabatan_pejabat"),
            nip_pejabat=str(parsed.get("nip_pejabat")) if parsed.get("nip_pejabat") else None,
            ada_stempel_basah=bool(parsed.get("ada_stempel_basah")),
            ada_tanda_tangan=bool(parsed.get("ada_tanda_tangan")),
            source_engine="gemini_flash"
        )

    def _extract_via_heuristics(self, text: str, pil_image: Optional[Image.Image] = None) -> ExtractedMetadata:
        """Robust offline heuristic extractor tuned for Indonesian government correspondence."""
        res = ExtractedMetadata()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # 1. Nomor Surat - kandidat disaring ketat supaya tidak menangkap alamat
        for line in lines:
            nomor_match = re.search(r'\b(?:Nomor|NOMOR|No)\s*[:.]?\s*(.{3,90})', line)
            if not nomor_match:
                continue
            candidate = nomor_match.group(1)
            # Potong sebelum kata kunci yang jelas bukan bagian nomor
            candidate = re.split(
                r'\s{2,}|Lampiran|Sifat|Perihal|Hal|TENTANG|Tanggal|Tgl|Tentang',
                candidate, flags=re.IGNORECASE
            )[0].strip(" .;,")
            if looks_like_document_number(candidate):
                res.nomor_surat = candidate
                break

        # 1b. Fallback: cari pola nomor naskah dinas langsung (tanpa kata "Nomor")
        if not res.nomor_surat:
            for match in re.finditer(
                r'\b(\d{1,4}(?:\.\d{1,4}){0,3}/[0-9A-Za-z.\-]+(?:/[0-9A-Za-z.\-]+){1,5})\b', text
            ):
                kandidat = match.group(1).strip(" .;,")
                if looks_like_document_number(kandidat):
                    res.nomor_surat = kandidat
                    break

        # 2. Instansi / Kop Surat (typically first 1-4 lines)
        instansi_candidates = []
        for line in lines[:8]:
            if re.search(r'\b(?:jl|jalan|alamat|telepon|email|pos-el|fax|kode pos)\b', line, re.IGNORECASE):
                continue
            if re.search(r'PEMERINTAH|DINAS|UPT|BADAN|SEKOLAH|KOMUNITAS|KEMENTERIAN|KOTA|KABUPATEN|SDI', line, re.IGNORECASE):
                instansi_candidates.append(line)
        if instansi_candidates:
            # Join with space for standard naming
            res.instansi = " ".join(instansi_candidates[:2])

        # 3. Perihal / Judul
        perihal_match = re.search(r'(?:Perihal|Hal|TENTANG)\s*[:.]?\s*([^\n\r]+(?:\n[^\n\r]+)?)', text, re.IGNORECASE)
        if perihal_match:
            perihal_text = perihal_match.group(1).replace("\n", " ").strip()
            res.perihal = re.sub(r'\s+', ' ', perihal_text)[:200]
        elif re.search(r'SURAT\s+PERNYATAAN', text, re.IGNORECASE):
            res.perihal = "Surat Pernyataan"
        elif re.search(r'KEPUTUSAN\s+KEPALA', text, re.IGNORECASE):
            res.perihal = "Keputusan Kepala Dinas / Pejabat"
        elif re.search(r'RASIO\s+PENGADUAN', text, re.IGNORECASE):
            res.perihal = "Rasio Pengaduan"
        elif re.search(r'SOSIALISASI\s+TIM', text, re.IGNORECASE):
            res.perihal = "Sosialisasi Tim Penggerak Genting"

        # 4. Tanggal Surat
        bulan = r'(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)'
        date_match = re.search(rf'\b(\d{{1,2}}\s+{bulan}\s+\d{{4}})\b', text, re.IGNORECASE)
        if date_match:
            res.tanggal_surat = date_match.group(1)

        # 5. NIP Pejabat
        nip_match = re.search(r'(?:NIP|Nip)\.?\s*[:.]?\s*([0-9 ]{18,22})', text)
        if nip_match:
            res.nip_pejabat = re.sub(r'\D', '', nip_match.group(1))
        else:
            nip_standalone = re.search(r'\b(19\d{6}|20\d{6})\s?([012]\d{5})\s?([12])\s?(\d{3})\b', text)
            if nip_standalone:
                res.nip_pejabat = "".join(nip_standalone.groups())

        # 6. Pejabat Nama & Jabatan
        jabatan_match = re.search(r'(Kepala\s+[^\n,]+|Plt\.\s+Kepala\s+[^\n,]+|Lurah\s+[^\n,]+|Camat\s+[^\n,]+)', text, re.IGNORECASE)
        if jabatan_match:
            res.jabatan_pejabat = jabatan_match.group(1).strip()

        if res.nip_pejabat and lines:
            for idx, line in enumerate(lines):
                if res.nip_pejabat in line or "NIP" in line:
                    if idx > 0:
                        candidate_name = lines[idx-1].strip()
                        if len(candidate_name) > 3 and not re.search(r'pembina|golongan|nip', candidate_name, re.IGNORECASE):
                            res.nama_pejabat = candidate_name
                    break

        # 7. Visual stamp & signature detection via OpenCV
        if pil_image:
            img_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            blue_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
            blue_pixels = cv2.countNonZero(blue_mask)
            if blue_pixels > 800:
                res.ada_stempel_basah = True
                res.ada_tanda_tangan = True

        res.source_engine = "smart_heuristics"
        return res
