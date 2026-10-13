"""
Fundamentals Repository
Data access layer for financial ratios, valuations, and corporate health scores.
"""

from datetime import date
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.fundamentals import Fundamentals


class FundamentalsRepository:

    @staticmethod
    def get_latest(db: Session, stock_id: int) -> Optional[Fundamentals]:
        if db is None:
            return None
        stmt = (
            select(Fundamentals)
            .where(Fundamentals.stock_id == stock_id)
            .order_by(Fundamentals.as_of_date.desc())
        )
        return db.scalars(stmt).first()

    @staticmethod
    def upsert(
        db: Session,
        stock_id: int,
        fund_data: Dict[str, Any],
        as_of_date: Optional[date] = None,
    ) -> Optional[Fundamentals]:
        if db is None:
            return None
        target_date = as_of_date or date.today()

        existing = db.scalars(
            select(Fundamentals).where(
                Fundamentals.stock_id == stock_id,
                Fundamentals.as_of_date == target_date,
            )
        ).first()

        def clean_val(v):
            if v is None or v == "N/A":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        fields = {
            "revenue_growth_pct": clean_val(fund_data.get("Revenue Growth (%)")),
            "profit_growth_pct": clean_val(fund_data.get("Profit Growth (%)")),
            "eps_trailing": clean_val(fund_data.get("EPS (Trailing)")),
            "eps_forward": clean_val(fund_data.get("EPS (Forward)")),
            "pe_ratio": clean_val(fund_data.get("PE Ratio")),
            "pb_ratio": clean_val(fund_data.get("PB Ratio")),
            "roe_pct": clean_val(fund_data.get("ROE (%)")),
            "roce_pct": clean_val(fund_data.get("ROCE (%)")),
            "debt_to_equity": clean_val(fund_data.get("Debt to Equity")),
            "free_cash_flow": clean_val(fund_data.get("Free Cash Flow (₹)")),
            "promoter_holding_pct": clean_val(fund_data.get("Promoter Holding (%)")),
            "institutional_holding_pct": clean_val(fund_data.get("Institutional Holding (%)")),
            "fundamental_score": int(fund_data["Fundamental Score"]) if fund_data.get("Fundamental Score") and fund_data["Fundamental Score"] != "N/A" else None,
            "fundamental_rating": str(fund_data.get("Fundamental Rating", "")),
            "summary": str(fund_data.get("Fundamental Summary", "")),
            "key_highlights": fund_data.get("Key Highlights", []),
            "raw_metrics": fund_data,
        }

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        new_record = Fundamentals(
            stock_id=stock_id,
            as_of_date=target_date,
            **fields,
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
