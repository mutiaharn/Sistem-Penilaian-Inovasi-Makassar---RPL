import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import pypdfium2 as pdfium

class Stage2Preprocessor:
    """Stage 2: High-Resolution Rasterization (300 DPI) & Computer Vision Enhancement."""

    def __init__(self, target_dpi: int = 300):
        self.scale = target_dpi / 72.0

    def render_page(self, pdf_path: str | Path, page_index: int = 0) -> Image.Image:
        """Render a specific PDF page to high-res PIL Image."""
        doc = pdfium.PdfDocument(str(pdf_path))
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(f"Page index {page_index} out of range (total {len(doc)} pages)")
        page = doc[page_index]
        return page.render(scale=self.scale).to_pil()

    def deskew_image(self, img_bgr: np.ndarray) -> tuple[np.ndarray, float]:
        """Detect skew angle and rotate image to level horizontal lines."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Invert and threshold to find text pixels
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Get coordinates of all non-zero pixels
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return img_bgr, 0.0

        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct OpenCV angle convention
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # If slight angle detected (between 0.5 and 15 degrees), rotate
        if 0.5 < abs(angle) < 15.0:
            (h, w) = img_bgr.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                img_bgr, M, (w, h), 
                flags=cv2.INTER_CUBIC, 
                borderMode=cv2.BORDER_CONSTANT, 
                borderValue=(255, 255, 255)
            )
            return rotated, angle

        return img_bgr, 0.0

    def enhance_contrast(self, img_bgr: np.ndarray) -> np.ndarray:
        """Enhance contrast to separate stamped text and remove photocopy noise."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)

        # Subtle bilateral filter to smooth paper texture while preserving sharp text edges
        filtered = cv2.bilateralFilter(equalized, d=5, sigmaColor=50, sigmaSpace=50)
        return cv2.cvtColor(filtered, cv2.COLOR_GRAY2BGR)

    def process(self, pdf_path: str | Path, page_index: int = 0) -> dict:
        """Complete Stage 2 pipeline for a page."""
        pil_img = self.render_page(pdf_path, page_index)
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        deskewed_img, skew_angle = self.deskew_image(cv_img)
        enhanced_img = self.enhance_contrast(deskewed_img)
        clean_pil = Image.fromarray(cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2RGB))

        return {
            "page_index": page_index,
            "skew_angle": round(skew_angle, 2),
            "image_size": pil_img.size,
            "pil_image": clean_pil,
            "cv_image": enhanced_img
        }
