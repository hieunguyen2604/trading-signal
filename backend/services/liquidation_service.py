import json
import asyncio
import websockets
from typing import List, Dict
from datetime import datetime, timedelta

class LiquidationService:
    """Subscribes to @forceOrder streams to detect clusters of liquidated positions (Magnets)."""
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.base_url = "wss://fstream.binance.com/ws"
        self.is_running = False
        # Liquidation cache: {symbol: [{"price": 65000, "vol": 1.5, "side": "SELL", "time": dt}]}
        self.liq_cache: Dict[str, List[dict]] = {s: [] for s in self.symbols}
        self.order_book_data: Dict[str, dict] = {} 
        self.last_large_liq: Dict[str, dict] = {} 
        self.max_age_minutes = 15

    async def start(self):
        self.is_running = True
        
        # Subscribe to forceOrder for all symbols
        streams = [f"{symbol}@forceOrder" for symbol in self.symbols]
        url = f"{self.base_url}/{'/'.join(streams)}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Connected to Liquidation Hunter Stream: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        self.handle_force_order(data)
            except Exception as e:
                print(f"Liquidation Stream Error: {e}. Reconnecting in 2s...")
                await asyncio.sleep(2)

    def handle_force_order(self, data: dict):
        """Stores liquidation event and updates clusters."""
        o = data['o']
        symbol = o['s'].lower()
        price = float(o['ap']) # Average price
        quantity = float(o['q'])
        side = o['S'] # SELL = Long Liquidation, BUY = Short Liquidation
        volume_usdt = price * quantity

        # Add to cache
        if symbol in self.liq_cache:
            self.liq_cache[symbol].append({
                "price": price,
                "vol": volume_usdt,
                "side": side,
                "time": datetime.now()
            })
            
            # Track Large Liquidation for Flash Alerts (Alpha v5.0)
            if volume_usdt > 5000: # Threshold for $5k+
                self.last_large_liq[symbol] = {
                    "side": side,
                    "vol": volume_usdt,
                    "time": datetime.now()
                }
                
            # Cleanup old events
            cutoff = datetime.now() - timedelta(minutes=self.max_age_minutes)
            self.liq_cache[symbol] = [e for e in self.liq_cache[symbol] if e['time'] > cutoff]

    def get_magnet_context(self, symbol: str) -> dict:
        """Finds the price cluster with the highest forced volume."""
        symbol = symbol.lower()
        events = self.liq_cache.get(symbol, [])
        if not events:
            return {"magnet_price": 0, "magnet_vol": 0, "magnet_side": "NONE"}

        # Cluster by rounding price (e.g., to nearest 0.1% or fixed step)
        # For simplicity, we just find the single largest event price in the 15m window
        max_event = max(events, key=lambda x: x['vol'])
        
        return {
            "magnet_price": max_event["price"],
            "magnet_vol": sum(e['vol'] for e in events), # Total hunt volume in 15m
            "magnet_side": max_event["side"] # SELL=Longs liquidated (Magnet below), BUY=Shorts liquidated (Magnet above)
        }

    def stop(self):
        self.is_running = False

# Global singleton
TRACKED_SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "linkusdt", "dotusdt", "avaxusdt"]
liquidation_service = LiquidationService(TRACKED_SYMBOLS)
