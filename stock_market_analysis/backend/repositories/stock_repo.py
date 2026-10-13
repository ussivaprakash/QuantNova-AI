"""
Stock Repository
Data access layer for stock master table.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from models.stock import Stock


class StockRepository:

    @staticmethod
    def get_by_id(db: Session, stock_id: int) -> Optional[Stock]:
        if db is None:
            return None
        return db.get(Stock, stock_id)

    @staticmethod
    def get_by_symbol(db: Session, symbol: str) -> Optional[Stock]:
        if db is None:
            return None
        clean_symbol = symbol.strip().upper()
        stmt = select(Stock).where(Stock.symbol == clean_symbol)
        return db.scalars(stmt).first()

    @staticmethod
    def search(db: Session, query: str, limit: int = 30) -> List[Stock]:
        if db is None:
            return []
        query_clean = query.strip()
        if not query_clean:
            stmt = select(Stock).where(Stock.is_active == True).order_by(Stock.symbol).limit(limit)
            return list(db.scalars(stmt).all())

        search_pattern = f"%{query_clean}%"
        stmt = (
            select(Stock)
            .where(
                Stock.is_active == True,
                or_(
                    Stock.symbol.ilike(search_pattern),
                    Stock.company_name.ilike(search_pattern),
                    Stock.sector.ilike(search_pattern),
                ),
            )
            .order_by(Stock.symbol)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_all_active(db: Session, limit: int = 100) -> List[Stock]:
        if db is None:
            return []
        stmt = select(Stock).where(Stock.is_active == True).order_by(Stock.symbol).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def upsert(db: Session, data: Dict[str, Any]) -> Optional[Stock]:
        if db is None:
            return None
        symbol = data["symbol"].strip().upper()
        existing = StockRepository.get_by_symbol(db, symbol)
        if existing:
            for k, v in data.items():
                if hasattr(existing, k) and v is not None:
                    setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        new_stock = Stock(
            symbol=symbol,
            company_name=data.get("company_name", symbol),
            exchange=data.get("exchange", "NSE"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            isin=data.get("isin"),
            is_active=data.get("is_active", True),
        )
        db.add(new_stock)
        db.commit()
        db.refresh(new_stock)
        return new_stock
