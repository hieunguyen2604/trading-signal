import pandas as pd
from datetime import datetime
from utils.indicators import calculate_ema, calculate_rsi, calculate_macd, calculate_volume_ratio, calculate_atr

class SignalEngine:
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
    def calculate_score(df_1m: pd.DataFrame, df_15m: pd.DataFrame = None, df_1h: pd.DataFrame = None, 
                        btc_trend_15m: str = "NEUTRAL", btc_trend_1h: str = "NEUTRAL",
                        liquidity_context: dict = None, liquidation_context: dict = None) -> dict:
        """Calculate strength with MTF, BTC Correlation, Order Flow, and Liquidation Magnets."""
        if len(df_1m) < 50:
            return None
            
        prices = df_1m['close'].astype(float)
        highs = df_1m['high'].astype(float)
        lows = df_1m['low'].astype(float)
        volumes = df_1m['volume'].astype(float)
        
        ema20 = calculate_ema(prices, 20).iloc[-1]
        ema50 = calculate_ema(prices, 50).iloc[-1]
        rsi = calculate_rsi(prices, 14).iloc[-1]
        macd_line, signal_line, _ = calculate_macd(prices)
        macd = macd_line.iloc[-1]
        macd_sig = signal_line.iloc[-1]
        vol_ratio = calculate_volume_ratio(volumes)
        
        # ATR Calibration
        atr_15m = 0
        if df_15m is not None and len(df_15m) >= 14:
            df_15m_prices = df_15m['close'].astype(float)
            df_15m_highs = df_15m['high'].astype(float)
            df_15m_lows = df_15m['low'].astype(float)
            atr_15m = calculate_atr(df_15m_highs, df_15m_lows, df_15m_prices, 14).iloc[-1]
            risk = 3.5 * atr_15m 
        else:
            atr_1m = calculate_atr(highs, lows, prices, 14).iloc[-1]
            risk = 7.0 * atr_1m

        # Momentum Base
        bull_score = 0
        bear_score = 0
        if ema20 > ema50: bull_score += 15
        if rsi > 50: bull_score += 15
        if macd > macd_sig: bull_score += 15
        if vol_ratio > 1.5: bull_score += 15
        if ema20 < ema50: bear_score += 15
        if rsi < 50: bear_score += 15
        if macd < macd_sig: bear_score += 15
        if vol_ratio > 1.5: bear_score += 15
        
        # MTF Trend
        trend_15m = SignalEngine.get_trend(df_15m)
        trend_1h = SignalEngine.get_trend(df_1h)
        if trend_15m == "UP": bull_score += 20
        if trend_1h == "UP": bull_score += 20
        if trend_15m == "DOWN": bear_score += 20
        if trend_1h == "DOWN": bear_score += 20
        
        # Order Flow Intelligence (Alpha v4.0)
        obi = 0
        if liquidity_context:
            obi = liquidity_context.get("obi", 0)
            if obi > 0.4: bull_score += 15
            elif obi < -0.4: bear_score += 15

        # Liquidation Magnets (Alpha v5.0)
        magnet_price = 0
        magnet_vol = 0
        magnet_side = "NONE"
        if liquidation_context:
            magnet_price = liquidation_context.get("magnet_price", 0)
            magnet_vol = liquidation_context.get("magnet_vol", 0)
            magnet_side = liquidation_context.get("magnet_side", "NONE")
            
            # Boost score based on magnet attraction
            # Magnet SELL (Long liquidations below) indicates potential trap or target dump
            # Magnet BUY (Short liquidations above) indicates potential breakout target
            if magnet_vol > 10000: # Significant liquidity zone
                current_price = float(prices.iloc[-1])
                if magnet_side == "BUY" and magnet_price > current_price:
                    bull_score += 10 # Price attracted to shorts above
                elif magnet_side == "SELL" and magnet_price < current_price:
                    bear_score += 10 # Price attracted to longs below

        # Final Signal
        if bull_score >= bear_score:
            winner_score = bull_score
            signal_text = "BUY" if winner_score >= 70 else "WATCH" if winner_score >= 40 else "SELL"
        else:
            winner_score = bear_score
            signal_text = "SELL" if winner_score >= 70 else "WATCH" if winner_score >= 40 else "BUY"

        # BTC Correlation
        market_sync = False
        if signal_text == "BUY" and btc_trend_15m == "UP":
            market_sync = True
        elif signal_text == "SELL" and btc_trend_15m == "DOWN":
            market_sync = True
            
        # Confidence
        if signal_text == "BUY":
            confidence = "STRONG BUY" if (winner_score >= 90 and market_sync) else "CONFIRMED" if winner_score >= 70 else "PROVISIONAL"
            if not market_sync and winner_score >= 70:
                confidence = "CONTRA-TREND"
        elif signal_text == "SELL":
            confidence = "STRONG SELL" if (winner_score >= 90 and market_sync) else "CONFIRMED" if winner_score >= 70 else "PROVISIONAL"
            if not market_sync and winner_score >= 70:
                confidence = "CONTRA-TREND"
        else:
            confidence = "PROVISIONAL"
        
        # Guidance
        entry_price = float(prices.iloc[-1])
        if signal_text == "BUY":
            stop_loss = entry_price - risk
            tp1 = entry_price + (2 * risk)
            tp2 = entry_price + (3 * risk)
        elif signal_text == "SELL":
            stop_loss = entry_price + risk
            tp1 = entry_price - (2 * risk)
            tp2 = entry_price - (3 * risk)
        else:
            stop_loss = tp1 = tp2 = 0
            
        return {
            "score": winner_score,
            "signal": signal_text,
            "confidence": confidence,
            "market_sync": market_sync,
            "btc_trend": btc_trend_15m,
            "trend_15m": trend_15m,
            "trend_1h": trend_1h,
            "obi": obi,
            "liq_magnet_price": magnet_price,
            "liq_vol": magnet_vol,
            "entryPrice": entry_price,
            "stopLoss": stop_loss,
            "takeProfit1": tp1,
            "takeProfit2": tp2,
            "riskReward": "1:2 / 1:3"
        }

    @classmethod
    def calculate_signal(cls, symbol: str, df_1m: pd.DataFrame, df_15m: pd.DataFrame, df_1h: pd.DataFrame, 
                         is_final: bool, btc_trend_15m: str = "NEUTRAL", btc_trend_1h: str = "NEUTRAL",
                         liquidity_context: dict = None, liquidation_context: dict = None):
        """Processes fresh data with full Alpha v5.0 Master Context."""
        result = cls.calculate_score(df_1m, df_15m, df_1h, btc_trend_15m, btc_trend_1h, liquidity_context, liquidation_context)
        if result:
            return {
                "symbol": symbol,
                "score": result["score"],
                "signal": result["signal"],
                "confidence": result["confidence"],
                "market_sync": result["market_sync"],
                "btc_trend": result["btc_trend"],
                "trend_15m": result["trend_15m"],
                "trend_1h": result["trend_1h"],
                "obi": result["obi"],
                "liq_magnet_price": result["liq_magnet_price"],
                "liq_vol": result["liq_vol"],
                "entryPrice": result["entryPrice"],
                "currentPrice": float(df_1m.iloc[-1]["close"]),
                "stopLoss": result["stopLoss"],
                "takeProfit1": result["takeProfit1"],
                "takeProfit2": result["takeProfit2"],
                "riskReward": result["riskReward"],
                "is_final": is_final,
                "updatedAt": datetime.now().isoformat()
            }
        return None
