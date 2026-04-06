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
            # 14.1 Update: Ensure strategy column exists for mode-specific stats
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    strategy TEXT, -- SCALP/AETHER
                    entry_price REAL NOT NULL,
                    final_price REAL NOT NULL,
                    pnl_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_trade(self, symbol: str, signal: str, entry: float, final: float, pnl: float, status: str, strategy: str = "AETHER"):
        """Saves a completed trade to persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO historical_trades (symbol, signal, strategy, entry_price, final_price, pnl_pct, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (symbol, signal, strategy, entry, final, pnl, status))
            conn.commit()

    def get_stats(self) -> dict:
        """Calculates performance metrics filtered by active strategy mode."""
        from services.signal_engine import SignalEngine
        mode = SignalEngine.ACTIVE_MODE
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Filter by strategy column
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE status IN ('WIN', 'TP2_HIT') AND strategy = ?", (mode,))
            wins = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE strategy = ?", (mode,))
            total = cursor.fetchone()[0]
            
            # Fallback if no trades yet to populate the UI dashboard
            if total == 0:
                return {"totalTrades": 0, "winRate": 0, "totalPnlPct": 0, "trades24h": 0, "winRate24h": 0, "netPnL": 0}

            win_rate = (wins / total * 100) if total > 0 else 0
            
            cursor.execute("SELECT SUM(pnl_pct) FROM historical_trades WHERE strategy = ?", (mode,))
            total_pnl_pct = cursor.fetchone()[0] or 0
            
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE timestamp > ? AND strategy = ?", (yesterday, mode))
            trades_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM historical_trades WHERE timestamp > ? AND status IN ('WIN', 'TP2_HIT') AND strategy = ?", (yesterday, mode))
            wins_24h = cursor.fetchone()[0]
            win_rate_24h = (wins_24h / trades_24h * 100) if trades_24h > 0 else 0

            return {
                "totalTrades": total,
                "winRate": round(win_rate, 1),
                "totalPnlPct": round(total_pnl_pct, 2),
                "trades24h": trades_24h,
                "winRate24h": round(win_rate_24h, 1),
                "netPnL": round(total_pnl_pct * 10, 2)
            }


    def get_equity_data(self) -> List[dict]:
        """Returns a list of PnL snapshots for the Equity Curve chart."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, pnl_pct FROM historical_trades ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            
            equity = []
            cumulative_pnl = 0.0
            
            # Start with baseline
            equity.append({"time": "Start", "pnl": 0.0})
            
            for row in rows:
                cumulative_pnl += row[1]
                # Safe timestamp splitting for HH:MM:SS
                timestamp_str = row[0]
                time_label = timestamp_str.split(" ")[1] if " " in timestamp_str else timestamp_str
                
                equity.append({
                    "time": time_label,
                    "pnl": round(cumulative_pnl, 2)
                })
            
            return equity

    def get_trade_log_csv(self) -> str:
        """Generates a CSV string of the entire trade history for export."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Symbol", "Signal", "Entry", "Exit", "PnL%", "Status", "Timestamp"])
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM historical_trades ORDER BY timestamp DESC")
            writer.writerows(cursor.fetchall())
            
        return output.getvalue()


# Global singleton
edge_service = EdgeService()
