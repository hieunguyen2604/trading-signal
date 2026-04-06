import pandas as pd
import json
import os
from datetime import datetime
from utils.indicators import (
    calculate_ema, calculate_rsi, calculate_macd, 
    calculate_volume_ratio, calculate_atr, calculate_bollinger_bands
)
from services.market_sentiment_service import sentiment_service

class SignalEngine:
    """Core logic for analyzing market data and generating trading signals."""
    ACTIVE_MODE = "AETHER"
    
    @classmethod
    def set_mode(cls, mode: str):
        """Supported mode: AETHER."""
        pass

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculates Session VWAP (Volume Weighted Average Price)."""
        tp = (df['high'].astype(float) + df['low'].astype(float) + df['close'].astype(float)) / 3
        return (tp * df['volume'].astype(float)).cumsum() / df['volume'].astype(float).cumsum()

    @staticmethod
    def detect_rsi_divergence(prices: pd.Series, rsi: pd.Series, window: int = 20) -> str:
        """Detects Bullish/Bearish Divergence over a lookback window."""
        if len(prices) < window or len(rsi) < window:
            return "NONE"
            
        p_slice = prices.iloc[-window:].values
        r_slice = rsi.iloc[-window:].values
        
        # Simple Peak/Trough Detection
        p_max_idx = p_slice.argmax()
        p_min_idx = p_slice.argmin()
        
        # Check Bearish Divergence (Price HH, RSI LH)
        if p_max_idx < window - 5: # Peak must not be the very last candle
            if p_slice[-1] > p_slice[p_max_idx] and r_slice[-1] < r_slice[p_max_idx]:
                return "BEARISH"
                
        # Check Bullish Divergence (Price LL, RSI HL)
        if p_min_idx < window - 5:
            if p_slice[-1] < p_slice[p_min_idx] and r_slice[-1] > r_slice[p_min_idx]:
                return "BULLISH"
                
        return "NONE"

    @staticmethod
    def get_trend(df: pd.DataFrame) -> str:
        """Triple EMA Trend Detection (20, 50, 200)."""
        if df is None or len(df) < 200:
            return "NEUTRAL"
        
        prices = df['close'].astype(float)
        e20 = calculate_ema(prices, 20).iloc[-1]
        e50 = calculate_ema(prices, 50).iloc[-1]
        e200 = calculate_ema(prices, 200).iloc[-1]
        current_price = float(prices.iloc[-1])
        
        if current_price > e20 > e50 > e200:
            return "UP"
        elif current_price < e20 < e50 < e200:
            return "DOWN"
        return "NEUTRAL"

    @staticmethod
    def _calculate_swing_score(df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame = None, 
                               btc_trend_1h: str = "NEUTRAL", btc_trend_4h: str = "NEUTRAL",
                               liquidity_context: dict = None, liquidation_context: dict = None) -> dict:
        """Calculates internal confirmation score based on 15m/1h momentum and 1h/4h trend."""
        if len(df_1h) < 200 or len(df_15m) < 100: return None
        
        # 1H Primary Indicators
        prices_1h = df_1h['close'].astype(float)
        highs_1h, lows_1h = df_1h['high'].astype(float), df_1h['low'].astype(float)
        current_price = float(prices_1h.iloc[-1])
        
        e20_1h = calculate_ema(prices_1h, 20).iloc[-1]
        e50_1h = calculate_ema(prices_1h, 50).iloc[-1]
        e200_1h = calculate_ema(prices_1h, 200).iloc[-1]
        rsi_1h = calculate_rsi(prices_1h, 14).iloc[-1]
        macd_line, signal_line, _ = calculate_macd(prices_1h)
        macd, macd_sig = macd_line.iloc[-1], signal_line.iloc[-1]
        atr = calculate_atr(highs_1h, lows_1h, prices_1h, 14).iloc[-1]
        vol_ratio = calculate_volume_ratio(df_1h['volume'].astype(float), 20)
        upper, mid, lower = calculate_bollinger_bands(prices_1h)
        upper_last, Lower_last = upper.iloc[-1], lower.iloc[-1]
        vwap_1h = SignalEngine.calculate_vwap(df_1h).iloc[-1]
        div_1h = SignalEngine.detect_rsi_divergence(prices_1h, calculate_rsi(prices_1h, 14))

        # 15M Immediate Momentum
        prices_15m = df_15m['close'].astype(float)
        rsi_15m = calculate_rsi(prices_15m, 14).iloc[-1]
        e20_15m = calculate_ema(prices_15m, 20).iloc[-1]
        e50_15m = calculate_ema(prices_15m, 50).iloc[-1]
        vwap_15m = SignalEngine.calculate_vwap(df_15m).iloc[-1]
        div_15m = SignalEngine.detect_rsi_divergence(prices_15m, calculate_rsi(prices_15m, 14))
        
        bull_score, bear_score = 0, 0
        
        # 1H EMA Alignment (Base Points)
        if e20_1h > e50_1h: bull_score += 15
        if e50_1h > e200_1h: bull_score += 10
        if e20_1h < e50_1h: bear_score += 15
        if e50_1h < e200_1h: bear_score += 10

        # 15M Momentum (Sensitive Points)
        if e20_15m > e50_15m: bull_score += 10
        if rsi_15m > 55: bull_score += 10
        if e20_15m < e50_15m: bear_score += 10
        if rsi_15m < 45: bear_score += 10
        
        # Momentum Indicators (1H)
        if rsi_1h > 50: bull_score += 5
        if rsi_1h < 50: bear_score += 5
        if macd > macd_sig: bull_score += 5
        if macd < macd_sig: bear_score += 5
        
        # Sensitive Trend Synchronization (1H / 4H instead of 4H / 1D)
        trend_1h, trend_4h = SignalEngine.get_trend(df_1h), SignalEngine.get_trend(df_4h)
        if trend_1h == "UP": bull_score += 25  # Increased weight for 1H
        if trend_4h == "UP": bull_score += 15
        if trend_1h == "DOWN": bear_score += 25
        if trend_4h == "DOWN": bear_score += 15
        
        # Market Intelligence
        if liquidity_context:
            obi = liquidity_context.get("obi", 0)
            if obi > 0.3: bull_score += 10
            elif obi < -0.3: bear_score += 10
            
        if liquidation_context:
            magnet_side = liquidation_context.get("magnet_side", "NONE")
            magnet_vol = liquidation_context.get("magnet_vol", 0)
            if magnet_vol > 50000:
                if magnet_side == "BUY": bear_score += 10
                elif magnet_side == "SELL": bull_score += 10
        
        # Institutional Indicators (Alpha v14.8 Upgrade)
        # 1. VWAP Alignment
        if current_price < vwap_1h: bull_score += 10 # Value Buy
        if current_price > vwap_1h: bear_score += 10 # Value Sell
        
        # 2. RSI Divergence (High Priority Reversal Trigger)
        if div_1h == "BULLISH" or div_15m == "BULLISH":
            bull_score += 30
            print(f"[{datetime.now()}] BULLISH DIVERGENCE DETECTED (1H/15M)")
        if div_1h == "BEARISH" or div_15m == "BEARISH":
            bear_score += 30
            print(f"[{datetime.now()}] BEARISH DIVERGENCE DETECTED (1H/15M)")
        
        # Sentiment Integration
        multiplier = sentiment_service.get_multiplier()
        bull_score, bear_score = int(bull_score * multiplier), int(bear_score * multiplier)
        
        # Overextension Filters
        if current_price > upper_last: bull_score = int(bull_score * 0.4)
        if current_price < Lower_last: bear_score = int(bear_score * 0.4)
        if vol_ratio < 1.05: # Lowered volume requirement for sensitivity
            bull_score = int(bull_score * 0.9)
            bear_score = int(bear_score * 0.9)

        # Decision Thresholds (Alpha v14.5: Lowered for sensitivity)
        CONFIRMATION_THRESHOLD = 65
        STRONG_THRESHOLD = 85
        
        if bull_score >= bear_score:
            winner_score = bull_score
            signal_text = "BUY" if bull_score >= CONFIRMATION_THRESHOLD else "WATCH" if bull_score >= 45 else "SELL"
        else:
            winner_score = bear_score
            signal_text = "SELL" if bear_score >= CONFIRMATION_THRESHOLD else "WATCH" if bear_score >= 45 else "BUY"
            
        risk = max(2.0 * atr, current_price * 0.01)
        
        return {
            "score": winner_score, 
            "signal": signal_text, 
            "confidence": "STRONG" if winner_score >= STRONG_THRESHOLD else "CONFIRMED" if winner_score >= CONFIRMATION_THRESHOLD else "PROVISIONAL",
            "market_sync": (signal_text == "BUY" and trend_1h == "UP") or (signal_text == "SELL" and trend_1h == "DOWN"),
            "btc_trend": btc_trend_1h, 
            "trend_1st": trend_1h, 
            "trend_2nd": trend_4h,
            "entryPrice": current_price, 
            "stopLoss": current_price - risk if signal_text == "BUY" else current_price + risk,
            "takeProfit1": current_price + (1.0*risk) if signal_text == "BUY" else current_price - (1.0*risk),
            "takeProfit2": current_price + (2.0*risk) if signal_text == "BUY" else current_price - (2.0*risk),
            "riskReward": "Dynamic", 
            "sentiment_alignment": "BULLISH" if multiplier > 1 else "BEARISH" if multiplier < 1 else "NEUTRAL",
            "atr": atr
        }

    @classmethod
    async def calculate_signal(cls, symbol: str, df_1m: pd.DataFrame, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                         df_4h: pd.DataFrame, df_1d: pd.DataFrame, is_final: bool, 
                         btc_context: dict, liq_context: dict, liquid_context: dict):
        """Unified signal calculation with context awareness and AI justification."""
        result = cls._calculate_swing_score(df_15m, df_1h, df_4h, btc_context.get("btc_trend_1h"), btc_context.get("btc_trend_4h"), liquid_context, liq_context)
            
        if result:
            ai_insight = None
            # [Gemini Quota Bypassed] Disabled for Alpha v14.5.2 Sensitivity Upgrade
            # if result["score"] >= 65:
            #     from services.ai_service import ai_service
            #     ai_insight = await ai_service.get_tactical_justification(
            #         symbol, result["signal"], result["score"], result
            #     )

            return {
                "symbol": symbol,
                "strategy": cls.ACTIVE_MODE,
                "score": result["score"],
                "signal": result["signal"],
                "confidence": result["confidence"],
                "market_sync": result["market_sync"],
                "btc_trend": result["btc_trend"],
                "trend_1st": result["trend_1st"],
                "trend_2nd": result["trend_2nd"],
                "entryPrice": result["entryPrice"],
                "currentPrice": float(df_1m.iloc[-1]["close"]),
                "stopLoss": result["stopLoss"],
                "takeProfit1": result["takeProfit1"],
                "takeProfit2": result.get("takeProfit2", 0),
                "riskReward": result["riskReward"],
                "sentiment_alignment": result["sentiment_alignment"],
                "ai_insight": ai_insight,
                "is_final": is_final,
                "updatedAt": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
        return None


