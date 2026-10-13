"""
AI Research Repository
Logs chatbot interactions, interpreted intents, research plans, and synthesized answers.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.ai_research import AIResearchLog


class AIResearchRepository:

    @staticmethod
    def log_query(
        db: Session,
        raw_query: str,
        symbol: Optional[str] = None,
        intent: Optional[str] = None,
        timeframe: Optional[str] = None,
        peers: Optional[List[str]] = None,
        research_plan: Optional[List[Dict[str, Any]]] = None,
        agent_type: Optional[str] = None,
        ai_response: str = "",
        context_data: Optional[Dict[str, Any]] = None,
        stock_id: Optional[int] = None,
    ) -> Optional[AIResearchLog]:
        if db is None:
            return None
        log_entry = AIResearchLog(
            stock_id=stock_id,
            raw_query=raw_query,
            interpreted_symbol=symbol,
            interpreted_intent=intent,
            timeframe=timeframe,
            peers=peers or [],
            research_plan=research_plan or [],
            agent_type=agent_type or "QuantIntelligence_Agent",
            ai_response=ai_response,
            context_data=context_data or {},
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def get_recent_logs(db: Session, limit: int = 20) -> List[AIResearchLog]:
        if db is None:
            return []
        stmt = select(AIResearchLog).order_by(AIResearchLog.created_at.desc()).limit(limit)
        return list(db.scalars(stmt).all())
