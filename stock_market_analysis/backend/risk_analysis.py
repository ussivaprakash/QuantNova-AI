"""
Stage 9: Risk Analysis Module.
Calculates Risk Score (0-100), Reward/Risk Ratio, ATR Stop Loss, Target Price,
and Suggested Portfolio Position Size (Kelly Criterion / ATR Allocation).
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


def analyze_risk_metrics(data: pd.DataFrame, portfolio_value: float = 100000.0) -> Dict[str, Any]:
    """
    Computes risk score, ATR stop-loss, target price, reward-to-risk ratio,
    and recommended portfolio position sizing.
    """
    latest = data.iloc[-1]
    close_price = float(latest["Close"])
    atr = float(latest.get("ATR (14)", close_price * 0.025))
    volatility = float(latest.get("Rolling Volatility (20D Ann %)", 22.0))

    # Stop Loss & Target Price Calculation based on ATR & Technical Levels
    stop_loss = round(close_price - (1.75 * atr), 2)
    target_price = round(close_price + (2.75 * atr), 2)

    risk_per_share = abs(close_price - stop_loss)
    reward_per_share = abs(target_price - close_price)

    r2r_ratio = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 1.57

    # Risk Score Calculation (0-100)
    risk_score = 30.0
    if volatility > 35.0:
        risk_score += 35.0
    elif volatility > 25.0:
        risk_score += 20.0
    else:
        risk_score += 10.0

    if "BB Bandwidth" in data.columns and float(latest.get("BB Bandwidth", 0)) > 0.15:
        risk_score += 15.0

    if "ADX (14)" in data.columns and float(latest.get("ADX (14)", 0)) < 18.0:
        risk_score += 15.0  # Choppy/unclear trend risk

    final_risk_score = int(min(max(risk_score, 15), 95))

    # Position Sizing (Fixed 2% Risk Allocation Rule)
    max_portfolio_risk = portfolio_value * 0.02  # 2% max portfolio drawdown risk
    recommended_shares = int(max_portfolio_risk / risk_per_share) if risk_per_share > 0 else 10
    total_position_cost = round(recommended_shares * close_price, 2)
    position_pct = round((total_position_cost / portfolio_value) * 100.0, 1)

    if final_risk_score >= 70:
        risk_category = "High Risk"
    elif final_risk_score >= 45:
        risk_category = "Moderate Risk"
    else:
        risk_category = "Low Risk"

    return {
        "Risk Score": final_risk_score,
        "Risk Category": risk_category,
        "Annualized Volatility (%)": round(volatility, 2),
        "Suggested Entry Price (₹)": close_price,
        "Suggested Stop Loss (₹)": stop_loss,
        "Suggested Target Price (₹)": target_price,
        "Risk-to-Reward Ratio": f"1:{r2r_ratio}",
        "Reward per Share (₹)": round(reward_per_share, 2),
        "Risk per Share (₹)": round(risk_per_share, 2),
        "Recommended Shares": recommended_shares,
        "Suggested Position Value (₹)": total_position_cost,
        "Suggested Portfolio Size (%)": position_pct,
    }
