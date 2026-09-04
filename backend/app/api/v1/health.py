from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.fleet import SystemHealthResponse
from app.services.fleet_service import get_system_diagnostics

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "database": db_status,
    }


@router.get("/health/system", response_model=SystemHealthResponse)
def system_health_check(db: Session = Depends(get_db)):
    return get_system_diagnostics(db)