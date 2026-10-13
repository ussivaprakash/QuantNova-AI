"""
QuantNova AI - Automated Backend Smoke & Health Test Suite
Tests API endpoints, module imports, and critical business logic.
Works with both unittest and pytest.
"""

import sys
import unittest
from pathlib import Path

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
        import api
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
