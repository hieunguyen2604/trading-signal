import json
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional
from services.websocket_manager import manager
from services.edge_service import edge_service

TRADES_PATH = os.path.join(os.path.dirname(__file__), "..", "active_trades.json")

class TradeManager:
    """Manages lifecycles of active trades (Break-even, Trailing Stop, PnL) and archives to EdgeService."""
    def __init__(self, account_balance: float = 1000.0, risk_percent: float = 0.01):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.active_trades: Dict[str, dict] = {}
        self.latest_signals: Dict[str, dict] = {} # Alpha v12.4: Cache for immediate UI retrieval
        self.load_trades()


    def load_trades(self):
        """Recover active trades from disk."""
        if os.path.exists(TRADES_PATH):
            try:
                with open(TRADES_PATH, "r") as f:
                    self.active_trades = json.load(f)
                    print(f"Trade Recovery System: Loaded {len(self.active_trades)} active positions.")
            except Exception as e:
                print(f"Failed to load active trades: {e}")

    def save_trades(self):
        """Persist current active trades to disk."""
        try:
            with open(TRADES_PATH, "w") as f:
                json.dump(self.active_trades, f)
        except Exception as e:
            print(f"Failed to save active trades: {e}")

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
            edge_service.record_trade(symbol, trade["signal"], entry, current_price, pnl_pct, status_label)
            print(f"[{symbol}] Trade Archived: {status_label} ({pnl_pct}%)")
            del self.active_trades[symbol]
        
        self.save_trades()
        return trade

    async def activate_signal(self, symbol: str, signal_data: dict):
        """Turn a CONFIRMED or STRONG signal into an ACTIVE trade."""
        if symbol in self.active_trades and self.active_trades[symbol]["tradeStatus"] not in ["STOP_LOSS_HIT", "TP2_HIT"]:
            return # Already active
            
        if signal_data["confidence"] in ["CONFIRMED", "STRONG BUY", "STRONG SELL"]:
            entry = signal_data["entryPrice"]
            stop = signal_data["stopLoss"]
            
            position_size = self.calculate_position_size(entry, stop)
            
            new_trade = {
                **signal_data,
                "positionSize": position_size,
                "riskAmount": self.account_balance * self.risk_percent,
                "tradeStatus": "ACTIVE",
                "pnlPct": 0.0,
                "currentPrice": entry
            }
            
            self.active_trades[symbol] = new_trade
            print(f"[{symbol}] Trade Activated @ {entry} (Size: {position_size})")
            self.save_trades()
            
            # 11.5: Immediate broadcast so UI reflects the new trade instantly
            await manager.broadcast(json.dumps({
                "type": "TRADE_UPDATE",
                **new_trade
            }), "signals")
            
            # 12.1: Sync Portfolio Stats
            await self.broadcast_portfolio_stats()

    def clear_all_signals(self):
        """Purges the signal cache during strategy mode transitions."""
        self.latest_signals.clear()
        print("TradeManager: Signal cache purged for tactical realignment.")

    def update_latest_signal(self, symbol: str, signal_data: dict):
        """Updates the persistent cache of the latest signals."""
        self.latest_signals[symbol] = signal_data

    def get_latest_signals(self) -> List[dict]:
        """Returns the current prioritized list of opportunistic signals."""
        return list(self.latest_signals.values())


    async def broadcast_portfolio_stats(self):
        """Calculates and broadcasts global risk metrics to all terminals."""
        stats = self.get_exposure_stats()
        await manager.broadcast(json.dumps({
            "type": "PORTFOLIO_SYNC",
            **stats
        }), "signals")

    def get_exposure_stats(self) -> dict:
        """Calculates total risk, directional bias, and asset concentration."""
        total_risk = 0.0
        buys = 0
        sells = 0
        symbols = []
        
        for symbol, trade in self.active_trades.items():
            total_risk += trade.get("riskAmount", 0)
            if trade["signal"] == "BUY": buys += 1
            else: sells += 1
            symbols.append(symbol)
            
        risk_percent = (total_risk / self.account_balance) * 100 if self.account_balance > 0 else 0
        
        bias = "NEUTRAL"
        if buys > sells + 2: bias = "HIGH LONG"
        elif sells > buys + 2: bias = "HIGH SHORT"
        elif buys > sells: bias = "LONG BIAS"
        elif sells > buys: bias = "SHORT BIAS"
        
        return {
            "totalRisk": round(total_risk, 2),
            "riskPercent": round(risk_percent, 2),
            "directionalBias": bias,
            "activePositions": len(self.active_trades),
            "symbols": symbols,
            "balance": self.account_balance
        }

# Global singleton
trade_manager = TradeManager()
