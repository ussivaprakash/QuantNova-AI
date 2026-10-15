"""
End-to-End Stock Market Quantitative Pipeline.

Pipeline Stages:
1. Raw Data Ingestion & Cleaning (Yahoo Finance API)
2. Technical Indicators Calculation (MA, RSI, MACD, BB, ATR, Gaps)
3. Trend Analysis & Market Regime Classification
4. Machine Learning Prediction Model (Random Forest Classifier)
5. Buy / Hold / Sell Signal Engine with Confidence Scoring
6. Interactive HTML Dashboard & Multi-Sheet Excel Workbook Export
"""

import sys
from pathlib import Path
import pandas as pd

# Add current code directory to python path
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from data_loader import PipelineConfig, download_raw_data
from data_cleaner import audit_ohlcv_dataset
from indicators import calculate_all_indicators
from trend_analysis import analyze_trend_regime
from predictor import train_and_evaluate_random_forest
from signal_engine import generate_buy_hold_sell_signals
from backtester import run_strategy_backtest
from dashboard import generate_html_dashboard, export_to_excel_workbook


def run_pipeline():
    """Executes all 8 stages of the quantitative stock trading pipeline."""
    config = PipelineConfig()
    print("=" * 65)
    print(f"🚀 RUNNING 8-STAGE QUANTITATIVE PIPELINE FOR {config.ticker}")
    print("=" * 65)

    # --- Stage 1: Data Collection ---
    print("\n[Stage 1/8] Data Collection (Downloading OHLCV history)...")
    raw_data = download_raw_data(config)
    print(f"      ✓ Downloaded {len(raw_data)} daily records from {raw_data['Date'].min().date()} to {raw_data['Date'].max().date()}")

    # --- Stage 2: Data Cleaning ---
    print("\n[Stage 2/8] Data Cleaning & Quality Audit...")
    cleaned_data, audit_summary, audit_report_df = audit_ohlcv_dataset(raw_data)
    print(f"      ✓ Audit Cleaned: Duplicates: {audit_summary['Duplicates Removed']}, Nulls: {audit_summary['Missing Values Imputed']}, Range Fixes: {audit_summary['Price Range Violations Fixed']}")

    # --- Stage 3: Technical Indicators ---
    print("\n[Stage 3/8] Technical Indicators (SMA, EMA, RSI, MACD, BB, ATR, ADX, VWAP, OBV, Stoch)...")
    data_with_indicators = calculate_all_indicators(cleaned_data, config)
    print("      ✓ 25+ Technical Indicators computed successfully.")

    # --- Stage 4: Trend Analysis ---
    print("\n[Stage 4/8] Trend Analysis (5-Tier Market Regime & Reason Breakdown)...")
    data_with_trend = analyze_trend_regime(data_with_indicators)
    print("      ✓ Trend classification complete.")

    # --- Stage 5: Machine Learning ---
    print("\n[Stage 5/8] Machine Learning (Random Forest Chronological 70/30 Classifier)...")
    data_with_ml, rf_metrics, feature_importance_df = train_and_evaluate_random_forest(data_with_trend)
    print(f"      ✓ Random Forest Trained (Accuracy: {rf_metrics.get('Accuracy', 0):.2%}, F1: {rf_metrics.get('F1 Score', 0):.4f})")

    # --- Stage 6: Trading Signal Engine ---
    print("\n[Stage 6/8] Trading Signal Engine (Buy/Hold/Sell, Risk Level, Stop Loss, Target Price)...")
    final_df = generate_buy_hold_sell_signals(data_with_ml)
    print("      ✓ Trade Signal Decision Matrix applied.")

    # --- Stage 7: Backtesting ---
    print("\n[Stage 7/8] Backtesting Strategy Performance vs Buy-and-Hold Benchmark...")
    backtest_df, backtest_metrics_df, trade_log_df = run_strategy_backtest(final_df)
    print("      ✓ Out-of-Sample Quantitative Backtesting Complete.")

    # --- Stage 8: Dashboard & Reports ---
    print("\n[Stage 8/8] Dashboard & Reports (Generating Plotly Dashboard & 11-Sheet Excel Workbook)...")
    dashboard_path = generate_html_dashboard(backtest_df, config)
    excel_path = export_to_excel_workbook(
        backtest_df,
        config,
        audit_report_df=audit_report_df,
        rf_metrics=rf_metrics,
        feature_importance_df=feature_importance_df,
        backtest_metrics_df=backtest_metrics_df,
        trade_log_df=trade_log_df,
    )

    latest = final_df.iloc[-1]
    print("\n" + "=" * 65)
    print("📊 LATEST QUANTITATIVE SIGNAL ENGINE DECISION")
    print("=" * 65)
    print(f" Date                 : {latest['Date'].strftime('%Y-%m-%d')}")
    print(f" Ticker               : {config.ticker}")
    print(f" Close Price          : ₹{latest['Close']:.2f}")
    print(f" Trend Classification : {latest.get('Trend Classification', 'N/A')}")
    ml_probability = latest.get("ML Bull Prob (%)")
    ml_probability_text = f"{ml_probability:.1f}%" if pd.notna(ml_probability) else "Unavailable"
    print(f" ML Bull Probability  : {ml_probability_text}")
    print(f" Trade Signal         : {latest.get('Signal', 'HOLD / WAIT')}")
    print(f" Confidence Score     : {latest.get('Signal Confidence (%)', 0)}%")
    print(f" Risk Level           : {latest.get('Risk Level', 'N/A')}")
    print(f" Suggested Stop Loss  : ₹{latest.get('Suggested Stop Loss (₹)', 0):.2f}")
    print(f" Suggested Target     : ₹{latest.get('Suggested Target Price (₹)', 0):.2f}")
    print(f" Reason for Decision  : {latest.get('Reason for Decision', 'N/A')}")
    print(f" Action Plan          : {latest.get('Signal Action Plan', 'N/A')}")
    print("=" * 65)
    print(f"✨ Interactive Dashboard : {dashboard_path.resolve()}")
    print(f"📈 Excel Workbook       : {excel_path.resolve()}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_pipeline()
