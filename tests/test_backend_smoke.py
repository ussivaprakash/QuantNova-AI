"""
QuantNova AI - Automated Backend Smoke & Health Test Suite
Tests API endpoints, module imports, and critical business logic.
Works with both unittest and pytest.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import DEFAULT, patch

# Ensure backend directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "stock_market_analysis" / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT / "stock_market_analysis") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "stock_market_analysis"))


class TestBackendSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend import api
        from fastapi.testclient import TestClient
        cls.api = api
        cls.client = TestClient(api.app)

    def test_01_backend_modules_import(self):
        """Verifies that all core quantitative and analytical modules import without error."""
        import config
        import database
        import data_loader
        import data_cleaner
        import indicators
        import trend_analysis
        import predictor
        import signal_engine
        import backtester
        import fundamentals
        import market_context
        import risk_analysis
        import question_understanding
        import research_planner
        import pdf_exporter
        import dashboard

        self.assertIsNotNone(config.settings)
        self.assertIsNotNone(question_understanding.understand_user_question)

    def test_02_health_endpoint(self):
        """Verifies that GET /api/health returns 200 OK and online status."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("active_stages", data)

    def test_03_stocks_catalog(self):
        """Verifies that GET /api/stocks returns active equities list."""
        response = self.client.get("/api/stocks?limit=10")
        self.assertEqual(response.status_code, 200)
        stocks = response.json()
        self.assertIsInstance(stocks, list)
        self.assertGreater(len(stocks), 0)

    def test_04_search_endpoint(self):
        """Verifies ticker search endpoint."""
        response = self.client.get("/api/search?q=RELIANCE")
        self.assertEqual(response.status_code, 200)
        results = response.json()
        self.assertIsInstance(results, list)
        symbols = [item["symbol"] for item in results]
        self.assertTrue(any("RELIANCE" in s for s in symbols))

    def test_05_question_understanding(self):
        """Verifies question parser and backward-compatible alias."""
        from question_understanding import understand_user_question, parse_user_question
        
        # Test alias identity
        self.assertEqual(understand_user_question, parse_user_question)
        
        # Test query parsing
        res = understand_user_question("Why did Tata Motors rise today?")
        self.assertEqual(res["primary_symbol"], "TATAMOTORS.NS")
        self.assertEqual(res["intent"], "stock_movement")

    def test_06_pipeline_config(self):
        """Verifies PipelineConfig validation and defaults."""
        from data_loader import PipelineConfig
        cfg = PipelineConfig(ticker="TCS.NS", period="1y")
        self.assertEqual(cfg.ticker, "TCS.NS")
        self.assertEqual(cfg.period, "1y")

    def test_07_production_frontend_cors_preflight(self):
        response = self.client.options(
            "/api/analyze",
            headers={
                "Origin": "https://quant-nova-ai-rprt.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "https://quant-nova-ai-rprt.vercel.app")

    def test_08_invalid_period_is_rejected_before_provider_call(self):
        response = self.client.get("/api/analyze?symbol=RELIANCE.NS&period=2y")
        self.assertEqual(response.status_code, 422)

    def test_09_unavailable_analysis_market_data_returns_provider_error(self):
        with patch.object(self.api, "download_raw_data", side_effect=ValueError("Yahoo Finance returned no live OHLCV data for 'INVALIDXYZ.NS'.")):
            response = self.client.get("/api/analyze?symbol=INVALIDXYZ.NS&period=1y")
        self.assertEqual(response.status_code, 502)
        self.assertIn("Yahoo Finance", response.json()["detail"])

    def test_10_provider_no_data_is_an_error_not_synthetic_success(self):
        import data_loader
        from data_loader import PipelineConfig

        with patch.object(data_loader.yf, "Ticker") as ticker:
            ticker.return_value.history.return_value = __import__("pandas").DataFrame()
            with self.assertRaisesRegex(ValueError, "Yahoo Finance returned no live OHLCV data"):
                data_loader.download_raw_data(PipelineConfig(ticker="INVALIDXYZ.NS", period="1y"))
        ticker.assert_called_once_with("INVALIDXYZ.NS")

    def test_11_incomplete_ohlcv_rows_are_excluded_not_filled(self):
        import pandas as pd
        from data_cleaner import audit_ohlcv_dataset

        rows = pd.DataFrame({
            "Date": pd.date_range("2025-01-01", periods=3, freq="B"),
            "Open": [10.0, None, 12.0], "High": [11.0, None, 13.0],
            "Low": [9.0, None, 11.0], "Close": [10.5, None, 12.5],
            "Adj Close": [10.5, None, 12.5], "Volume": [100.0, 120.0, 140.0],
        })
        cleaned, audit, _ = audit_ohlcv_dataset(rows)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(audit["Rows Excluded for Missing Values"], 1)
        self.assertEqual(audit["Missing Values Imputed"], 0)

    def test_12_missing_fundamentals_are_not_scored_from_defaults(self):
        import fundamentals

        with patch.object(fundamentals.yf, "Ticker") as ticker:
            ticker.return_value.info = {}
            result = fundamentals.analyze_fundamentals("UNKNOWN.NS")
        self.assertIsNone(result["Fundamental Score"])
        self.assertEqual(result["Fundamental Rating"], "Incomplete Data")

    def test_13_missing_benchmark_is_not_reported_as_bullish(self):
        import market_context
        import pandas as pd

        with patch.object(market_context.yf, "Ticker") as ticker:
            ticker.return_value.history.return_value = pd.DataFrame()
            result = market_context.analyze_market_context(pd.DataFrame({"Close": range(25)}))
        self.assertIsNone(result["Nifty 1M Return (%)"])
        self.assertIsNone(result["Relative Strength Rating"])
        self.assertEqual(result["Data Status"], "unavailable")

    def test_14_ml_probability_is_unavailable_without_enough_history(self):
        import numpy as np
        import pandas as pd
        import predictor

        source = pd.DataFrame({"Close": [100.0, 101.0]})
        with patch.object(predictor, "build_prediction_features", return_value=(pd.DataFrame(), pd.Series(dtype=int), source)):
            result, metrics, feature_importance = predictor.train_and_evaluate_random_forest(source)
        self.assertTrue(result["ML Bull Prob (%)"].isna().all())
        self.assertTrue(result["ML Prediction"].str.startswith("Unavailable").all())

    def test_15_risk_levels_require_observed_atr_and_volatility(self):
        import pandas as pd
        from risk_analysis import analyze_risk_metrics

        row = pd.DataFrame({"Close": [100.0], "ATR (14)": [float("nan")], "Rolling Volatility (20D Ann %)": [22.0]})
        with self.assertRaisesRegex(ValueError, "latest ATR is unavailable"):
            analyze_risk_metrics(row)

    def test_16_analysis_api_contract_with_controlled_pipeline_inputs(self):
        import numpy as np
        import pandas as pd

        date = pd.Timestamp("2026-10-14")
        raw = pd.DataFrame({
            "Date": [date], "Open": [99.0], "High": [102.0], "Low": [98.0],
            "Close": [101.0], "Adj Close": [101.0], "Volume": [1000],
        })
        raw.attrs["data_source"] = "yahoo_finance"
        latest = pd.DataFrame({
            "Date": [date], "Open": [99.0], "High": [102.0], "Low": [98.0],
            "Close": [101.0], "Volume": [1000], "ATR (14)": [2.0],
            "RSI (14)": [55.0], "MACD Histogram": [0.5], "SMA 20": [100.0],
            "SMA 50": [98.0], "ADX (14)": [22.0], "VWAP": [100.0], "OBV": [100.0],
            "SuperTrend": [97.0], "Support 1": [95.0], "Resistance 1": [105.0],
            "Trend Classification": ["Bullish"], "Trend Score": [60], "Trend Reason": ["Test trend"],
            "MA20 Slope (%)": [1.0], "ML Bull Prob (%)": [np.nan], "ML Prediction": ["Unavailable"],
            "ML Confidence": ["Unavailable"], "Signal": ["BUY"], "Signal Confidence (%)": [70],
            "Technical Score": [65], "Reason for Decision": ["Test signal"],
        })
        fundamentals = {
            "Company Name": "Controlled Test Company", "Sector": "Test", "Fundamental Score": None,
            "Fundamental Rating": "Incomplete Data", "Fundamental Summary": "Source data unavailable",
            "Key Highlights": [],
        }
        risk = {
            "Risk Score": 40, "Risk Category": "Moderate Risk", "Risk-to-Reward Ratio": "1:1.57",
            "Suggested Entry Price (₹)": 101.0, "Suggested Stop Loss (₹)": 97.5,
            "Suggested Target Price (₹)": 106.5,
        }
        with patch.multiple(
            self.api,
            download_raw_data=DEFAULT,
            audit_ohlcv_dataset=DEFAULT,
            calculate_all_indicators=DEFAULT,
            analyze_trend_regime=DEFAULT,
            analyze_fundamentals=DEFAULT,
            analyze_market_context=DEFAULT,
            train_and_evaluate_random_forest=DEFAULT,
            generate_buy_hold_sell_signals=DEFAULT,
            analyze_risk_metrics=DEFAULT,
            run_strategy_backtest=DEFAULT,
        ) as mocks:
            mocks["download_raw_data"].return_value = raw
            mocks["audit_ohlcv_dataset"].return_value = (raw, {"Duplicates Removed": 0, "Missing Values Imputed": 0, "Rows Excluded for Missing Values": 0}, pd.DataFrame())
            mocks["calculate_all_indicators"].return_value = raw
            mocks["analyze_trend_regime"].return_value = latest
            mocks["analyze_fundamentals"].return_value = fundamentals
            mocks["analyze_market_context"].return_value = {"Data Status": "unavailable", "Relative Strength Rating": None}
            mocks["train_and_evaluate_random_forest"].return_value = (latest, {}, pd.DataFrame())
            mocks["generate_buy_hold_sell_signals"].return_value = latest
            mocks["analyze_risk_metrics"].return_value = risk
            mocks["run_strategy_backtest"].return_value = (latest, pd.DataFrame(), pd.DataFrame())
            response = self.client.get("/api/analyze?symbol=CONTROLLEDTEST.NS&period=1y")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["latest_price"], 101.0)
        self.assertEqual(body["market_data_source"], "yahoo_finance")
        self.assertIsNone(body["stage_7_machine_learning"]["bullish_probability"])
        self.assertIsNone(body["stage_10_decision_engine"]["fundamental_score"])
        self.assertEqual(len(body["pipeline_stages"]), 10)
        self.assertTrue(all(stage["status"] == "completed" for stage in body["pipeline_stages"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
