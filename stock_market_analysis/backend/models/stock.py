"""
Stock Master Model
Stores unique NSE/BSE stock symbols, company profiles, and metadata.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(30), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    exchange = Column(String(10), nullable=False, default="NSE", index=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    isin = Column(String(20), unique=True, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    market_data = relationship("MarketData", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")
    fundamentals = relationship("Fundamentals", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")
    analysis_snapshots = relationship("AnalysisSnapshot", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")
    trading_signals = relationship("TradingSignal", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")
    risk_assessments = relationship("RiskAssessment", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")
    ai_research_logs = relationship("AIResearchLog", back_populates="stock", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', exchange='{self.exchange}', name='{self.company_name}')>"
