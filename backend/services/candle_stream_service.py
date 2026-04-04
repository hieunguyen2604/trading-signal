import json
import asyncio
import websockets
import pandas as pd
import requests
from typing import List, Dict, Tuple
from services.signal_engine import SignalEngine
from services.websocket_manager import manager

class CandleStreamService:
    """Subscribes to 1m, 15m, and 1h kline streams for MTF trend confirmation."""
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.intervals = ["1m", "15m", "1h", "4h", "1d"]
        self.base_url = "wss://fstream.binance.com/ws"
        self.rest_url = "https://fapi.binance.com/fapi/v1/klines"
        # data_frames keyed by (symbol, interval)
        self.data_frames: Dict[Tuple[str, str], pd.DataFrame] = {}
        self.is_running = False

    async def initialize_data(self):
        """Fetch historical klines for 1m, 15m, 1h, 4h, 1d for all symbols."""
        for symbol in self.symbols:
            for interval in self.intervals:
                params = {"symbol": symbol.upper(), "interval": interval, "limit": 200}
                try:
                    response = requests.get(self.rest_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        df = pd.DataFrame(data, columns=[
                            "open_time", "open", "high", "low", "close", "volume",
                            "close_time", "quote_asset_volume", "number_of_trades",
                            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                        ])
                        self.data_frames[(symbol, interval)] = df[["open_time", "open", "high", "low", "close", "volume"]]
                        print(f"Initialized {symbol} {interval}: {len(df)} rows")
                except Exception as e:
                    print(f"MTF Init Error {symbol} {interval}: {e}")

    async def start_standalone(self):
        """Starts the WebSocket stream without re-initializing historical data."""
        self.is_running = True
        
        # Subscribe to all intervals for each symbol
        streams = []
        for symbol in self.symbols:
            for interval in self.intervals:
                streams.append(f"{symbol}@kline_{interval}")
                
        url = f"{self.base_url}/{'/'.join(streams)}"
        
        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    print(f"Connected to MTF Candle Stream: {url}")
                    while self.is_running:
                        message = await ws.recv()
                        data = json.loads(message)
                        await self.handle_kline(data)
            except Exception as e:
                print(f"MTF Stream Error: {e}. Reconnecting in 2s...")
                await asyncio.sleep(2)

    async def start(self):
        """Standard start which includes data initialization."""
        await self.initialize_data()
        await self.start_standalone()

    async def handle_kline(self, data: dict):
        """Processes kline data, manages MTF frames, and triggers signal logic."""
        symbol = data['s'].lower()
        k = data['k']
        interval = k['i']
        new_row = {
            "open_time": k['t'],
            "open": k['o'],
            "high": k['h'],
            "low": k['l'],
            "close": k['c'],
            "volume": k['v']
        }
        is_final = k['x']
        
        key = (symbol, interval)
        if key in self.data_frames:
            df = self.data_frames[key]
            # Replace last row or append
            if not df.empty and df.iloc[-1]['open_time'] == k['t']:
                df.iloc[-1] = new_row
            else:
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                if len(df) > 200:
                    df = df.iloc[-200:]
            
            self.data_frames[key] = df
            
            # SYNCED STRATEGY TRIGGER (Alpha v10.0)
            mode = SignalEngine.ACTIVE_MODE
            
            # Trigger conditions:
            # - SCALP: Every 1m update
            # - AETHER: 1h update OR finalizing 15m candle
            should_trigger = (mode == "SCALP" and interval == "1m") or \
                             (mode == "AETHER" and (interval == "1h" or (interval == "15m" and is_final)))
            
            if should_trigger:
                # Prepare exhaustive context for the Engine
                df_1m = self.data_frames.get((symbol, "1m"))
                df_15m = self.data_frames.get((symbol, "15m"))
                df_1h = self.data_frames.get((symbol, "1h"))
                df_4h = self.data_frames.get((symbol, "4h"))
                df_1d = self.data_frames.get((symbol, "1d"))
                
                # BTC Multi-Timeframe Context
                btc_context = {
                    "btc_trend_15m": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "15m"))),
                    "btc_trend_1h": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "1h"))),
                    "btc_trend_4h": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "4h"))),
                    "btc_trend_1d": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "1d")))
                }
                
                # External Intelligence Context
                from services.liquidity_service import liquidity_service
                from services.liquidation_service import liquidation_service
                liq_context = liquidity_service.get_liquidity_context(symbol)
                liquid_context = liquidation_service.get_magnet_context(symbol)
                
                signal_data = await SignalEngine.calculate_signal(
                    symbol.upper(), df_1m, df_15m, df_1h, df_4h, df_1d, is_final,
                    btc_context, liq_context, liquid_context
                )

                
                if signal_data:
                    from services.trade_manager import trade_manager
                    from services.tactical_alert_service import alert_service
                    
                    # Alpha v12.4: Sync to persistent signal cache
                    trade_manager.update_latest_signal(symbol.upper(), signal_data)
                    await trade_manager.activate_signal(symbol.upper(), signal_data)

                    
                    # Alpha v12.0 Tactical Alerts (Filtered High-Confidence Signals)
                    alert_service.send_signal_alert(signal_data)
                    
                    await manager.broadcast(json.dumps({
                        "type": "SIGNAL_UPDATE",
                        **signal_data
                    }), "signals")

            # Alpha v6.0: Update Active Trades via TradeManager for every tick
            from services.trade_manager import trade_manager
            trade_update = trade_manager.update_trade(symbol, float(new_row["close"]), 0.001) # Using a default min ATR for now
            if trade_update:
                await manager.broadcast(json.dumps({
                    "type": "TRADE_UPDATE",
                    **trade_update
                }), "signals")

    async def recalculate_all(self):
        """Force immediate re-calculation for all symbols using current cache."""
        print(f"FORCING INSTANT RE-CALCULATION (Mode: {SignalEngine.ACTIVE_MODE})...")
        for symbol in self.symbols:
            df_1m = self.data_frames.get((symbol, "1m"))
            df_15m = self.data_frames.get((symbol, "15m"))
            df_1h = self.data_frames.get((symbol, "1h"))
            df_4h = self.data_frames.get((symbol, "4h"))
            df_1d = self.data_frames.get((symbol, "1d"))
            
            btc_context = {
                "btc_trend_15m": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "15m"))),
                "btc_trend_1h": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "1h"))),
                "btc_trend_4h": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "4h"))),
                "btc_trend_1d": SignalEngine.get_trend(self.data_frames.get(("btcusdt", "1d")))
            }
            
            from services.liquidity_service import liquidity_service
            from services.liquidation_service import liquidation_service
            liq_context = liquidity_service.get_liquidity_context(symbol)
            liquid_context = liquidation_service.get_magnet_context(symbol)
            
            signal_data = await SignalEngine.calculate_signal(
                symbol.upper(), df_1m, df_15m, df_1h, df_4h, df_1d, False,
                btc_context, liq_context, liquid_context
            )

            
            
            if signal_data:
                from services.trade_manager import trade_manager
                trade_manager.update_latest_signal(symbol.upper(), signal_data)
                
                await manager.broadcast(json.dumps({
                    "type": "SIGNAL_UPDATE",
                    **signal_data
                }), "signals")


    def stop(self):
        self.is_running = False

# Global singleton
TRACKED_SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "linkusdt", "dotusdt", "avaxusdt"]
candle_service = CandleStreamService(TRACKED_SYMBOLS)
