"""
Stage 3: Trend Analysis Module.
Performs 5-tier market trend classification (Strong Bullish, Bullish, Sideways, Bearish, Strong Bearish)
and generates human-readable explanations for every trading day.
"""

import pandas as pd
import numpy as np


def analyze_trend_regime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates market trend using a multi-factor quantitative scoring matrix:
    - Strong Bullish (Net Score >= +4)
    - Bullish (Net Score +2 to +3)
    - Sideways (Net Score -1 to +1)
    - Bearish (Net Score -3 to -2)
    - Strong Bearish (Net Score <= -4)

    Generates explicit reasons for every single trading day.
    """
    trend_labels = []
    trend_scores = []
    trend_reasons = []
    ma_slopes = []

    # Calculate 5-day percentage slope of SMA 20
    sma20_col = "SMA 20" if "SMA 20" in df.columns else "20-Day MA"
    ma20_slope = (df[sma20_col] - df[sma20_col].shift(5)) / df[sma20_col].shift(5) * 100.0

    for i, (idx, row) in enumerate(df.iterrows()):
        price = row["Close"]
        ma20 = row.get(sma20_col, np.nan)
        ma50 = row.get("SMA 50", row.get("50-Day MA", np.nan))
        ma200 = row.get("SMA 200", np.nan)
        slope = ma20_slope.iloc[i]

        rsi = row.get("RSI (14)", np.nan)
        macd = row.get("MACD", np.nan)
        macd_sig = row.get("MACD Signal", np.nan)
        macd_hist = row.get("MACD Histogram", np.nan)
        adx = row.get("ADX (14)", np.nan)
        pos_di = row.get("+DI", np.nan)
        neg_di = row.get("-DI", np.nan)

        if pd.isna(ma20) or pd.isna(rsi):
            trend_labels.append("Sideways")
            trend_scores.append(0)
            trend_reasons.append("Warming up indicator calculation windows.")
            ma_slopes.append(np.nan)
            continue

        ma_slopes.append(slope)
        bull_reasons = []
        bear_reasons = []
        score = 0

        # --- Factor 1: Moving Average Alignment ---
        if price > ma20:
            score += 1
            bull_reasons.append("Price above 20-MA")
        else:
            score -= 1
            bear_reasons.append("Price below 20-MA")

        if not pd.isna(ma50):
            if ma20 > ma50:
                score += 1
                bull_reasons.append("20-MA above 50-MA")
            else:
                score -= 1
                bear_reasons.append("20-MA below 50-MA")

        if not pd.isna(ma200):
            if ma50 > ma200:
                score += 1
                bull_reasons.append("Golden Alignment (50-MA above 200-MA)")
            else:
                score -= 1
                bear_reasons.append("Death Alignment (50-MA below 200-MA)")

        # --- Factor 2: MA Slope ---
        if not pd.isna(slope):
            if slope > 0.5:
                score += 1
                bull_reasons.append(f"20-MA rising (+{slope:.2f}%)")
            elif slope < -0.5:
                score -= 1
                bear_reasons.append(f"20-MA falling ({slope:.2f}%)")

        # --- Factor 3: ADX & Directional Indicators ---
        if not pd.isna(adx) and not pd.isna(pos_di) and not pd.isna(neg_di):
            if adx >= 20 and pos_di > neg_di:
                score += 1
                bull_reasons.append(f"ADX confirms uptrend (+DI > -DI, ADX={adx:.1f})")
            elif adx >= 20 and neg_di > pos_di:
                score -= 1
                bear_reasons.append(f"ADX confirms downtrend (-DI > +DI, ADX={adx:.1f})")

        # --- Factor 4: Momentum (RSI & MACD) ---
        if rsi >= 55:
            score += 1
            bull_reasons.append(f"RSI bullish ({rsi:.1f})")
        elif rsi <= 45:
            score -= 1
            bear_reasons.append(f"RSI bearish ({rsi:.1f})")

        if not pd.isna(macd) and not pd.isna(macd_sig) and macd > macd_sig and macd_hist > 0:
            score += 1
            bull_reasons.append("MACD bullish crossover")
        elif not pd.isna(macd) and not pd.isna(macd_sig) and macd < macd_sig and macd_hist < 0:
            score -= 1
            bear_reasons.append("MACD bearish crossover")

        # Classification Mapping
        if score >= 4:
            classification = "Strong Bullish"
            primary_reasons = bull_reasons
        elif score >= 2:
            classification = "Bullish"
            primary_reasons = bull_reasons
        elif score <= -4:
            classification = "Strong Bearish"
            primary_reasons = bear_reasons
        elif score <= -2:
            classification = "Bearish"
            primary_reasons = bear_reasons
        else:
            classification = "Sideways"
            primary_reasons = bull_reasons if score >= 0 else bear_reasons

        trend_labels.append(classification)
        trend_scores.append(score)
        reason_str = "; ".join(primary_reasons) if primary_reasons else "Indicators balanced in neutral range."
        trend_reasons.append(reason_str)

    res = df.copy()
    res["Trend Classification"] = trend_labels
    res["Trend Regime"] = trend_labels  # Alias for backward compatibility
    res["Trend Score"] = trend_scores
    res["Trend Reason"] = trend_reasons
    res["MA20 Slope (%)"] = ma_slopes

    return res
