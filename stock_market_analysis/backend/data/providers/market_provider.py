"""
Market Data Provider for QuantNova AI.

Fetches real-time price quotes, intraday movements, historical OHLCV data,
volume metrics, delivery context, and benchmark/sector index context for Indian equities.
"""

from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd


class MarketDataProvider:
    """Provider for stock prices, market breadth, intraday movements, and sector context."""

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetches latest quote metrics for target ticker symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            fast_info = getattr(ticker, "fast_info", {})
            
            # Fetch 5-day history for recent price change
            hist = ticker.history(period="5d", timeout=15)
            if not hist.empty:
                latest_close = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else info.get("previousClose")
                change = round(latest_close - prev_close, 2) if prev_close else None
                p_change = round((change / prev_close) * 100.0, 2) if change is not None and prev_close > 0 else None
                open_price = float(hist["Open"].iloc[-1])
                high_price = float(hist["High"].iloc[-1])
                low_price = float(hist["Low"].iloc[-1])
                volume = int(hist["Volume"].iloc[-1])
                avg_vol_20d = int(hist["Volume"].mean())
            else:
                latest_close = info.get("currentPrice", info.get("regularMarketPrice"))
                if latest_close is None:
                    return {"symbol": symbol, "error": "Yahoo Finance returned no current quote."}
                latest_close = float(latest_close)
                prev_close = info.get("previousClose")
                change = round(latest_close - prev_close, 2) if prev_close else None
                p_change = round(info["regularMarketChangePercent"], 2) if info.get("regularMarketChangePercent") is not None else None
                open_price = info.get("open")
                high_price = info.get("dayHigh")
                low_price = info.get("dayLow")
                volume = info.get("volume")
                avg_vol_20d = info.get("averageVolume")

            vol_ratio = round(volume / avg_vol_20d, 2) if volume is not None and avg_vol_20d else None

            return {
                "symbol": symbol,
                "company_name": info.get("longName", info.get("shortName", symbol)),
                "currency": info.get("currency"),
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
                "market_cap": info.get("marketCap"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "day_range": f"{low_price} - {high_price}" if low_price is not None and high_price is not None else None,
                "52w_range": f"{info.get('fiftyTwoWeekLow')} - {info.get('fiftyTwoWeekHigh')}" if info.get("fiftyTwoWeekLow") is not None and info.get("fiftyTwoWeekHigh") is not None else None
            }
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"Failed to fetch market quote ({type(e).__name__})."
            }

    def get_intraday(self, symbol: str) -> Dict[str, Any]:
        """Fetches 1-day intraday 5m price movement series."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="5m", timeout=15)
            if df.empty:
                df = ticker.history(period="5d", interval="15m", timeout=15)

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
        except Exception as exc:
            return {"timestamps": [], "prices": [], "volumes": [], "error": f"Market data unavailable ({type(exc).__name__})."}

        return {"timestamps": [], "prices": [], "volumes": [], "error": "Yahoo Finance returned no intraday data."}

    def get_market_context(self, symbol: str = "TATAMOTORS.NS") -> Dict[str, Any]:
        """Fetches Indian benchmark market indicators (NIFTY 50, SENSEX, Sector Index)."""
        nifty = self.get_quote("^NSEI")
        sensex = self.get_quote("^BSESN")

        # Determine appropriate sector index
        sector_symbol = "^CNXAUTO" if "TATA" in symbol or "MARUTI" in symbol or "M&M" in symbol or "ASHOK" in symbol else "^NSEBANK" if "BANK" in symbol or "SBIN" in symbol or "IOB" in symbol else "^CNXIT"
        sector_quote = self.get_quote(sector_symbol)

        return {
            "nifty_50": {
                "price": nifty.get("current_price"),
                "change": nifty.get("change"),
                "percent_change": nifty.get("percent_change"),
                "trend": "Unavailable" if nifty.get("percent_change") is None else "Bullish" if nifty["percent_change"] > 0.2 else "Bearish" if nifty["percent_change"] < -0.2 else "Neutral"
            },
            "sensex": {
                "price": sensex.get("current_price"),
                "change": sensex.get("change"),
                "percent_change": sensex.get("percent_change"),
            },
            "sector_index": {
                "name": "NIFTY Auto Index" if "CNXAUTO" in sector_symbol else "NIFTY Bank Index" if "NSEBANK" in sector_symbol else "NIFTY IT Index",
                "symbol": sector_symbol,
                "price": sector_quote.get("current_price"),
                "percent_change": sector_quote.get("percent_change")
            }
        }
