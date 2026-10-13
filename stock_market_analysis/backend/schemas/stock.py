"""
Pydantic Schemas for Stocks
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StockBase(BaseModel):
    symbol: str
    company_name: str
    exchange: str = "NSE"
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    is_active: bool = True


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    is_active: Optional[bool] = None


class StockResponse(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
