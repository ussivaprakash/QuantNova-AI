"""
Market Data Repository
High-performance time-series ingestion and retrieval for equity OHLCV.
"""

from datetime import date
from typing import List, Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.market_data import MarketData


class MarketDataRepository:

    @staticmethod
    def get_bars_by_stock_id(
        db: Session,
        stock_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[MarketData]:
        if db is None:
            return []
        stmt = select(MarketData).where(MarketData.stock_id == stock_id)
        if start_date:
            stmt = stmt.where(MarketData.trading_date >= start_date)
        if end_date:
            stmt = stmt.where(MarketData.trading_date <= end_date)

        stmt = stmt.order_by(MarketData.trading_date.asc())
        if limit:
            stmt = stmt.limit(limit)

        return list(db.scalars(stmt).all())

    @staticmethod
    def get_latest_date(db: Session, stock_id: int) -> Optional[date]:
        if db is None:
            return None
        stmt = select(func.max(MarketData.trading_date)).where(MarketData.stock_id == stock_id)
        return db.scalar(stmt)

    @staticmethod
    def count_bars(db: Session, stock_id: int) -> int:
        if db is None:
            return 0
        stmt = select(func.count(MarketData.id)).where(MarketData.stock_id == stock_id)
        return db.scalar(stmt) or 0

    @staticmethod
    def bulk_upsert(db: Session, stock_id: int, records: List[Dict[str, Any]]) -> int:
        """
        High-performance bulk upsert of OHLCV bars.
        Uses PostgreSQL ON CONFLICT DO UPDATE for millisecond writes.
        """
        if db is None or not records:
            return 0

        # Try PostgreSQL native dialect insert
        try:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            insert_stmt = pg_insert(MarketData).values([
                {
                    "stock_id": stock_id,
                    "trading_date": r["trading_date"] if not isinstance(r["trading_date"], str) else pd.to_datetime(r["trading_date"]).date(),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "adj_close": float(r.get("adj_close", r["close"])),
                    "volume": int(r["volume"]),
                }
                for r in records
            ])

            upsert_stmt = insert_stmt.on_conflict_do_update(
                constraint="uq_stock_trading_date",
                set_={
                    "open": insert_stmt.excluded.open,
                    "high": insert_stmt.excluded.high,
                    "low": insert_stmt.excluded.low,
                    "close": insert_stmt.excluded.close,
                    "adj_close": insert_stmt.excluded.adj_close,
                    "volume": insert_stmt.excluded.volume,
                }
            )
            db.execute(upsert_stmt)
            db.commit()
            return len(records)

        except Exception:
            # Fallback for generic SQL / SQLite engines
            db.rollback()
            count = 0
            for r in records:
                t_date = r["trading_date"] if not isinstance(r["trading_date"], str) else pd.to_datetime(r["trading_date"]).date()
                existing = db.scalars(
                    select(MarketData).where(
                        MarketData.stock_id == stock_id,
                        MarketData.trading_date == t_date
                    )
                ).first()

                if existing:
                    existing.open = float(r["open"])
                    existing.high = float(r["high"])
                    existing.low = float(r["low"])
                    existing.close = float(r["close"])
                    existing.adj_close = float(r.get("adj_close", r["close"]))
                    existing.volume = int(r["volume"])
                else:
                    new_bar = MarketData(
                        stock_id=stock_id,
                        trading_date=t_date,
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        adj_close=float(r.get("adj_close", r["close"])),
                        volume=int(r["volume"]),
                    )
                    db.add(new_bar)
                count += 1
            db.commit()
            return count

    @staticmethod
    def to_dataframe(bars: List[MarketData]) -> pd.DataFrame:
        """Converts MarketData ORM objects into standard QuantNova Pandas DataFrame."""
        if not bars:
            return pd.DataFrame()

        records = [
            {
                "Date": pd.to_datetime(b.trading_date),
                "Open": float(b.open),
                "High": float(b.high),
                "Low": float(b.low),
                "Close": float(b.close),
                "Adj Close": float(b.adj_close),
                "Volume": int(b.volume),
            }
            for b in bars
        ]
        df = pd.DataFrame(records)
        df.sort_values(by="Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
