from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Set
import asyncio
import json
from datetime import datetime
from services.signal_engine import SignalEngine
from services.websocket_manager import manager
from services.candle_stream_service import candle_service

router = APIRouter()

# WebSocket /ws/prices: Tick-by-step instant price board
@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """Handle instant tick-by-step price streaming."""
    await manager.connect(websocket, "prices")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "prices")
    except Exception as e:
        print(f"Price WebSocket Error: {e}")
        manager.disconnect(websocket, "prices")

# WebSocket /ws/signals: Signal calculations
@router.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """Handle signal streaming with initial state handshake."""
    await manager.connect(websocket, "signals")
    
    # Initial State Handshake
    from services.market_sentiment_service import sentiment_service
    from services.edge_service import edge_service
    
    initial_state = {
        "type": "WELCOME_UPDATE",
        "mode": "AETHER",
        "sentiment": sentiment_service.get_sentiment(),
        "stats": edge_service.get_stats()
    }
    await manager.send_personal_message(json.dumps(initial_state), websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "signals")
    except Exception as e:
        print(f"Signal WebSocket Error: {e}")
        manager.disconnect(websocket, "signals")

@router.get("/status")
async def get_status():
    return {
        "status": "online",
        "mode": "AETHER"
    }

@router.get("/mode")
async def get_mode():
    return {"mode": "AETHER"}

@router.get("/portfolio/stats")
async def get_portfolio_stats():
    """Get current account exposure and risk stats."""
    from services.trade_manager import trade_manager
    return trade_manager.get_exposure_stats()

@router.get("/edge/history")
async def get_edge_history():
    """Get cumulative PnL history for the performance chart."""
    from services.edge_service import edge_service
    return edge_service.get_equity_data()

@router.get("/edge/export")
async def export_trade_log():
    """Export the total trade history as a CSV file."""
    from services.edge_service import edge_service
    from fastapi.responses import Response
    
    csv_data = edge_service.get_trade_log_csv()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=aether_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/active")
async def get_active_signals():
    """Get the current top prioritized tactical signals from cache."""
    from services.trade_manager import trade_manager
    return trade_manager.get_latest_signals()

@router.get("/trades/active")
async def get_active_positions():
    """Get all current live positions from the trade manager."""
    from services.trade_manager import trade_manager
    return list(trade_manager.active_trades.values())

