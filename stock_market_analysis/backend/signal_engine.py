"""
Stage 5: Buy / Hold / Sell Signal Engine Module.

Synthesizes:
1. Trend Analysis (Regime & Classification)
2. Technical Indicators (SMA/EMA, RSI, MACD, BB, ATR, ADX, VWAP, OBV, Stochastic)
3. Machine Learning Prediction (Random Forest Forecast Probabilities)

Outputs:
- Signal (BUY, HOLD, SELL)
- Confidence Score (%)
- Risk Level (Low Risk, Moderate Risk, High Risk)
- Reason for Decision (Detailed multi-factor justification)
- Suggested Stop Loss (₹)
- Suggested Target Price (₹)
"""

import pandas as pd
import numpy as np


def generate_buy_hold_sell_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master Decision Engine combining Trend Analysis, Technical Indicators, and ML Model Forecasts.
    Computes precise Stop-Loss and Target Price levels using Average True Range (ATR).
    """
    signals = []
    confidence_scores = []
    risk_levels = []
    reasons_list = []
    stop_losses = []
    target_prices = []
    action_plans = []

    for idx, row in df.iterrows():
        close = row["Close"]
        atr = row.get("ATR (14)", close * 0.02)  # Fallback to 2% if ATR not available
        if pd.isna(atr) or atr <= 0:
            atr = close * 0.02

        # Check for initial warmup rows
        req = [row.get("SMA 20", row.get("20-Day MA")), row.get("RSI (14)"), row.get("MACD")]
        if any(pd.isna(v) for v in req):
            signals.append("HOLD / WAIT")
            confidence_scores.append(0)
            risk_levels.append("High Risk")
            reasons_list.append("Indicator windows initializing.")
            stop_losses.append(round(close - (1.5 * atr), 2))
            target_prices.append(round(close + (1.5 * atr), 2))
            action_plans.append("Wait for indicator windows to fill.")
            continue

        reasons = []
        score = 0.0

        # --- Component 1: Trend Analysis (Weight: 35%) ---
        trend_class = str(row.get("Trend Classification", row.get("Trend Regime", "")))

        if "Strong Bullish" in trend_class:
            score += 3.5
            reasons.append("Trend: Strong Bullish alignment")
        elif "Bullish" in trend_class:
            score += 2.0
            reasons.append("Trend: Bullish structure")
        elif "Strong Bearish" in trend_class:
            score -= 3.5
            reasons.append("Trend: Strong Bearish alignment")
        elif "Bearish" in trend_class:
            score -= 2.0
            reasons.append("Trend: Bearish structure")
        else:
            reasons.append("Trend: Sideways / Consolidation")

        # --- Component 2: Technical Indicators (Weight: 35%) ---
        rsi = row["RSI (14)"]
        macd_hist = row.get("MACD Histogram", 0.0)
        stoch_k = row.get("Stoch %K", 50.0)
        adx = row.get("ADX (14)", 15.0)
        pos_di = row.get("+DI", 0.0)
        neg_di = row.get("-DI", 0.0)
        vwap = row.get("VWAP", close)

        if rsi >= 55:
            score += 1.25
            reasons.append(f"RSI bullish ({rsi:.1f})")
        elif rsi <= 45:
            score -= 1.25
            reasons.append(f"RSI bearish ({rsi:.1f})")

        if macd_hist > 0:
            score += 1.25
            reasons.append("MACD histogram positive")
        elif macd_hist < 0:
            score -= 1.25
            reasons.append("MACD histogram negative")

        if close > vwap:
            score += 0.5
            reasons.append("Price above VWAP")
        elif close < vwap:
            score -= 0.5
            reasons.append("Price below VWAP")

        if not pd.isna(stoch_k):
            if stoch_k <= 20:
                score += 0.5
                reasons.append(f"Stochastic oversold ({stoch_k:.1f})")
            elif stoch_k >= 80:
                score -= 0.5
                reasons.append(f"Stochastic overbought ({stoch_k:.1f})")

        # --- Component 3: Machine Learning Model (Weight: 30%) ---
        ml_prob = row.get("ML Bull Prob (%)", 50.0)
        if ml_prob >= 60.0:
            score += 3.0
            reasons.append(f"ML Model: Bullish forecast ({ml_prob:.1f}% prob)")
        elif ml_prob <= 40.0:
            score -= 3.0
            reasons.append(f"ML Model: Bearish forecast ({ml_prob:.1f}% prob)")

        # --- Confidence Calculation ---
        confidence = min(max(int((abs(score) / 9.5) * 100), 20), 95)
        confidence_scores.append(confidence)

        # --- Signal Determination & Levels ---
        volatility_ratio = (atr / close) * 100.0  # Daily volatility %

        if score >= 3.5:
            signal = "BUY"
            action = "Strong Buy setup confirmed by Trend, Momentum, and ML Model."
            stop_loss = round(close - (1.5 * atr), 2)
            target_price = round(close + (2.5 * atr), 2)  # 1:1.67 Risk-to-Reward
            risk = "Low Risk" if (confidence >= 65 and volatility_ratio < 3.0) else "Moderate Risk"
        elif score >= 1.5:
            signal = "BUY"
            action = "Moderate Buy setup; enter with standard risk limits."
            stop_loss = round(close - (1.5 * atr), 2)
            target_price = round(close + (2.0 * atr), 2)
            risk = "Moderate Risk"
        elif score <= -3.5:
            signal = "SELL"
            action = "Strong Sell / Exit setup; protect capital and trim positions."
            stop_loss = round(close + (1.5 * atr), 2)
            target_price = round(close - (2.5 * atr), 2)
            risk = "Low Risk" if (confidence >= 65 and volatility_ratio < 3.0) else "Moderate Risk"
        elif score <= -1.5:
            signal = "SELL"
            action = "Moderate Sell / Caution setup; consider tightening stops."
            stop_loss = round(close + (1.5 * atr), 2)
            target_price = round(close - (2.0 * atr), 2)
            risk = "Moderate Risk"
        else:
            signal = "HOLD / WAIT"
            action = "No clear directional edge; hold current stance or await breakout."
            stop_loss = round(close - (1.2 * atr), 2)
            target_price = round(close + (1.2 * atr), 2)
            risk = "High Risk" if volatility_ratio > 4.0 else "Moderate Risk"

        signals.append(signal)
        risk_levels.append(risk)
        reasons_list.append("; ".join(reasons))
        stop_losses.append(stop_loss)
        target_prices.append(target_price)
        action_plans.append(action)

    res = df.copy()
    res["Signal Category"] = signals
    res["Signal"] = signals
    res["Signal Confidence (%)"] = confidence_scores
    res["Risk Level"] = risk_levels
    res["Reason for Decision"] = reasons_list
    res["Signal Justification"] = reasons_list  # Alias
    res["Suggested Stop Loss (₹)"] = stop_losses
    res["Suggested Target Price (₹)"] = target_prices
    res["Signal Action Plan"] = action_plans

    # Technical Score (0-100)
    res["Technical Score"] = res.apply(
        lambda r: int(min(max(50 + (
            (15 if "Bullish" in str(r.get("Trend Classification", "")) else -15 if "Bearish" in str(r.get("Trend Classification", "")) else 0) +
            (10 if r.get("RSI (14)", 50) > 55 else -10 if r.get("RSI (14)", 50) < 45 else 0) +
            (10 if r.get("MACD Histogram", 0) > 0 else -10) +
            (10 if r.get("Close", 0) > r.get("SMA 50", 0) else -10)
        ), 10), 98)), axis=1
    )

    return res
