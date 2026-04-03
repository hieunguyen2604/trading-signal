import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from backend.services.websocket_manager import manager
from backend.services.edge_service import edge_service

class TradeManager:
    """Manages lifecycles of active trades (Break-even, Trailing Stop, PnL) and archives to EdgeService."""
    def __init__(self, account_balance: float = 1000.0, risk_percent: float = 0.01):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.active_trades: Dict[str, dict] = {}

    def calculate_position_size(self, entry: float, stop: float) -> float:
        """Calculate coin units based on 1% risk."""
        risk_amount = self.account_balance * self.risk_percent
        risk_per_unit = abs(entry - stop)
        if risk_per_unit == 0: return 0
        return risk_amount / risk_per_unit

    def update_trade(self, symbol: str, current_price: float, atr: float):
        """Update trade status, break-even and trailing stop."""
        if symbol not in self.active_trades:
            return
            
        trade = self.active_trades[symbol]
        entry = trade["entryPrice"]
        stop = trade["stopLoss"]
        tp1 = trade["takeProfit1"]
        tp2 = trade["takeProfit2"]
        direction = 1 if trade["signal"] == "BUY" else -1
        
        # 1. Check Break-Even Logic
        if trade["tradeStatus"] == "ACTIVE":
            if (direction == 1 and current_price >= tp1) or (direction == -1 and current_price <= tp1):
                trade["stopLoss"] = entry
                trade["tradeStatus"] = "BREAK_EVEN"
                print(f"[{symbol}] Moved Stop Loss to Break-Even at {entry}")

        # 2. Check Trailing Stop (Only after TP1 hit or Break-Even)
        if trade["tradeStatus"] in ["BREAK_EVEN", "TP1_HIT"]:
            new_trailing = current_price - (direction * atr)
            if direction == 1:
                if new_trailing > trade["stopLoss"]:
                    trade["stopLoss"] = new_trailing
            else:
                if new_trailing < trade["stopLoss"]:
                    trade["stopLoss"] = new_trailing
                    
        # 3. Check Exit Conditions
        final_status = None
        if (direction == 1 and current_price <= trade["stopLoss"]) or (direction == -1 and current_price >= trade["stopLoss"]):
            final_status = "STOP_LOSS_HIT"
        elif (direction == 1 and current_price >= tp2) or (direction == -1 and current_price <= tp2):
            final_status = "TP2_HIT"

        # 4. Update PnL
        pnl_pct = ((current_price - entry) / entry) * 100 * direction
        trade["pnlPct"] = round(pnl_pct, 2)
        trade["currentPrice"] = current_price

        # 5. Handle Archive if closed
        if final_status:
            trade["tradeStatus"] = final_status
            status_label = "WIN" if pnl_pct > 0 else "LOSS"
            # Persistent Archive (Alpha v5.5)
            edge_service.record_trade(symbol, trade["signal"], entry, current_price, pnl_pct, status_label)
            print(f"[{symbol}] Trade Archived: {status_label} ({pnl_pct}%)")
            
            # Remove from active but keep for a few seconds so UI shows the hit
            del self.active_trades[symbol]
        
        return trade

    def activate_signal(self, symbol: str, signal_data: dict):
        """Turn a CONFIRMED or STRONG signal into an ACTIVE trade."""
        if symbol in self.active_trades and self.active_trades[symbol]["tradeStatus"] not in ["STOP_LOSS_HIT", "TP2_HIT"]:
            return # Already active
            
        if signal_data["confidence"] in ["CONFIRMED", "STRONG BUY", "STRONG SELL"]:
            entry = signal_data["entryPrice"]
            stop = signal_data["stopLoss"]
            
            position_size = self.calculate_position_size(entry, stop)
            
            self.active_trades[symbol] = {
                **signal_data,
                "positionSize": position_size,
                "riskAmount": self.account_balance * self.risk_percent,
                "tradeStatus": "ACTIVE",
                "pnlPct": 0.0,
                "currentPrice": entry
            }
            print(f"[{symbol}] Trade Activated @ {entry} (Size: {position_size})")

# Global singleton
trade_manager = TradeManager()
