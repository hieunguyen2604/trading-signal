from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TradingSignal(BaseModel):
    symbol: str
    score: float
    signal: str  # BUY, WATCH, SELL
    price: float
    change_24h: Optional[float] = 0.0
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    volume_ratio: Optional[float] = None
    updatedAt: datetime

class SignalResponse(BaseModel):
    signals: List[TradingSignal]
    market_status: str
    last_updated: datetime
