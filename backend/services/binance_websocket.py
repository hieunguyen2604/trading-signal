import json
import asyncio
import websockets
import pandas as pd
import requests
from typing import List, Dict
from datetime import datetime
from backend.services.signal_calculator import SignalService

class BinanceWS:
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.base_url = "wss://stream.binance.com:9443/ws"
        self.rest_url = "https://api.binance.com/api/v3/klines"
        self.data_frames: Dict[str, pd.DataFrame] = {}
        self.is_running = False

    async def initialize_data(self):
        """Fetch historical 1m klines to bootstrap indicator calculation."""
        for symbol in self.symbols:
            params = {
                "symbol": symbol.upper(),
                "interval": "1m",
                "limit": 100
            }
            try:
                response = requests.get(self.rest_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    df = pd.DataFrame(data, columns=[
                        "open_time", "open", "high", "low", "close", "volume",
                        "close_time", "quote_asset_volume", "number_of_trades",
                        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                    ])
                    # Use only relevant columns
                    self.data_frames[symbol] = df[["open_time", "open", "high", "low", "close", "volume"]]
                    print(f"Initialized {symbol.upper()} with {len(df)} candles.")
            except Exception as e:
                print(f"Error initializing {symbol}: {e}")

    async def start(self, callback=None):
        """Start the WebSocket connection and stream data."""
        self.is_running = True
        await self.initialize_data()
        
        streams = "/".join([f"{s}@kline_1m" for s in self.symbols])
        url = f"{self.base_url}/{streams}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Connected to Binance WS: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self.handle_message(data, callback)
            except Exception as e:
                print(f"WS Connection error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def handle_message(self, data: dict, callback=None):
        """Handle incoming kline data."""
        symbol = data['s'].lower()
        kline = data['k']
        
        # Only process if the candle is closed or at regular intervals
        # For real-time updates, we update the last row in our DataFrame
        new_row = {
            "open_time": kline['t'],
            "open": kline['o'],
            "high": kline['h'],
            "low": kline['l'],
            "close": kline['c'],
            "volume": kline['v']
        }
        
        if symbol in self.data_frames:
            df = self.data_frames[symbol]
            # Replace last row if open_time matches, else append
            if df.iloc[-1]['open_time'] == kline['t']:
                df.iloc[-1] = new_row
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                # Keep last 200 for memory efficiency
                if len(df) > 200:
                    df = df.iloc[-200:]
            
            self.data_frames[symbol] = df
            
            # Recalculate signal
            signal = SignalService.process_data(symbol.upper(), df)
            if callback and signal:
                await callback(signal)

    def stop(self):
        self.is_running = False
