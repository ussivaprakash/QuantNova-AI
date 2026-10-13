"""
Analysis Snapshot Model
Records historical quantitative analysis executions, ML predictions, and feature scores.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AnalysisSnapshot(Base):
    __tablename__ = "analysis_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    period = Column(String(10), nullable=False, default="1y")

    latest_price = Column(Numeric(14, 4), nullable=False)
    trend_classification = Column(String(50), nullable=True)
    trend_score = Column(Integer, nullable=True)
    ma20_slope = Column(Numeric(8, 2), nullable=True)

    # Machine Learning Forecasts
    ml_bullish_prob_pct = Column(Numeric(6, 2), nullable=True)
    ml_prediction = Column(String(20), nullable=True)
    ml_confidence = Column(String(20), nullable=True)
    ml_metrics = Column(JSON, nullable=True, default=dict)
    feature_importances = Column(JSON, nullable=True, default=list)

    # Indicator & Backtesting Summaries
    indicator_summary = Column(JSON, nullable=True, default=dict)
    backtest_summary = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="analysis_snapshots")
    trading_signals = relationship("TradingSignal", back_populates="analysis_snapshot")
    risk_assessments = relationship("RiskAssessment", back_populates="analysis_snapshot")

    __table_args__ = (
        Index("idx_analysis_stock_date_desc", "stock_id", analysis_date.desc()),
    )

    def __repr__(self):
        return f"<AnalysisSnapshot(stock_id={self.stock_id}, trend='{self.trend_classification}', ml='{self.ml_prediction}')>"
