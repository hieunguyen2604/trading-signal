import json
import asyncio
import websockets
from typing import List, Dict, Tuple

class LiquidityService:
    """Subscribes to depth10@100ms streams for all symbols to calculate OBI and detect walls."""
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.base_url = "wss://fstream.binance.com/ws"
        self.is_running = False
        self.order_book_data: Dict[str, dict] = {} # {symbol: {"obi": 0.5, "wall_price": 65000, "wall_side": "ASK"}}

    async def start(self):
        self.is_running = True
        
        # Subscribe to depth10@100ms for each symbol
        streams = [f"{symbol}@depth10@100ms" for symbol in self.symbols]
        url = f"{self.base_url}/{'/'.join(streams)}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Connected to Liquidity Depth Stream: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        self.handle_depth(data)
            except Exception as e:
                print(f"Liquidity Stream Error: {e}. Reconnecting in 2s...")
                await asyncio.sleep(2)

    def handle_depth(self, data: dict):
        """Calculates OBI and identifies the largest wall in the top 10."""
        symbol = data['s'].lower()
        bids = data['b']
        asks = data['a']

        # Total Volume at top 10
        total_bid_vol = sum(float(b[1]) for b in bids)
        total_ask_vol = sum(float(a[1]) for a in asks)
        
        # OBI Score: (Bids - Asks) / (Bids + Asks) -> -1.0 to 1.0
        total_vol = total_bid_vol + total_ask_vol
        obi = (total_bid_vol - total_ask_vol) / total_vol if total_vol > 0 else 0
        
        # Identify Nearest Major Wall
        # Wall = level with the highest volume in the top 10
        max_bid_vol = max(float(b[1]) for b in bids) if bids else 0
        max_ask_vol = max(float(a[1]) for a in asks) if asks else 0
        
        if max_bid_vol > max_ask_vol:
            wall_price = next(float(b[0]) for b in bids if float(b[1]) == max_bid_vol)
            wall_side = "BID"
            wall_vol = max_bid_vol
        else:
            wall_price = next(float(a[0]) for a in asks if float(a[1]) == max_ask_vol)
            wall_side = "ASK"
            wall_vol = max_ask_vol

        self.order_book_data[symbol] = {
            "obi": round(obi, 3),
            "wall_price": wall_price,
            "wall_side": wall_side,
            "wall_vol": wall_vol
        }

    def get_liquidity_context(self, symbol: str) -> dict:
        return self.order_book_data.get(symbol.lower(), {
            "obi": 0,
            "wall_price": 0,
            "wall_side": "NEUTRAL",
            "wall_vol": 0
        })

    def stop(self):
        self.is_running = False

# Global singleton
TRACKED_SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "linkusdt", "dotusdt", "avaxusdt"]
liquidity_service = LiquidityService(TRACKED_SYMBOLS)
