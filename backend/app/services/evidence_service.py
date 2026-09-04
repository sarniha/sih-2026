import os
import uuid
from typing import Optional


STATIC_DIR = os.path.join(os.getcwd(), "static")
EVIDENCE_DIR = os.path.join(STATIC_DIR, "evidence")


def ensure_evidence_dir():
    """Ensure the static/evidence directory exists."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)


def generate_sample_evidence(evidence_type: str = "image", object_id: Optional[str] = None) -> str:
    """
    Generates a sample evidence file on disk if it doesn't exist and returns its serveable URL.
    """
    ensure_evidence_dir()
    file_id = object_id or uuid.uuid4().hex[:8]
    filename = f"evidence_{evidence_type}_{file_id}.jpg"
    file_path = os.path.join(EVIDENCE_DIR, filename)

    if not os.path.exists(file_path):
        # Create a simple valid binary file (synthetic image header/content)
        content = f"Synthetic evidence placeholder for {evidence_type} ({file_id})".encode("utf-8")
        with open(file_path, "wb") as f:
            f.write(content)

    return f"/static/evidence/{filename}"
