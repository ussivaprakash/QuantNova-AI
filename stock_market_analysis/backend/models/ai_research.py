"""
AI Research Log Model
Tracks natural language questions, parsed intent, research execution plans, and AI intelligence responses.
"""

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AIResearchLog(Base):
    __tablename__ = "ai_research_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="SET NULL"), nullable=True, index=True)

    raw_query = Column(Text, nullable=False)
    interpreted_symbol = Column(String(30), nullable=True)
    interpreted_intent = Column(String(100), nullable=True)
    timeframe = Column(String(50), nullable=True)

    peers = Column(JSON, nullable=True, default=list)
    research_plan = Column(JSON, nullable=True, default=list)
    agent_type = Column(String(50), nullable=True)
    ai_response = Column(Text, nullable=False)
    context_data = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    stock = relationship("Stock", back_populates="ai_research_logs")

    __table_args__ = (
        Index("idx_ai_research_stock_desc", "stock_id", created_at.desc()),
        Index("idx_ai_research_created_desc", created_at.desc()),
    )

    def __repr__(self):
        return f"<AIResearchLog(id={self.id}, symbol='{self.interpreted_symbol}', agent='{self.agent_type}')>"
