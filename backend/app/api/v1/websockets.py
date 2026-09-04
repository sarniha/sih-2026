from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect_event(websocket)
    try:
        while True:
            # Keep connection open and listen for ping/heartbeat from client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_event(websocket)
    except Exception:
        ws_manager.disconnect_event(websocket)


@router.websocket("/ws/incidents")
async def websocket_incidents_endpoint(websocket: WebSocket):
    await ws_manager.connect_incident(websocket)
    try:
        while True:
            # Keep connection open and listen for ping/heartbeat from client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_incident(websocket)
    except Exception:
        ws_manager.disconnect_incident(websocket)
