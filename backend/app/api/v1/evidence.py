import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.security import verify_service_token
from app.services.evidence_service import EVIDENCE_DIR, ensure_evidence_dir

router = APIRouter()


@router.post("/evidence/upload", dependencies=[Depends(verify_service_token)])
async def upload_evidence_endpoint(file: UploadFile = File(...)):
    """
    Receives an optical evidence frame from edge detection units, saves it to
    the static evidence repository, and returns its public URL path.
    """
    ensure_evidence_dir()

    # Generate a safe filename
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".mp4"]:
        ext = ".jpg"

    safe_name = f"evidence_{uuid.uuid4().hex[:12]}{ext}"
    dest_path = os.path.join(EVIDENCE_DIR, safe_name)

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save evidence file: {str(e)}")

    return {
        "filename": safe_name,
        "url": f"/static/evidence/{safe_name}",
        "size_bytes": os.path.getsize(dest_path),
    }
