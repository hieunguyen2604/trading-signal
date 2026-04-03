import json
import asyncio
import websockets
from typing import List, Dict
import pandas as pd
ACTIVE_SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "linkusdt", "dotusdt", "avaxusdt"]
from services.websocket_manager import manager

class TradeStreamService:
    """Subscribes to @aggTrade streams for tick-by-tick price updates."""
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.base_url = "wss://fstream.binance.com/ws"
        self.is_running = False

    async def start(self):
        self.is_running = True
        streams = "/".join([f"{s}@aggTrade" for s in self.symbols])
        url = f"{self.base_url}/{streams}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Connected to Trade Stream: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self.handle_trade(data)
            except Exception as e:
                print(f"Trade Stream Error: {e}. Reconnecting in 2s...")
                await asyncio.sleep(2)

    async def handle_trade(self, data: dict):
        """Broadcast instant price updates and update trade lifecycle."""
        symbol = data['s']
        price = float(data['p'])
        timestamp = data['T']
        direction = "down" if data['m'] else "up"
        
        # Get OBI and Large Liq for Alpha v5.0
        from services.liquidity_service import liquidity_service
        from services.liquidation_service import liquidation_service
        obi = liquidity_service.get_liquidity_context(symbol)['obi']
        
        last_liq = liquidation_service.last_large_liq.get(symbol.lower())
        liq_side = "NONE"
        liq_vol = 0
        
        # Only broadcast if it happened within last 2 seconds
        if last_liq and (datetime.now() - last_liq['time']).total_seconds() < 2:
            liq_side = last_liq['side'] # BUY (Shorts liqd) or SELL (Longs liqd)
            liq_vol = last_liq['vol']

        payload = {
            "symbol": symbol,
            "price": price,
            "direction": direction,
            "timestamp": timestamp,
            "obi": obi,
            "liq_side": liq_side,
            "liq_val": liq_vol
        }
        
        # 1. Update Price Board Tickers
        await manager.broadcast(json.dumps(payload), "prices")
        
        # 2. Update Active Trade Lifecycle (Trailing Stops, PnL, BE)
        from services.trade_manager import trade_manager
        from services.candle_stream_service import candle_service
        
        # Get current ATR for the symbol if available
        atr = 0
        if symbol.lower() in candle_service.data_frames:
            df = candle_service.data_frames[symbol.lower()]
            if len(df) >= 14:
                from utils.indicators import calculate_atr
                atr_series = calculate_atr(df['high'].astype(float), df['low'].astype(float), df['close'].astype(float))
                atr = float(atr_series.iloc[-1])
                
        updated_trade = trade_manager.update_trade(symbol, price, atr)
        if updated_trade:
            # Broadcast updated trade state to signals channel
            await manager.broadcast(json.dumps({
                "type": "TRADE_UPDATE",
                "symbol": symbol,
                **updated_trade
            }), "signals")

    def stop(self):
        self.is_running = False

# Global singleton
trade_service = None
