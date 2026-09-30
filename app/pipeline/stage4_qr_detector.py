import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode as zbar_decode

class Stage4QrDetector:
    """Stage 4: Heuristic QR Code & Digital Signature (TTE BSrE) Verification Reader."""

    def scan_image(self, pil_img: Image.Image) -> list[dict]:
        """Scan a PIL image for QR codes and barcodes."""
        results = []

        # 1. First pass: PyZbar
        try:
            decoded = zbar_decode(pil_img)
            for d in decoded:
                data_str = d.data.decode("utf-8", errors="ignore").strip()
                if data_str:
                    results.append({
                        "type": d.type,
                        "data": data_str,
                        "detector": "pyzbar"
                    })
        except Exception:
            pass

        # 2. Second pass: OpenCV QRCodeDetector fallback
        if not results:
            try:
                img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                val, points, qrcode = detector.detectAndDecode(img_bgr)
                if val:
                    results.append({
                        "type": "QRCODE",
                        "data": val.strip(),
                        "detector": "opencv"
                    })
            except Exception:
                pass

        return results

    def extract_verification_url(self, images: list[Image.Image]) -> str | None:
        """Scan candidate page images (usually page 1 and signature page) for verification URL."""
        for img in images:
            codes = self.scan_image(img)
            for c in codes:
                data = c["data"]
                if data.startswith("http://") or data.startswith("https://"):
                    return data
                if "tte" in data.lower() or "bsre" in data.lower() or "sigap" in data.lower():
                    return data
        return None
