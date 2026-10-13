"""
Analysis, Signal & Risk Repository
Persists pipeline execution results, ML predictions, signal logs, and risk sizing.
"""

from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.analysis import AnalysisSnapshot
from models.signals import TradingSignal
from models.risk import RiskAssessment


class AnalysisRepository:

    @staticmethod
    def create_snapshot(db: Session, stock_id: int, data: Dict[str, Any]) -> Optional[AnalysisSnapshot]:
        if db is None:
            return None
        snapshot = AnalysisSnapshot(
            stock_id=stock_id,
            period=data.get("period", "1y"),
            latest_price=data["latest_price"],
            trend_classification=data.get("trend_classification"),
            trend_score=data.get("trend_score"),
            ma20_slope=data.get("ma20_slope"),
            ml_bullish_prob_pct=data.get("ml_bullish_prob_pct"),
            ml_prediction=data.get("ml_prediction"),
            ml_confidence=data.get("ml_confidence"),
            ml_metrics=data.get("ml_metrics", {}),
            feature_importances=data.get("feature_importances", []),
            indicator_summary=data.get("indicator_summary", {}),
            backtest_summary=data.get("backtest_summary", {}),
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    @staticmethod
    def save_trading_signal(
        db: Session,
        stock_id: int,
        signal_data: Dict[str, Any],
        analysis_id: Optional[int] = None,
        signal_date: Optional[date] = None,
    ) -> Optional[TradingSignal]:
        if db is None:
            return None
        s_date = signal_date or date.today()
        signal = TradingSignal(
            stock_id=stock_id,
            analysis_id=analysis_id,
            signal_date=s_date,
            signal_type=signal_data.get("signal", "HOLD / WAIT"),
            confidence_score=signal_data.get("confidence_score"),
            technical_score=signal_data.get("technical_score"),
            fundamental_score=signal_data.get("fundamental_score"),
            risk_score=signal_data.get("risk_score"),
            risk_level=signal_data.get("risk_level"),
            entry_price=signal_data.get("entry_price", 0.0),
            stop_loss=signal_data.get("stop_loss", 0.0),
            target_price=signal_data.get("target_price", 0.0),
            risk_reward_ratio=signal_data.get("risk_reward_ratio"),
            expected_time_horizon=signal_data.get("expected_time_horizon"),
            pros=signal_data.get("pros", []),
            cons=signal_data.get("cons", []),
            risks=signal_data.get("risks", []),
            reason_for_decision=signal_data.get("reason_for_decision"),
            ai_explanation=signal_data.get("ai_explanation"),
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal

    @staticmethod
    def save_risk_assessment(
        db: Session,
        stock_id: int,
        risk_data: Dict[str, Any],
        analysis_id: Optional[int] = None,
        assessment_date: Optional[date] = None,
    ) -> Optional[RiskAssessment]:
        if db is None:
            return None
        a_date = assessment_date or date.today()
        risk = RiskAssessment(
            stock_id=stock_id,
            analysis_id=analysis_id,
            assessment_date=a_date,
            risk_score=risk_data.get("Risk Score"),
            risk_category=risk_data.get("Risk Category"),
            annualized_volatility_pct=risk_data.get("Annualized Volatility (%)"),
            suggested_entry_price=risk_data.get("Suggested Entry Price (₹)"),
            suggested_stop_loss=risk_data.get("Suggested Stop Loss (₹)"),
            suggested_target_price=risk_data.get("Suggested Target Price (₹)"),
            risk_to_reward_ratio=str(risk_data.get("Risk-to-Reward Ratio", "")),
            recommended_shares=risk_data.get("Recommended Shares"),
            suggested_position_value=risk_data.get("Suggested Position Value (₹)"),
            suggested_portfolio_pct=risk_data.get("Suggested Portfolio Size (%)"),
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return risk

    @staticmethod
    def get_latest_signals(
        db: Session,
        limit: int = 20,
        signal_type: Optional[str] = None,
    ) -> List[TradingSignal]:
        if db is None:
            return []
        stmt = select(TradingSignal)
        if signal_type:
            stmt = stmt.where(TradingSignal.signal_type.ilike(f"%{signal_type}%"))
        stmt = stmt.order_by(TradingSignal.created_at.desc()).limit(limit)
        return list(db.scalars(stmt).all())
