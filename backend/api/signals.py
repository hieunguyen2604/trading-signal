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
    
    # 11.5: Send Initial State Handshake
    from services.market_sentiment_service import sentiment_service
    from services.edge_service import edge_service
    
    initial_state = {
        "type": "WELCOME_UPDATE",
        "mode": SignalEngine.ACTIVE_MODE,
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
    """System health status."""
    return {
        "status": "online",
        "market": "LIVE",
        "mode": SignalEngine.ACTIVE_MODE,
        "active_clients": {
            "prices": len(manager.active_connections["prices"]),
            "signals": len(manager.active_connections["signals"])
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/mode")
async def get_mode():
    """Get current strategy mode."""
    return {"mode": SignalEngine.ACTIVE_MODE}

@router.post("/mode")
async def set_mode(mode: str):
    """Set strategy mode and broadcast change."""
    if mode in ["SCALP", "SWING"]:
        from services.trade_manager import trade_manager
        
        # Alpha v12.4: PURGE SIGNAL CACHE BEFORE SWITCH
        trade_manager.clear_all_signals()
        
        SignalEngine.set_mode(mode)

        # Broadcast strategy change event to all clients
        await manager.broadcast(json.dumps({
            "type": "STRATEGY_CHANGE",
            "mode": mode
        }), "signals")
        
        # Trigger immediate re-calculation for all symbols to provide "instant" feel
        await candle_service.recalculate_all()
        
        # Broadcast isolated stats for the new mode
        from services.edge_service import edge_service
        await manager.broadcast(json.dumps({
            "type": "STATS_UPDATE",
            **edge_service.get_stats()
        }), "signals")
        
        return {"status": "success", "mode": mode}

    return {"status": "error", "message": "Invalid mode"}

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

