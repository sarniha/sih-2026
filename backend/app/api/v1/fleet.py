from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.fleet import FleetSummaryResponse
from app.services.fleet_service import get_fleet_summary

router = APIRouter()


@router.get("/fleet/summary", response_model=FleetSummaryResponse)
def get_fleet_summary_endpoint(db: Session = Depends(get_db)):
    return get_fleet_summary(db)


@router.get("/fleet/cameras")
def get_fleet_cameras_endpoint(db: Session = Depends(get_db)):
    summary = get_fleet_summary(db)
    return {"total": summary.total_cameras, "cameras": summary.cameras}
