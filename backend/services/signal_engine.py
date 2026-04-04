import pandas as pd
import json
import os
from datetime import datetime
from utils.indicators import calculate_ema, calculate_rsi, calculate_macd, calculate_volume_ratio, calculate_atr
from services.market_sentiment_service import sentiment_service

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

class SignalEngine:
    ACTIVE_MODE = "AETHER"  # Pure Single-Mode Branding
    
    @classmethod
    def set_mode(cls, mode: str):
        """No-op as only SWING is supported."""
        pass

    @staticmethod
    def get_trend(df: pd.DataFrame) -> str:
        """Determines if the trend is UP or DOWN based on EMA 50."""
        if df is None or len(df) < 50:
            return "NEUTRAL"
        prices = df['close'].astype(float)
        ema50 = calculate_ema(prices, 50).iloc[-1]
        current_price = float(prices.iloc[-1])
        return "UP" if current_price > ema50 else "DOWN"


    @staticmethod
    def _calculate_swing_score(df_1h: pd.DataFrame, df_4h: pd.DataFrame = None, df_1d: pd.DataFrame = None, 
                              btc_trend_4h: str = "NEUTRAL", btc_trend_1d: str = "NEUTRAL",
                              liquidity_context: dict = None, liquidation_context: dict = None) -> dict:
        """Alpha v9.0 Swing Logic (1h base)."""
        if len(df_1h) < 50: return None
        prices, highs, lows = df_1h['close'].astype(float), df_1h['high'].astype(float), df_1h['low'].astype(float)
        ema20, ema50 = calculate_ema(prices, 20).iloc[-1], calculate_ema(prices, 50).iloc[-1]
        rsi = calculate_rsi(prices, 14).iloc[-1]
        macd_line, signal_line, _ = calculate_macd(prices)
        macd, macd_sig = macd_line.iloc[-1], signal_line.iloc[-1]
        atr_1h = calculate_atr(highs, lows, prices, 14).iloc[-1]
        vol_ratio = calculate_volume_ratio(df_1h['volume'].astype(float), 20)
        
        # Alpha v12.1: Implement Volatility Floor (Min 2.5% for Swings)
        MIN_SWING_RISK_PCT = 0.025
        entry_price = float(prices.iloc[-1])
        floor_risk = entry_price * MIN_SWING_RISK_PCT
        risk = max(4.5 * atr_1h, floor_risk)
        
        bull_score, bear_score = 0, 0
        if ema20 > ema50: bull_score += 15
        if rsi > 50: bull_score += 15
        if macd > macd_sig: bull_score += 15
        if ema20 < ema50: bear_score += 15
        if rsi < 50: bear_score += 15
        if macd < macd_sig: bear_score += 15
        trend_4h, trend_1d = SignalEngine.get_trend(df_4h), SignalEngine.get_trend(df_1d)
        if trend_4h == "UP": bull_score += 20
        if trend_1d == "UP": bull_score += 20
        if trend_4h == "DOWN": bear_score += 20
        if trend_1d == "DOWN": bear_score += 20
        multiplier = sentiment_service.get_multiplier()
        bull_score, bear_score = int(bull_score * multiplier), int(bear_score * multiplier)
        
        # --- ELITE TACTICAL FILTERS (Alpha v12.6) ---
        # 1. RSI Safety Zone: Don't buy overbought (70), don't sell oversold (30)
        if rsi > 70: bull_score = int(bull_score * 0.5) 
        if rsi < 30: bear_score = int(bear_score * 0.5)
        
        # 2. Volume Breakout: Require 20% more volume than average
        if vol_ratio < 1.2:
            bull_score = int(bull_score * 0.8)
            bear_score = int(bear_score * 0.8)

        # 3. Decision Logic
        CONFIRMATION_THRESHOLD = 80
        
        if bull_score >= bear_score:
            winner_score, signal_text = bull_score, ("BUY" if bull_score >= CONFIRMATION_THRESHOLD else "WATCH" if bull_score >= 50 else "SELL")
        else:
            winner_score, signal_text = bear_score, ("SELL" if bear_score >= CONFIRMATION_THRESHOLD else "WATCH" if bear_score >= 50 else "BUY")
        market_sync = (signal_text == "BUY" and trend_4h == "UP") or (signal_text == "SELL" and trend_4h == "DOWN")
        entry_price = float(prices.iloc[-1])
        return {
            "score": winner_score, "signal": signal_text, "confidence": "CONFIRMED" if winner_score >= 80 else "PROVISIONAL",
            "market_sync": market_sync, "btc_trend": btc_trend_4h, "trend_1st": trend_4h, "trend_2nd": trend_1d,
            "entryPrice": entry_price, "stopLoss": entry_price - risk if signal_text == "BUY" else entry_price + risk,
            "takeProfit1": entry_price + (2.5*risk) if signal_text == "BUY" else entry_price - (2.5*risk),
            "takeProfit2": entry_price + (4.0*risk) if signal_text == "BUY" else entry_price - (4.0*risk),
            "riskReward": "1:2.5 (TACTICAL)", "sentiment_alignment": "BULLISH" if multiplier > 1 else "BEARISH" if multiplier < 1 else "NEUTRAL"
        }

    @classmethod
    async def calculate_signal(cls, symbol: str, df_1m: pd.DataFrame, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                         df_4h: pd.DataFrame, df_1d: pd.DataFrame, is_final: bool, 
                         btc_context: dict, liq_context: dict, liquid_context: dict):
        """Unified signal calculation with dynamic strategy mode and AI Intelligence."""
        # Always use Swing Logic for Alpha v12.5 Era
        result = cls._calculate_swing_score(df_1h, df_4h, df_1d, btc_context.get("btc_trend_4h"), btc_context.get("btc_trend_1d"), liq_context, liquid_context)
            
        if result:
            # Alpha v13.1: Async AI Tactical Reasoner (Only for CONFIRMED/STRONG)
            ai_insight = None
            if result["score"] >= 70:
                from services.ai_service import ai_service
                ai_insight = await ai_service.get_tactical_justification(
                    symbol, result["signal"], result["score"], result
                )

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
                "ai_insight": ai_insight, # Intelligence Era Field
                "is_final": is_final,
                "updatedAt": datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' # High precision
            }
        return None


