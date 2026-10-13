"""
Pydantic Schemas for Fundamentals, Analysis, Signals, and AI Research
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class FundamentalsResponse(BaseModel):
    id: int
    stock_id: int
    as_of_date: date
    revenue_growth_pct: Optional[float] = None
    profit_growth_pct: Optional[float] = None
    eps_trailing: Optional[float] = None
    eps_forward: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    promoter_holding_pct: Optional[float] = None
    institutional_holding_pct: Optional[float] = None
    fundamental_score: Optional[int] = None
    fundamental_rating: Optional[str] = None
    summary: Optional[str] = None
    key_highlights: Optional[List[str]] = None
    raw_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TradingSignalResponse(BaseModel):
    id: int
    stock_id: int
    analysis_id: Optional[int] = None
    signal_date: date
    signal_type: str
    confidence_score: Optional[int] = None
    technical_score: Optional[int] = None
    fundamental_score: Optional[int] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward_ratio: Optional[str] = None
    expected_time_horizon: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    reason_for_decision: Optional[str] = None
    ai_explanation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentResponse(BaseModel):
    id: int
    stock_id: int
    analysis_id: Optional[int] = None
    assessment_date: date
    risk_score: Optional[int] = None
    risk_category: Optional[str] = None
    annualized_volatility_pct: Optional[float] = None
    suggested_entry_price: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_target_price: Optional[float] = None
    risk_to_reward_ratio: Optional[str] = None
    recommended_shares: Optional[int] = None
    suggested_position_value: Optional[float] = None
    suggested_portfolio_pct: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIResearchResponse(BaseModel):
    id: int
    stock_id: Optional[int] = None
    raw_query: str
    interpreted_symbol: Optional[str] = None
    interpreted_intent: Optional[str] = None
    timeframe: Optional[str] = None
    peers: Optional[List[str]] = None
    research_plan: Optional[List[Dict[str, Any]]] = None
    agent_type: Optional[str] = None
    ai_response: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
