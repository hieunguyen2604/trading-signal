import pandas as pd
from datetime import datetime
from utils.indicators import calculate_ema, calculate_rsi, calculate_macd, calculate_volume_ratio
from schemas.signal import TradingSignal
from services.cache_manager import cache

class SignalService:
    @staticmethod
    def calculate_score(df: pd.DataFrame) -> dict:
        """Calculate technical indicators and ultimate signal score."""
        if len(df) < 50:  # Need at least 50 periods for EMA 50
            return None
            
        prices = df['close'].astype(float)
        volumes = df['volume'].astype(float)
        
        ema20 = calculate_ema(prices, 20).iloc[-1]
        ema50 = calculate_ema(prices, 50).iloc[-1]
        rsi = calculate_rsi(prices, 14).iloc[-1]
        macd_line, signal_line, _ = calculate_macd(prices)
        macd = macd_line.iloc[-1]
        macd_sig = signal_line.iloc[-1]
        vol_ratio = calculate_volume_ratio(volumes)
        
        score = 0
        # 1. EMA20 > EMA50 = +30
        if ema20 > ema50:
            score += 30
            
        # 2. RSI > 50 = +20
        if rsi > 50:
            score += 20
            
        # 3. MACD Bullish = +20
        if macd > macd_sig:
            score += 20
            
        # 4. Volume Ratio > 1.5 = +30
        if vol_ratio > 1.5:
            score += 30
            
        # Determine signal text
        if score >= 70:
            signal_text = "BUY"
        elif score >= 40:
            signal_text = "WATCH"
        else:
            signal_text = "SELL"
            
        return {
            "score": score,
            "signal": signal_text,
            "price": prices.iloc[-1],
            "ema20": ema20,
            "ema50": ema50,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_sig,
            "volume_ratio": vol_ratio,
            "updatedAt": datetime.now()
        }

    @classmethod
    def process_data(cls, symbol: str, df: pd.DataFrame):
        """Processes fresh market data and updates the cache."""
        result = cls.calculate_score(df)
        if result:
            signal = TradingSignal(
                symbol=symbol,
                **result
            )
            cache.update_signal(symbol, signal)
            return signal
        return None
