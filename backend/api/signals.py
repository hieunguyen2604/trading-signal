from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
import asyncio
import json
from datetime import datetime
from services.websocket_manager import manager

router = APIRouter()

# WebSocket /ws/prices: Tick-by-tick instant price board
@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """Handle instant tick-by-tick price streaming."""
    await manager.connect(websocket, "prices")
    try:
        # Keep connection open
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "prices")
    except Exception as e:
        print(f"Price WebSocket Error: {e}")
        manager.disconnect(websocket, "prices")

# WebSocket /ws/signals: Signal calculations (provisional + 1m confirm)
@router.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """Handle 1s provisional / 1m finalized signal streaming."""
    await manager.connect(websocket, "signals")
    try:
        # Keep connection open
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "signals")
    except Exception as e:
        print(f"Signal WebSocket Error: {e}")
        manager.disconnect(websocket, "signals")

@router.get("/status")
async def get_status():
    """System health status."""
    return {
        "status": "online",
        "market": "LIVE",
        "active_clients": {
            "prices": len(manager.active_connections["prices"]),
            "signals": len(manager.active_connections["signals"])
        },
        "timestamp": datetime.now().isoformat()
    }
