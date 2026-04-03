from typing import Dict, List
from datetime import datetime
from schemas.signal import TradingSignal

class SignalCache:
    """In-memory cache for trading signals, designed to be Redis-ready."""
    def __init__(self):
        self._signals: Dict[str, TradingSignal] = {}
        self._last_updated = datetime.now()

    def update_signal(self, symbol: str, signal: TradingSignal):
        self._signals[symbol] = signal
        self._last_updated = datetime.now()

    def get_top_signals(self, limit: int = 5) -> List[TradingSignal]:
        # Sort by score descending
        sorted_signals = sorted(
            self._signals.values(),
            key=lambda x: x.score,
            reverse=True
        )
        return sorted_signals[:limit]

    def get_last_updated(self) -> datetime:
        return self._last_updated

# Global singleton
cache = SignalCache()
