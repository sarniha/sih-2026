import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import events, fleet, health, incidents, traffic, websockets
from app.services.evidence_service import ensure_evidence_dir


def create_app() -> FastAPI:
    app = FastAPI(title="SIH26124 Backend")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    ensure_evidence_dir()
    static_dir = os.path.join(os.getcwd(), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(events.router, prefix="/api/v1", tags=["events"])
    app.include_router(incidents.router, prefix="/api/v1", tags=["incidents"])
    app.include_router(traffic.router, prefix="/api/v1", tags=["traffic"])
    app.include_router(websockets.router, prefix="/api/v1", tags=["websockets"])
    app.include_router(fleet.router, prefix="/api/v1", tags=["fleet"])

    return app


app = create_app()
