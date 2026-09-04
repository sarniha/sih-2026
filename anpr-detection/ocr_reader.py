"""
ocr_reader.py — OCR wrapper for Indian license plates

Engine: EasyOCR (off-the-shelf, English only)
  - Lazy-loads on first call to avoid startup cost at import time.
  - Applies pre-processing (grayscale, 2× upscale, Otsu threshold) before
    feeding to the engine — this significantly improves accuracy on small
    or blurry plate crops.

Indian plate format (validated): MH12AB1234
  State code (2 chars) + District (2 digits) + Series (1-2 chars) + Number (4 digits)

Post-hackathon: swap to PaddleOCR (better accuracy on tilted/worn plates) or
a custom CRNN trained on Indian plate fonts.
"""

import re
import cv2
import numpy as np
from typing import Optional, Tuple


# Regex for standard Indian plate: e.g. MH12AB1234 or DL3CAV0001
_INDIAN_PLATE_RE = re.compile(r'[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}')


class OCRReader:
    def __init__(self):
        self._reader = None   # lazy-loaded

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def read_plate(self, plate_img: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Run OCR on a plate crop.

        Args:
            plate_img: BGR crop of the license plate region.

        Returns:
            (raw_text, confidence)
              raw_text   — all text segments joined, uppercased (or None if blank)
              confidence — lowest per-segment confidence (most conservative estimate)
        """
        if plate_img is None or plate_img.size == 0:
            return None, 0.0

        preprocessed = self._preprocess(plate_img)
        reader       = self._get_reader()

        try:
            results = reader.readtext(preprocessed)
        except Exception as exc:
            print(f"[OCR] EasyOCR error: {exc}")
            return None, 0.0

        if not results:
            return None, 0.0

        # Join all segments (plates often split into 2 rows by OCR)
        raw_text   = " ".join(r[1] for r in results).upper().strip()
        confidence = min(r[2] for r in results)  # conservative: take lowest

        return raw_text, round(confidence, 4)

    def clean_plate(self, raw_text: Optional[str]) -> Optional[str]:
        """
        Strip non-alphanumeric chars and attempt to match Indian plate format.

        Returns the matched plate string, or the stripped raw text if no
        valid pattern is found (allows partial plates to pass through).
        """
        if not raw_text:
            return None

        stripped = re.sub(r'[^A-Z0-9]', '', raw_text.upper())

        match = _INDIAN_PLATE_RE.search(stripped)
        if match:
            return match.group(0)

        # Return stripped anyway — a partial match is better than None for demo
        return stripped if stripped else None

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _get_reader(self):
        """Lazy-load EasyOCR reader (heavy first load, cached after)."""
        if self._reader is None:
            import easyocr
            print("[OCR] Loading EasyOCR model (first call, may take 30s)…")
            self._reader = easyocr.Reader(['en'], gpu=False)
            print("[OCR] ✅ EasyOCR ready")
        return self._reader

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """
        Pre-processing pipeline for better OCR accuracy on small plate crops:
          1. Convert to grayscale
          2. 2× upscale with bicubic interpolation
          3. Otsu binarization (handles varying lighting)

        Returns the processed image as a numpy array.
        """
        gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        upscale = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(upscale, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
