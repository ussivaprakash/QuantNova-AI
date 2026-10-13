"""
Trading Signals Model
Stores quantitative decision engine recommendations, stop losses, target prices, and AI explanations.
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
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(BigInteger, ForeignKey("analysis_snapshots.id", ondelete="SET NULL"), nullable=True, index=True)
    signal_date = Column(Date, nullable=False, index=True)

    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD / WAIT
    confidence_score = Column(Integer, nullable=True)
    technical_score = Column(Integer, nullable=True)
    fundamental_score = Column(Integer, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String(30), nullable=True)

    entry_price = Column(Numeric(14, 4), nullable=False)
    stop_loss = Column(Numeric(14, 4), nullable=False)
    target_price = Column(Numeric(14, 4), nullable=False)
    risk_reward_ratio = Column(String(20), nullable=True)
    expected_time_horizon = Column(String(100), nullable=True)

    pros = Column(JSON, nullable=True, default=list)
    cons = Column(JSON, nullable=True, default=list)
    risks = Column(JSON, nullable=True, default=list)
    reason_for_decision = Column(Text, nullable=True)
    ai_explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="trading_signals")
    analysis_snapshot = relationship("AnalysisSnapshot", back_populates="trading_signals")

    __table_args__ = (
        Index("idx_signals_stock_date_desc", "stock_id", signal_date.desc()),
        Index("idx_signals_type_date_desc", "signal_type", signal_date.desc()),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 100", name="chk_signal_confidence_range"),
    )

    def __repr__(self):
        return f"<TradingSignal(stock_id={self.stock_id}, signal='{self.signal_type}', target={self.target_price})>"
