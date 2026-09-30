"""
Penjaga privasi untuk pemakaian AI Vision (Google Gemini).

KEBIJAKAN YANG DIPAKSA OLEH KODE INI
------------------------------------
1. **PDF tidak pernah dikirim.** Yang dikirim hanya CITRA halaman yang sudah
   dirasterisasi lokal, dan hanya halaman yang benar-benar diperlukan.
2. **Dokumen digital-native tidak dikirim.** Bila PDF punya lapisan teks
   (`is_scanned = false`), isinya sudah bisa dibaca lokal - tidak ada alasan
   mengirimkannya keluar. Hanya dokumen tanpa lapisan teks (hasil scan) yang
   boleh dikirim, dan itu pun hanya halamannya.
3. **Setiap pengiriman dicatat** ke storage/audit_kirim_api.jsonl: waktu, nama
   berkas, SHA-256, jumlah halaman yang dikirim, model, dan alasan.
4. Kebijakan dapat diubah HANYA lewat variabel lingkungan, dengan sadar:
       GEMINI_VISION_POLICY=scanned_only   (bawaan)
       GEMINI_VISION_POLICY=off            (tidak pernah mengirim apa pun)
       GEMINI_VISION_POLICY=all            (semua dokumen - PERLU PERSETUJUAN)

Modul ini TIDAK melakukan panggilan jaringan saat diimpor. Semua panggilan
melewati `boleh_kirim()` lebih dulu.
"""

import base64
import io
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image

from app.core.config import settings

logger = logging.getLogger("idp.vision_ai")
WITA = timezone(timedelta(hours=8))
AUDIT_FILE = settings.STORAGE_DIR / "audit_kirim_api.jsonl"

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAKS_HALAMAN_PER_KIRIM = 4  # batas wajar; halaman berlebih dikirim terpisah


def kebijakan() -> str:
    return os.getenv("GEMINI_VISION_POLICY", "scanned_only").strip().lower()


def ada_kunci() -> bool:
    return bool(settings.GEMINI_API_KEY)


def boleh_kirim(meta: dict) -> tuple[bool, str]:
    """Tentukan apakah dokumen ini boleh dikirim ke layanan AI eksternal.

    Mengembalikan (boleh, alasan). Alasan selalu diisi - dipakai untuk audit
    dan log, termasuk saat permintaan DITOLAK.
    """
    pol = kebijakan()
    if pol == "off":
        return False, "GEMINI_VISION_POLICY=off: pengiriman ke API dimatikan"
    if not ada_kunci():
        return False, "GEMINI_API_KEY kosong"
    if pol == "all":
        return True, "GEMINI_VISION_POLICY=all: seluruh dokumen diizinkan (persetujuan eksplisit)"
    if pol == "scanned_only":
        if meta.get("is_scanned"):
            return True, "dokumen tanpa lapisan teks (scan) - hanya halaman yang dikirim"
        return False, "dokumen digital-native punya lapisan teks: diproses lokal, tidak dikirim"
    return False, f"kebijakan tidak dikenal: {pol}"


def _catat_audit(entri: dict) -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entri["waktu"] = datetime.now(WITA).isoformat(timespec="seconds")
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entri, ensure_ascii=False) + "\n")


def _ke_base64_jpeg(gambar: Image.Image, maks_sisi: int = 1600, kualitas: int = 85) -> str:
    salinan = gambar.copy()
    salinan.thumbnail((maks_sisi, maks_sisi))
    buf = io.BytesIO()
    salinan.save(buf, format="JPEG", quality=kualitas)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def ekstrak_dengan_vision(
    nama_berkas: str,
    sha256: str,
    meta: dict,
    gambar_halaman: list[Image.Image],
    prompt: str,
    model: str | None = None,
) -> dict:
    """Kirim halaman terpilih ke Gemini Vision dan kembalikan dict hasil.

    Menolak dengan jelas (tanpa panggilan jaringan) bila kebijakan tidak mengizinkan.
    """
    model = model or settings.GEMINI_MODEL
    boleh, alasan = boleh_kirim(meta)
    if not boleh:
        _catat_audit({
            "aksi": "TOLAK_KIRIM", "berkas": nama_berkas, "sha256": sha256,
            "alasan": alasan, "halaman_terkirim": 0,
        })
        return {"ditolak": True, "alasan": alasan, "hasil": None}

    halaman = gambar_halaman[:MAKS_HALAMAN_PER_KIRIM]
    _catat_audit({
        "aksi": "KIRIM", "berkas": nama_berkas, "sha256": sha256,
        "alasan": alasan, "model": model,
        "halaman_terkirim": len(halaman),
        "halaman_total_dokumen": meta.get("page_count"),
    })

    import requests

    parts: list[dict] = [{"text": prompt}]
    for g in halaman:
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": _ke_base64_jpeg(g)}})

    url = ENDPOINT.format(model=model)
    coba = 0
    for coba in range(1, 4):  # sampai 3 percobaan, sesuai SRS UC-03 alur alternatif 3a
        try:
            resp = requests.post(
                url,
                params={"key": settings.GEMINI_API_KEY},
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {"response_mime_type": "application/json"},
                },
                timeout=60,
            )
            if resp.status_code == 429:
                logger.warning(f"Kuota API tercapai (429), percobaan {coba}/3")
                continue
            resp.raise_for_status()
            teks = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return {"ditolak": False, "alasan": alasan, "hasil": json.loads(teks), "percobaan": coba}
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Panggilan Vision gagal (percobaan {coba}/3): {exc}")

    _catat_audit({"aksi": "GAGAL", "berkas": nama_berkas, "sha256": sha256, "percobaan": coba})
    return {"ditolak": False, "alasan": alasan, "hasil": None, "gagal": True, "percobaan": coba}


def ringkasan_audit() -> dict:
    """Ringkasan isi audit: berapa dokumen yang benar-benar pernah dikirim keluar."""
    if not AUDIT_FILE.exists():
        return {"ada": False, "kirim": 0, "tolak": 0, "gagal": 0, "berkas_dikirim": []}
    kirim = tolak = gagal = 0
    berkas: list[str] = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for baris in f:
            try:
                e = json.loads(baris)
            except json.JSONDecodeError:
                continue
            if e.get("aksi") == "KIRIM":
                kirim += 1
                berkas.append(e.get("berkas", "?"))
            elif e.get("aksi") == "TOLAK_KIRIM":
                tolak += 1
            elif e.get("aksi") == "GAGAL":
                gagal += 1
    return {"ada": True, "kirim": kirim, "tolak": tolak, "gagal": gagal, "berkas_dikirim": sorted(set(berkas))}
