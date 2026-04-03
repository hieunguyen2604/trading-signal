import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.signals import router as signals_router
from backend.services.trade_stream_service import TradeStreamService
from backend.services.candle_stream_service import candle_service
from backend.services.liquidity_service import liquidity_service
from backend.services.liquidation_service import liquidation_service
from backend.services.edge_service import edge_service
from backend.services.websocket_manager import manager

app = FastAPI(title="Crypto Trade Assistant v5.5 (Alpha)")

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SYMBOLS TO TRACK
TRACKED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "LINKUSDT", "DOTUSDT", "AVAXUSDT"]

# Initialize Services
trade_service = TradeStreamService(TRACKED_SYMBOLS)

@app.on_event("startup")
async def startup_event():
    # Start Ticker Stream
    asyncio.create_task(trade_service.start())
    # Start MTF Candle Stream
    asyncio.create_task(candle_service.start())
    # Start Order Flow Liquidity Stream
    asyncio.create_task(liquidity_service.start())
    # Start Liquidation Hunter Stream
    asyncio.create_task(liquidation_service.start())
    
    # Start Stats Broadcast Loop (Alpha v5.5)
    asyncio.create_task(broadcast_stats_loop())
    
    print("Professional Trade Assistant Alpha v5.5 Engine Started...")

async def broadcast_stats_loop():
    """Periodically broadcasts historical strategy performance to the UI."""
    while True:
        try:
            stats = edge_service.get_stats()
            await manager.broadcast(json.dumps({
                "type": "STATS_UPDATE",
                **stats
            }), "signals")
        except Exception as e:
            print(f"Stats Broadcast Error: {e}")
        await asyncio.sleep(5) # Every 5 seconds

@app.on_event("shutdown")
def shutdown_event():
    trade_service.stop()
    candle_service.stop()
    liquidity_service.stop()
    liquidation_service.stop()

# Include routes
app.include_router(signals_router, prefix="/api/signals", tags=["engine"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
