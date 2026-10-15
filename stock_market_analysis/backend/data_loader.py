"""
Stage 1: Raw Data Ingestion & Cleaning Module.
Downloads daily OHLCV data for specified ticker and standardizes schema.
"""

from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

@dataclass
class PipelineConfig:
    """Central configuration for the stock analysis pipeline."""
    ticker: str = "TATAMOTORS.NS"
    period: str = "max"  # Fetch complete A-Z history from listing date to present
    interval: str = "1d"
    output_excel: Path = PROCESSED_DATA_DIR / "TATAMOTORS_NS_Stock_Analysis_Report.xlsx"
    output_dashboard: Path = REPORTS_DIR / "TATAMOTORS_NS_Trading_Dashboard.html"
    rsi_period: int = 14
    short_ma_window: int = 5
    long_ma_window: int = 20
    macd_fast_span: int = 12
    macd_slow_span: int = 26
    macd_signal_span: int = 9
    bb_window: int = 20
    bb_std_dev: float = 2.0


PERIOD_DAYS_MAP = {
    "1m": 22,
    "3m": 65,
    "6m": 126,
    "1y": 252,
    "3y": 756,
    "5y": 1260,
    "max": 2520,
}


TICKER_ALIASES = {
    "TATAMOTORS.NS": ["TMPV.NS", "TATAMOTORS.BO", "TMPV.BO"],
    "TATAMOTORS": ["TMPV.NS", "TATAMOTORS.BO"],
}


def download_raw_data(config: PipelineConfig, db=None) -> pd.DataFrame:
    """
    Download raw daily OHLCV stock data from PostgreSQL database if cached,
    otherwise download from Yahoo Finance and persist to database.
    Uses the requested period only. Missing provider data is an error, never a synthetic result.
    """
    raw_ticker = config.ticker.strip().upper()
    if " " in raw_ticker:
        raw_ticker = raw_ticker.replace(" ", "")

    period_req = config.period.lower() if config.period else "1y"
    if period_req not in PERIOD_DAYS_MAP:
        raise ValueError(f"Unsupported analysis period '{period_req}'. Choose one of: {', '.join(PERIOD_DAYS_MAP)}.")
    num_days_target = PERIOD_DAYS_MAP[period_req]

    # 1. Try reading from PostgreSQL Database first if db session is provided
    if db is not None:
        try:
            from repositories.stock_repo import StockRepository
            from repositories.market_data_repo import MarketDataRepository
            from repositories.fundamentals_repo import FundamentalsRepository

            stock = StockRepository.get_by_symbol(db, raw_ticker)
            if stock:
                provenance = FundamentalsRepository.get_latest(db, stock.id)
                source_metrics = provenance.raw_metrics if provenance else {}
                trusted_source = source_metrics.get("data_source") == "yahoo_finance"
                if not trusted_source:
                    raise ValueError(f"Cached market data for {raw_ticker} has no verified live-data provenance.")
                cached_bars = MarketDataRepository.get_bars_by_stock_id(db, stock.id)
                if len(cached_bars) >= min(num_days_target, 20):
                    df_db = MarketDataRepository.to_dataframe(cached_bars)
                    latest_cached = pd.to_datetime(df_db["Date"]).max()
                    cache_age_days = (pd.Timestamp.now(tz="UTC").tz_localize(None).normalize() - latest_cached.tz_localize(None).normalize() if latest_cached.tzinfo else pd.Timestamp.now().normalize() - latest_cached.normalize()).days
                    if cache_age_days > 7:
                        raise ValueError(f"Cached market data for {raw_ticker} is stale ({cache_age_days} days old).")
                    if len(df_db) > num_days_target:
                        df_db = df_db.tail(num_days_target).reset_index(drop=True)
                    df_db.attrs["data_source"] = "postgresql_cache"
                    print(f"      ✓ Retrieved {len(df_db)} OHLCV bars from PostgreSQL cache for {raw_ticker}")
                    return df_db
        except Exception as e:
            print(f"      ⚠️ Database cache check failed (error_type={type(e).__name__}), proceeding with external download...")

    # 2. External Download via Yahoo Finance
    tickers_to_try = [raw_ticker]
    if raw_ticker in TICKER_ALIASES:
        tickers_to_try.extend(TICKER_ALIASES[raw_ticker])

    data = pd.DataFrame()
    provider_errors = []

    for sym in tickers_to_try:
        try:
            downloaded = yf.Ticker(sym).history(period=period_req, interval=config.interval, timeout=15)
            if not downloaded.empty and len(downloaded) > 5:
                data = downloaded
                print(f"      ✓ Successfully retrieved live market data for symbol: {sym} ({len(data)} rows)")
                break
            provider_errors.append(f"{sym}: no data for requested period {period_req}")
        except Exception as exc:
            provider_errors.append(f"{sym}: {type(exc).__name__}")
        if not data.empty:
            break

    if data.empty:
        error_summary = "; ".join(provider_errors)
        raise ValueError(f"Yahoo Finance returned no live OHLCV data for '{raw_ticker}' for period {period_req}. Check the symbol or retry later. Provider details: {error_summary}")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    data["Date"] = pd.to_datetime(data["Date"])

    if "Adj Close" not in data.columns and "Close" in data.columns:
        data["Adj Close"] = data["Close"]

    expected_columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    missing_columns = [col for col in expected_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Market data provider returned incomplete live data for '{raw_ticker}' (missing: {', '.join(missing_columns)}).")

    result_df = data[expected_columns].sort_values("Date").reset_index(drop=True)
    if result_df.empty or result_df[["Open", "High", "Low", "Close", "Volume"]].isna().any().any():
        raise ValueError(f"Yahoo Finance returned incomplete OHLCV rows for '{raw_ticker}'. No analysis was produced.")
    if (result_df[["Open", "High", "Low", "Close"]] <= 0).any().any() or (result_df["Volume"] < 0).any():
        raise ValueError(f"Yahoo Finance returned invalid OHLCV values for '{raw_ticker}'. No analysis was produced.")
    if len(result_df) > num_days_target:
        result_df = result_df.tail(num_days_target).reset_index(drop=True)

    # 3. Cache newly downloaded market data in PostgreSQL if db session is provided
    if db is not None:
        try:
            from repositories.stock_repo import StockRepository
            from repositories.market_data_repo import MarketDataRepository

            stock = StockRepository.upsert(db, {
                "symbol": raw_ticker,
                "company_name": raw_ticker,
                "exchange": "BSE" if raw_ticker.endswith(".BO") else "NSE",
            })
            bars_to_upsert = [
                {
                    "trading_date": row["Date"].date(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adj_close": float(row.get("Adj Close", row["Close"])),
                    "volume": int(row["Volume"]),
                }
                for _, row in result_df.iterrows()
            ]
            MarketDataRepository.bulk_upsert(db, stock.id, bars_to_upsert)
            print(f"      ✓ Persisted {len(bars_to_upsert)} bars to PostgreSQL for {raw_ticker}")
        except Exception as e:
            print(f"      ⚠️ Failed to cache market data in DB (error_type={type(e).__name__})")

    result_df.attrs["data_source"] = "yahoo_finance"
    return result_df

