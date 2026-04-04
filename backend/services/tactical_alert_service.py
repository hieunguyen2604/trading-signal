import requests
import json
from datetime import datetime

# Placeholder Credentials (Updated with User Token & Chat ID)
TELEGRAM_BOT_TOKEN = "8057478097:AAELx1YWsbO9_EuvT-dbNUaSa7sdttLN2fI"
TELEGRAM_CHAT_ID = "5812737285"

class TacticalAlertService:
    """Tactical Alert Engine for pushing high-conviction signals to Telegram."""
    def __init__(self):
        self.last_alerts = {} # Track last alert sent per symbol to avoid spam

    def send_telegram_message(self, message: str):
        """Sends a raw text message to the specified Telegram chat."""
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID":
            print("[Alert System] Telegram Bot not configured. (Skipping Alert)")
            return

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[Alert System] Telegram Alert Sent Successfully.")
            else:
                print(f"[Alert System] Error Sending Telegram: {response.text}")
        except Exception as e:
            print(f"[Alert System] Telegram Exception: {e}")

    def send_signal_alert(self, signal_data: dict):
        """Filters and formats high-quality signals for Telegram."""
        symbol = signal_data["symbol"]
        score = signal_data["score"]
        signal_type = signal_data["signal"] # BUY or SELL
        market_sync = signal_data.get("market_sync", False)
        confidence = signal_data.get("confidence", "PROVISIONAL")
        
        # 1. ALPHA V12.0 ELITE FILTER (Only send if Score >= 82 AND Market Sync is confirmed)
        if score < 82 or not market_sync or confidence != "CONFIRMED":
            return

        # 2. ANTI-SPAM: Don't send more than one alert every 15 minutes for the SAME symbol/signal
        now = datetime.now()
        last_key = f"{symbol}_{signal_type}"
        if last_key in self.last_alerts:
            time_diff = (now - self.last_alerts[last_key]).total_seconds()
            if time_diff < 900: # 15-minute window
                return

        # 3. PREMIUM FORMATTING
        direction_emoji = "🚀 LONG" if signal_type == "BUY" else "📉 SHORT"
        header_emoji = "🏛️ *AETHER TACTICAL SIGNAL*"
        
        message = (
            f"{header_emoji}\n\n"
            f"💎 **{symbol}** | {direction_emoji}\n\n"
            f"🎯 **Entry**: {signal_data['entryPrice']}\n"
            f"🛡️ **Stop Loss**: {signal_data['stopLoss']}\n"
            f"📈 **Target 1**: {signal_data['takeProfit1']}\n"
            f"⚖️ **R/R Ratio**: {signal_data['riskReward']}\n\n"
            f"🚀 **Alpha Score**: {score}/100\n"
            f"🔗 **BTC Trend**: {signal_data['btc_trend']}\n"
            f"🕰️ {datetime.now().strftime('%H:%M:%S UTC')}"
        )

        # 4. DISPATCH
        self.send_telegram_message(message)
        self.last_alerts[last_key] = now

# Global singleton
alert_service = TacticalAlertService()
