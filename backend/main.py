import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.signals import router as signals_router
from api.ai import router as ai_router
from services.trade_stream_service import TradeStreamService
from services.candle_stream_service import candle_service
from services.liquidity_service import liquidity_service
from services.liquidation_service import liquidation_service
from services.edge_service import edge_service
from services.market_sentiment_service import sentiment_service
from services.websocket_manager import manager

app = FastAPI(title="Crypto Trade Assistant (AETHER)")

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
    print("Starting Trade Assistant Engine...")
    await candle_service.initialize_data()
    
    # Start Background Streams
    asyncio.create_task(trade_service.start_standalone())
    asyncio.create_task(candle_service.start_standalone())
    asyncio.create_task(liquidity_service.start())
    asyncio.create_task(liquidation_service.start())
    asyncio.create_task(candle_service.recalculate_all())
    
    # Broadcast Loops
    asyncio.create_task(broadcast_stats_loop())
    asyncio.create_task(broadcast_sentiment_loop())
    
    print("Engine active and broadcasting.")

async def broadcast_sentiment_loop():
    """Periodically broadcasts Fear & Greed Index and News to the UI."""
    while True:
        try:
            await sentiment_service.fetch_fng()
            await sentiment_service.fetch_news()
            sentiment = sentiment_service.get_sentiment()
            await manager.broadcast(json.dumps({
                "type": "SENTIMENT_UPDATE",
                **sentiment
            }), "signals")
        except Exception as e:
            print(f"Sentiment Broadcast Error: {e}")
        await asyncio.sleep(300) # Every 5 minutes for news/f&g

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
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
