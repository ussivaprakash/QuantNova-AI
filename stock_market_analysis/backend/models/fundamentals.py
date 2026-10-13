"""
Fundamentals Model
Captures periodic financial health metrics, valuation ratios, and scoring.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Date,
    Numeric,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)

    # Growth & Returns
    revenue_growth_pct = Column(Numeric(8, 2), nullable=True)
    profit_growth_pct = Column(Numeric(8, 2), nullable=True)
    eps_trailing = Column(Numeric(10, 2), nullable=True)
    eps_forward = Column(Numeric(10, 2), nullable=True)

    # Valuations
    pe_ratio = Column(Numeric(10, 2), nullable=True)
    pb_ratio = Column(Numeric(10, 2), nullable=True)
    roe_pct = Column(Numeric(8, 2), nullable=True)
    roce_pct = Column(Numeric(8, 2), nullable=True)

    # Leverage & Cash Flow
    debt_to_equity = Column(Numeric(8, 2), nullable=True)
    free_cash_flow = Column(Numeric(18, 2), nullable=True)

    # Shareholding Structure
    promoter_holding_pct = Column(Numeric(6, 2), nullable=True)
    institutional_holding_pct = Column(Numeric(6, 2), nullable=True)

    # Composite Institutional Scoring
    fundamental_score = Column(Integer, nullable=True)
    fundamental_rating = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    key_highlights = Column(JSON, nullable=True, default=list)
    raw_metrics = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="fundamentals")

    __table_args__ = (
        UniqueConstraint("stock_id", "as_of_date", name="uq_stock_fundamental_date"),
        Index("idx_fundamentals_stock_date_desc", "stock_id", as_of_date.desc()),
        CheckConstraint("fundamental_score >= 0 AND fundamental_score <= 100", name="chk_fundamental_score_range"),
    )

    def __repr__(self):
        return f"<Fundamentals(stock_id={self.stock_id}, date={self.as_of_date}, score={self.fundamental_score})>"
