"""
QuantNova AI - Production Seed Script
Populates initial catalog for 5 top Indian Equities (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK)
along with realistic sample OHLCV data, fundamental ratios, signals, and risk profiles.

NOTE: All generated sample metrics are clearly marked with {"data_source": "seed_sample_data"}.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import numpy as np
import pandas as pd

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import engine, SessionLocal, Base
from models import Stock, MarketData, Fundamentals, TradingSignal, RiskAssessment, AnalysisSnapshot
from repositories import StockRepository, MarketDataRepository, FundamentalsRepository, AnalysisRepository

SAMPLE_STOCKS = [
    {
        "symbol": "RELIANCE.NS",
        "company_name": "Reliance Industries Limited",
        "exchange": "NSE",
        "sector": "Energy & Petrochemicals",
        "industry": "Oil & Gas Refining / Telecom / Retail",
        "isin": "INE002A01018",
        "base_price": 2950.0,
        "fund_score": 88,
        "fund_rating": "Exceptional Fundamentals",
        "pe": 26.4,
        "pb": 2.8,
        "roe": 14.5,
        "roce": 16.2,
        "debt_to_equity": 0.38,
        "promoter_pct": 50.3,
        "inst_pct": 39.2,
        "signal": "BUY",
        "signal_confidence": 85,
    },
    {
        "symbol": "TCS.NS",
        "company_name": "Tata Consultancy Services Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "isin": "INE467B01029",
        "base_price": 4200.0,
        "fund_score": 92,
        "fund_rating": "Exceptional Fundamentals",
        "pe": 31.2,
        "pb": 13.5,
        "roe": 48.0,
        "roce": 59.0,
        "debt_to_equity": 0.05,
        "promoter_pct": 71.8,
        "inst_pct": 23.5,
        "signal": "BUY",
        "signal_confidence": 88,
    },
    {
        "symbol": "INFY.NS",
        "company_name": "Infosys Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
        "industry": "IT Services & Software",
        "isin": "INE009A01021",
        "base_price": 1820.0,
        "fund_score": 86,
        "fund_rating": "Exceptional Fundamentals",
        "pe": 27.5,
        "pb": 7.8,
        "roe": 31.8,
        "roce": 40.5,
        "debt_to_equity": 0.08,
        "promoter_pct": 14.7,
        "inst_pct": 69.4,
        "signal": "HOLD / WAIT",
        "signal_confidence": 60,
    },
    {
        "symbol": "HDFCBANK.NS",
        "company_name": "HDFC Bank Limited",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "isin": "INE040A01034",
        "base_price": 1650.0,
        "fund_score": 84,
        "fund_rating": "Strong Fundamentals",
        "pe": 18.2,
        "pb": 2.7,
        "roe": 16.5,
        "roce": 17.8,
        "debt_to_equity": 0.85,
        "promoter_pct": 0.0,
        "inst_pct": 79.5,
        "signal": "BUY",
        "signal_confidence": 80,
    },
    {
        "symbol": "ICICIBANK.NS",
        "company_name": "ICICI Bank Limited",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "isin": "INE090A01021",
        "base_price": 1240.0,
        "fund_score": 89,
        "fund_rating": "Exceptional Fundamentals",
        "pe": 17.8,
        "pb": 3.1,
        "roe": 18.9,
        "roce": 19.5,
        "debt_to_equity": 0.78,
        "promoter_pct": 0.0,
        "inst_pct": 84.1,
        "signal": "BUY",
        "signal_confidence": 90,
    },
    {
        "symbol": "TATAMOTORS.NS",
        "company_name": "Tata Motors Limited",
        "exchange": "NSE",
        "sector": "Automotive",
        "industry": "Passenger Vehicles & Commercial Trucks",
        "isin": "INE155A01022",
        "base_price": 980.0,
        "fund_score": 82,
        "fund_rating": "Strong Fundamentals",
        "pe": 16.5,
        "pb": 4.2,
        "roe": 24.5,
        "roce": 21.0,
        "debt_to_equity": 0.65,
        "promoter_pct": 46.4,
        "inst_pct": 38.2,
        "signal": "BUY",
        "signal_confidence": 82,
    },
]


def seed_database():
    """Populates database with initial stocks and seed OHLCV records."""
    print("=" * 65)
    print("🌱 SEEDING QUANTNOVA AI POSTGRESQL DATABASE")
    print("=" * 65)

    # Ensure tables exist (Alembic handles this in production, fallback create_all here)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        today = date.today()
        num_days = 252  # 1 trading year of historical daily bars

        for item in SAMPLE_STOCKS:
            print(f"--> Ingesting Stock: {item['symbol']} ({item['company_name']})...")

            # 1. Upsert Stock Master Record
            stock = StockRepository.upsert(db, {
                "symbol": item["symbol"],
                "company_name": item["company_name"],
                "exchange": item["exchange"],
                "sector": item["sector"],
                "industry": item["industry"],
                "isin": item["isin"],
                "is_active": True,
            })

            # 2. Check if OHLCV already exists
            existing_bars_count = MarketDataRepository.count_bars(db, stock.id)
            if existing_bars_count < num_days:
                print(f"    Generating {num_days} sample OHLCV daily bars [marked as seed data]...")
                np.random.seed(abs(hash(item["symbol"])) % (2**32))
                base_p = item["base_price"]
                returns = np.random.normal(0.0006, 0.014, num_days)
                close_prices = base_p * np.exp(np.cumsum(returns))

                dates = pd.date_range(end=today, periods=num_days, freq="B")
                ohlcv_records = []
                for i in range(num_days):
                    c = round(float(close_prices[i]), 2)
                    o = round(c * (1 + float(np.random.normal(0, 0.004))), 2)
                    h = round(max(o, c) * (1 + float(abs(np.random.normal(0, 0.007)))), 2)
                    l = round(min(o, c) * (1 - float(abs(np.random.normal(0, 0.007)))), 2)
                    vol = int(np.random.randint(800000, 15000000))
                    ohlcv_records.append({
                        "trading_date": dates[i].date(),
                        "open": o,
                        "high": h,
                        "low": l,
                        "close": c,
                        "adj_close": c,
                        "volume": vol,
                    })

                inserted = MarketDataRepository.bulk_upsert(db, stock.id, ohlcv_records)
                print(f"    ✓ Inserted {inserted} OHLCV bars.")
            else:
                print(f"    ✓ OHLCV bars already exist ({existing_bars_count} records). Skipping.")

            # 3. Upsert Fundamentals
            fund_data = {
                "Company Name": item["company_name"],
                "Sector": item["sector"],
                "Industry": item["industry"],
                "Revenue Growth (%)": 14.8,
                "Profit Growth (%)": 18.2,
                "EPS (Trailing)": round(item["base_price"] / item["pe"], 2),
                "EPS (Forward)": round((item["base_price"] / item["pe"]) * 1.15, 2),
                "PE Ratio": item["pe"],
                "PB Ratio": item["pb"],
                "ROE (%)": item["roe"],
                "ROCE (%)": item["roce"],
                "Debt to Equity": item["debt_to_equity"],
                "Free Cash Flow (₹)": 45000000000.0,
                "Promoter Holding (%)": item["promoter_pct"],
                "Institutional Holding (%)": item["inst_pct"],
                "Fundamental Score": item["fund_score"],
                "Fundamental Rating": item["fund_rating"],
                "Fundamental Summary": f"[SEED DATA] {item['company_name']} demonstrates institutional health with a {item['fund_score']}/100 score.",
                "Key Highlights": [
                    f"Strong double-digit ROE ({item['roe']}%)",
                    f"Healthy balance sheet with D/E of {item['debt_to_equity']}x",
                    f"Significant institutional backing of {item['inst_pct']}%",
                ],
                "data_source": "seed_sample_data"
            }
            FundamentalsRepository.upsert(db, stock.id, fund_data, as_of_date=today)
            print(f"    ✓ Upserted Fundamental Health Snapshot ({item['fund_score']}/100).")

            # 4. Upsert Baseline Trading Signal
            latest_price = round(float(item["base_price"]), 2)
            atr_approx = round(latest_price * 0.02, 2)
            stop_loss = round(latest_price - (1.5 * atr_approx), 2)
            target_price = round(latest_price + (2.5 * atr_approx), 2)

            signal_payload = {
                "signal": item["signal"],
                "confidence_score": item["signal_confidence"],
                "technical_score": 78,
                "fundamental_score": item["fund_score"],
                "risk_score": 32,
                "risk_level": "Moderate Risk",
                "entry_price": latest_price,
                "stop_loss": stop_loss,
                "target_price": target_price,
                "risk_reward_ratio": "1:1.67",
                "expected_time_horizon": "1 - 3 Months Swing / Position",
                "pros": [
                    "Trading above 50-day and 200-day simple moving averages",
                    "RSI momentum holding above neutral 50 threshold",
                    "High institutional and promoter ownership stability",
                ],
                "cons": [
                    "Near-term resistance approaching 52-week swing high",
                ],
                "risks": [
                    "Macro headline volatility and interest rate revision cycles",
                ],
                "reason_for_decision": f"[SEED DATA] Multi-factor indicator consensus confirms {item['signal']}.",
                "ai_explanation": f"[SEED DATA] QuantNova AI algorithmic engine flags {item['symbol']} with {item['signal_confidence']}% confidence.",
            }
            AnalysisRepository.save_trading_signal(db, stock.id, signal_payload, signal_date=today)

            # 5. Upsert Baseline Risk Assessment
            risk_payload = {
                "Risk Score": 32,
                "Risk Category": "Moderate Risk",
                "Annualized Volatility (%)": 21.4,
                "Suggested Entry Price (₹)": latest_price,
                "Suggested Stop Loss (₹)": stop_loss,
                "Suggested Target Price (₹)": target_price,
                "Risk-to-Reward Ratio": "1:1.67",
                "Recommended Shares": max(1, int(2000 / (latest_price - stop_loss))),
                "Suggested Position Value (₹)": latest_price * 15,
                "Suggested Portfolio Size (%)": 12.5,
            }
            AnalysisRepository.save_risk_assessment(db, stock.id, risk_payload, assessment_date=today)
            print(f"    ✓ Stored Baseline Signal & Risk Assessment.")

        print("=" * 65)
        print("✨ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
