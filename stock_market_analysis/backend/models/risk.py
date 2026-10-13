"""
Risk Assessment Model
Stores volatility metrics, ATR stop loss, and position sizing guidelines per equity.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Date,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(BigInteger, ForeignKey("analysis_snapshots.id", ondelete="SET NULL"), nullable=True, index=True)
    assessment_date = Column(Date, nullable=False, index=True)

    risk_score = Column(Integer, nullable=True)
    risk_category = Column(String(30), nullable=True)
    annualized_volatility_pct = Column(Numeric(8, 2), nullable=True)

    suggested_entry_price = Column(Numeric(14, 4), nullable=True)
    suggested_stop_loss = Column(Numeric(14, 4), nullable=True)
    suggested_target_price = Column(Numeric(14, 4), nullable=True)
    risk_to_reward_ratio = Column(String(20), nullable=True)

    recommended_shares = Column(Integer, nullable=True)
    suggested_position_value = Column(Numeric(14, 4), nullable=True)
    suggested_portfolio_pct = Column(Numeric(6, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="risk_assessments")
    analysis_snapshot = relationship("AnalysisSnapshot", back_populates="risk_assessments")

    __table_args__ = (
        Index("idx_risk_stock_date_desc", "stock_id", assessment_date.desc()),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_risk_score_range"),
    )

    def __repr__(self):
        return f"<RiskAssessment(stock_id={self.stock_id}, score={self.risk_score}, category='{self.risk_category}')>"
