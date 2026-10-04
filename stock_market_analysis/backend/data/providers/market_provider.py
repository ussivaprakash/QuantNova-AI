"""
Market Data Provider for QuantNova AI.

Fetches real-time price quotes, intraday movements, historical OHLCV data,
volume metrics, delivery context, and benchmark/sector index context for Indian equities.
"""

from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np


class MarketDataProvider:
    """Provider for stock prices, market breadth, intraday movements, and sector context."""

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches latest quote metrics for target ticker symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            fast_info = getattr(ticker, "fast_info", {})
            
            # Fetch 5-day history for recent price change
            hist = ticker.history(period="5d")
            if not hist.empty:
                latest_close = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else float(info.get("previousClose", latest_close))
                change = round(latest_close - prev_close, 2)
                p_change = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0
                open_price = float(hist["Open"].iloc[-1])
                high_price = float(hist["High"].iloc[-1])
                low_price = float(hist["Low"].iloc[-1])
                volume = int(hist["Volume"].iloc[-1])
                avg_vol_20d = int(hist["Volume"].mean())
            else:
                latest_close = float(info.get("currentPrice", info.get("regularMarketPrice", 500.0)))
                prev_close = float(info.get("previousClose", latest_close))
                change = round(latest_close - prev_close, 2)
                p_change = round(info.get("regularMarketChangePercent", 0.0), 2)
                open_price = float(info.get("open", latest_close))
                high_price = float(info.get("dayHigh", latest_close * 1.01))
                low_price = float(info.get("dayLow", latest_close * 0.99))
                volume = int(info.get("volume", 1000000))
                avg_vol_20d = int(info.get("averageVolume", 1000000))

            vol_ratio = round(volume / max(avg_vol_20d, 1), 2)

            return {
                "symbol": symbol,
                "company_name": info.get("longName", info.get("shortName", symbol)),
                "currency": "INR",
                "current_price": latest_close,
                "previous_close": prev_close,
                "change": change,
                "percent_change": p_change,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "avg_volume_20d": avg_vol_20d,
                "volume_ratio": vol_ratio,
                "market_cap": info.get("marketCap", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", high_price),
                "52w_low": info.get("fiftyTwoWeekLow", low_price),
                "day_range": f"₹{low_price:.2f} - ₹{high_price:.2f}",
                "52w_range": f"₹{info.get('fiftyTwoWeekLow', low_price):.2f} - ₹{info.get('fiftyTwoWeekHigh', high_price):.2f}"
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch market quote: {str(e)}",
                "current_price": 0.0,
                "percent_change": 0.0,
                "volume": 0
            }

    def get_intraday(self, symbol: str) -> Dict[str, Any]:
        """Fetches 1-day intraday 5m price movement series."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="5m")
            if df.empty:
                df = ticker.history(period="5d", interval="15m")

            if not df.empty:
                times = [t.strftime("%H:%M") for t in df.index]
                closes = df["Close"].round(2).tolist()
                volumes = df["Volume"].tolist()
                return {
                    "timestamps": times,
                    "prices": closes,
                    "volumes": volumes,
                    "intraday_high": float(df["High"].max()),
                    "intraday_low": float(df["Low"].min()),
                    "vwap": round(float((df["Close"] * df["Volume"]).sum() / max(df["Volume"].sum(), 1)), 2)
                }
        except Exception:
            pass

        return {"timestamps": [], "prices": [], "volumes": [], "intraday_high": 0.0, "intraday_low": 0.0, "vwap": 0.0}

    def get_market_context(self, symbol: str = "TATAMOTORS.NS") -> Dict[str, Any]:
        """Fetches Indian benchmark market indicators (NIFTY 50, SENSEX, Sector Index)."""
        nifty = self.get_quote("^NSEI")
        sensex = self.get_quote("^BSESN")

        # Determine appropriate sector index
        sector_symbol = "^CNXAUTO" if "TATA" in symbol or "MARUTI" in symbol or "M&M" in symbol or "ASHOK" in symbol else "^NSEBANK" if "BANK" in symbol or "SBIN" in symbol or "IOB" in symbol else "^CNXIT"
        sector_quote = self.get_quote(sector_symbol)

        return {
            "nifty_50": {
                "price": nifty.get("current_price", 24500.0),
                "change": nifty.get("change", 0.0),
                "percent_change": nifty.get("percent_change", 0.0),
                "trend": "Bullish" if nifty.get("percent_change", 0) > 0.2 else "Bearish" if nifty.get("percent_change", 0) < -0.2 else "Neutral"
            },
            "sensex": {
                "price": sensex.get("current_price", 80200.0),
                "change": sensex.get("change", 0.0),
                "percent_change": sensex.get("percent_change", 0.0),
            },
            "sector_index": {
                "name": "NIFTY Auto Index" if "CNXAUTO" in sector_symbol else "NIFTY Bank Index" if "NSEBANK" in sector_symbol else "NIFTY IT Index",
                "symbol": sector_symbol,
                "price": sector_quote.get("current_price", 22000.0),
                "percent_change": sector_quote.get("percent_change", 0.0)
            }
        }
