"""
Stage 6: Market Context Analysis Module.
Analyzes broader market environment, Nifty 50 benchmark performance (^NSEI),
sector momentum, volatility, and relative strength (RS) rating.
"""

from typing import Dict, Any
import time
import yfinance as yf
import pandas as pd

BENCHMARK_CACHE_TTL_SECONDS = 300
_benchmark_cache = {}


def _load_benchmark_history(symbol: str):
    cached = _benchmark_cache.get(symbol)
    now = time.monotonic()
    if cached and now - cached[0] < BENCHMARK_CACHE_TTL_SECONDS:
        return cached[1].copy(), True
    history = yf.Ticker(symbol).history(period="6mo", timeout=15)
    if not history.empty:
        _benchmark_cache[symbol] = (now, history.copy())
    return history, False


def analyze_market_context(stock_df: pd.DataFrame, benchmark_symbol: str = "^NSEI") -> Dict[str, Any]:
    """
    Evaluates broader market environment, benchmark trend, volatility, and relative strength.
    """
    provider_error = None
    benchmark_cache_hit = False
    try:
        nifty_df, benchmark_cache_hit = _load_benchmark_history(benchmark_symbol)
    except Exception as exc:
        nifty_df = pd.DataFrame()
        provider_error = type(exc).__name__

    if nifty_df.empty or len(nifty_df) < 20:
        nifty_return_1m = None
        nifty_trend = "Unavailable"
        relative_strength = None
    else:
        nifty_close = nifty_df["Close"]
        nifty_return_1m = round(((nifty_close.iloc[-1] - nifty_close.iloc[-20]) / nifty_close.iloc[-20]) * 100.0, 2)
        if len(nifty_close) >= 50:
            nifty_ma50 = nifty_close.rolling(50).mean().iloc[-1]
            if nifty_close.iloc[-1] > nifty_ma50:
                nifty_trend = "Bullish Uptrend (Above 50 MA)"
            else:
                nifty_trend = "Bearish Correction (Below 50 MA)"
        else:
            nifty_trend = "Unavailable (fewer than 50 sessions)"

        # Relative Strength vs Nifty over 1 Month
        stock_close = stock_df["Close"]
        if len(stock_close) >= 20:
            stock_return_1m = ((stock_close.iloc[-1] - stock_close.iloc[-20]) / stock_close.iloc[-20]) * 100.0
            rs_diff = stock_return_1m - nifty_return_1m
            relative_strength = round(min(max(50.0 + (rs_diff * 2.0), 10.0), 99.0), 1)
        else:
            relative_strength = None

    volatility_state = "Unavailable"
    if "Rolling Volatility (20D Ann %)" in stock_df.columns:
        curr_vol = stock_df["Rolling Volatility (20D Ann %)"].iloc[-1]
        if pd.isna(curr_vol):
            volatility_state = "Unavailable (insufficient price history)"
        elif curr_vol > 35.0:
            volatility_state = f"High Volatility ({curr_vol:.1f}%)"
        elif curr_vol < 18.0:
            volatility_state = f"Low Volatility ({curr_vol:.1f}%)"
        else:
            volatility_state = f"Moderate Volatility ({curr_vol:.1f}%)"

    market_explanation = (
        f"The broader Nifty 50 benchmark index ({benchmark_symbol}) is currently exhibiting a {nifty_trend} "
        f"with a 1-month return of {nifty_return_1m}%. The stock displays a Relative Strength (RS) rating of "
        f"{relative_strength}/99 against the benchmark under {volatility_state} market conditions."
    )

    return {
        "Benchmark Symbol": benchmark_symbol,
        "Nifty 1M Return (%)": nifty_return_1m,
        "Nifty Market Trend": nifty_trend,
        "Relative Strength Rating": relative_strength,
        "Market Volatility State": volatility_state,
        "Market Context Explanation": market_explanation if nifty_return_1m is not None else (
            "Benchmark context is unavailable because Yahoo Finance returned insufficient NIFTY 50 history."
            + (f" Provider request failed ({provider_error})." if provider_error else "")
        ),
        "Data Status": "available" if nifty_return_1m is not None else "unavailable",
        "Data Source": "Yahoo Finance",
        "Benchmark Cache Hit": benchmark_cache_hit,
    }
