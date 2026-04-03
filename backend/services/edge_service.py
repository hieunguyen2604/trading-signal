import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List

class EdgeService:
    """Manages persistent historical trade data using SQLite for strategy analytics."""
    def __init__(self, db_path: str = "backend/edge_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    final_price REAL NOT NULL,
                    pnl_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_trade(self, symbol: str, signal: str, entry: float, final: float, pnl: float, status: str):
        """Saves a completed trade to persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO historical_trades (symbol, signal, entry_price, final_price, pnl_pct, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (symbol, signal, entry, final, pnl, status))
            conn.commit()

    def get_stats(self) -> dict:
        """Calculates performance metrics (Win Rate, PnL, Profit Factor)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 1. Total Win Rate
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE status IN ('WIN', 'TP2_HIT')")
            wins = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM historical_trades")
            total = cursor.fetchone()[0]
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # 2. Net PnL (Virtual $ on $1000 base)
            cursor.execute("SELECT SUM(pnl_pct) FROM historical_trades")
            total_pnl_pct = cursor.fetchone()[0] or 0
            
            # 3. Last 24h Stats
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE timestamp > ?", (yesterday,))
            trades_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE timestamp > ? AND status IN ('WIN', 'TP2_HIT')", (yesterday,))
            wins_24h = cursor.fetchone()[0]
            win_rate_24h = (wins_24h / trades_24h * 100) if trades_24h > 0 else 0

            return {
                "totalTrades": total,
                "winRate": round(win_rate, 1),
                "totalPnlPct": round(total_pnl_pct, 2),
                "trades24h": trades_24h,
                "winRate24h": round(win_rate_24h, 1),
                "netPnL": round(total_pnl_pct * 10, 2) # Assuming $1000 base with 1% risk
            }

# Global singleton
edge_service = EdgeService()
