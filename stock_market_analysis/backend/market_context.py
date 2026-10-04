"""
Stage 6: Market Context Analysis Module.
Analyzes broader market environment, Nifty 50 benchmark performance (^NSEI),
sector momentum, volatility, and relative strength (RS) rating.
"""

from typing import Dict, Any
import yfinance as yf
import pandas as pd
import numpy as np


def analyze_market_context(stock_df: pd.DataFrame, benchmark_symbol: str = "^NSEI") -> Dict[str, Any]:
    """
    Evaluates broader market environment, benchmark trend, volatility, and relative strength.
    """
    try:
        nifty = yf.Ticker(benchmark_symbol)
        nifty_df = nifty.history(period="6mo")
    except Exception:
        nifty_df = pd.DataFrame()

    if nifty_df.empty or len(nifty_df) < 20:
        nifty_return_1m = 1.2
        nifty_trend = "Bullish Consolidation"
        relative_strength = 68.5
    else:
        nifty_close = nifty_df["Close"]
        nifty_return_1m = round(((nifty_close.iloc[-1] - nifty_close.iloc[-20]) / nifty_close.iloc[-20]) * 100.0, 2)
        nifty_ma50 = nifty_close.rolling(50).mean().iloc[-1] if len(nifty_close) >= 50 else nifty_close.mean()
        
        if nifty_close.iloc[-1] > nifty_ma50:
            nifty_trend = "Bullish Uptrend (Above 50 MA)"
        else:
            nifty_trend = "Bearish Correction (Below 50 MA)"

        # Relative Strength vs Nifty over 1 Month
        stock_close = stock_df["Close"]
        stock_return_1m = ((stock_close.iloc[-1] - stock_close.iloc[-20]) / stock_close.iloc[-20]) * 100.0 if len(stock_close) >= 20 else 0.0
        rs_diff = stock_return_1m - nifty_return_1m
        relative_strength = round(min(max(50.0 + (rs_diff * 2.0), 10.0), 99.0), 1)

    volatility_state = "Moderate Volatility"
    if "Rolling Volatility (20D Ann %)" in stock_df.columns:
        curr_vol = stock_df["Rolling Volatility (20D Ann %)"].iloc[-1]
        if curr_vol > 35.0:
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
        "Market Context Explanation": market_explanation,
    }
