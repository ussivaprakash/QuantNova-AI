"""
Pydantic Schemas for Historical Market Data (OHLCV)
"""

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MarketDataBase(BaseModel):
    trading_date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int


class MarketDataCreate(MarketDataBase):
    stock_id: int


class MarketDataResponse(MarketDataBase):
    id: int
    stock_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketDataBulkCreate(BaseModel):
    stock_id: int
    bars: List[MarketDataBase]
