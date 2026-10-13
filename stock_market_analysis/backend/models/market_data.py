"""
Historical Market Data Model (OHLCV)
Stores daily trading bars for equities. Optimized for millions of rows.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Date,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    trading_date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(14, 4), nullable=False)
    high = Column(Numeric(14, 4), nullable=False)
    low = Column(Numeric(14, 4), nullable=False)
    close = Column(Numeric(14, 4), nullable=False)
    adj_close = Column(Numeric(14, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="market_data")

    # Table Constraints & Composite Indexes
    __table_args__ = (
        UniqueConstraint("stock_id", "trading_date", name="uq_stock_trading_date"),
        Index("idx_market_data_stock_date_desc", "stock_id", trading_date.desc()),
        Index("idx_market_data_date_desc", trading_date.desc()),
    )

    def __repr__(self):
        return f"<MarketData(stock_id={self.stock_id}, date={self.trading_date}, close={self.close})>"
