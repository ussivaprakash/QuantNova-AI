"""
Stage 7: Backtesting Module.
Executes an event-driven backtest of the Quantitative Signal Engine against historical data.

Calculates:
- Total Return (%)
- CAGR (%)
- Win Rate (%)
- Sharpe Ratio
- Maximum Drawdown (%)
- Number of Trades
- Average Profit (%)
- Average Loss (%)
- Comparison against Benchmark Buy-and-Hold strategy
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def run_strategy_backtest(df: pd.DataFrame, initial_capital: float = 100000.0) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Backtests the Buy/Hold/Sell signal strategy on historical data vs Buy-and-Hold benchmark.
    Returns:
      - backtest_df: Original DataFrame with daily equity curves and trade logs.
      - metrics_summary: Dictionary comparing Strategy vs Buy-and-Hold.
      - trade_log_df: Tabular log of all individual trades executed.
    """
    data = df.copy()

    # Determine daily position signal: 1.0 for BUY, 0.0 for HOLD/SELL
    position = np.where(data["Signal"].str.startswith("BUY"), 1.0, 0.0)
    data["Position"] = pd.Series(position, index=data.index).shift(1).fillna(0.0)  # Shifted to prevent lookahead

    # Daily Returns (Decimal)
    daily_ret = data["Close"].pct_change().fillna(0.0)
    data["Benchmark Daily Ret"] = daily_ret
    data["Strategy Daily Ret"] = data["Position"] * daily_ret

    # Equity Curves
    data["Benchmark Equity"] = initial_capital * (1.0 + data["Benchmark Daily Ret"]).cumprod()
    data["Strategy Equity"] = initial_capital * (1.0 + data["Strategy Daily Ret"]).cumprod()

    # Track Individual Trades
    trades = []
    in_trade = False
    entry_date = None
    entry_price = 0.0
    entry_idx = 0

    for i in range(1, len(data)):
        prev_pos = data["Position"].iloc[i - 1]
        curr_pos = data["Position"].iloc[i]
        date = data["Date"].iloc[i]
        price = data["Close"].iloc[i]

        if prev_pos == 0.0 and curr_pos == 1.0:
            # Enter Long Trade
            in_trade = True
            entry_date = date
            entry_price = price
            entry_idx = i

        elif prev_pos == 1.0 and curr_pos == 0.0 and in_trade:
            # Exit Long Trade
            exit_date = date
            exit_price = price
            trade_return = (exit_price - entry_price) / entry_price * 100.0
            holding_days = i - entry_idx

            trades.append({
                "Trade #": len(trades) + 1,
                "Entry Date": entry_date,
                "Entry Price (₹)": round(entry_price, 2),
                "Exit Date": exit_date,
                "Exit Price (₹)": round(exit_price, 2),
                "Return (%)": round(trade_return, 2),
                "Holding Days": holding_days,
                "Result": "WIN" if trade_return > 0 else "LOSS",
            })
            in_trade = False

    # Close open trade at end if active
    if in_trade:
        exit_date = data["Date"].iloc[-1]
        exit_price = data["Close"].iloc[-1]
        trade_return = (exit_price - entry_price) / entry_price * 100.0
        holding_days = len(data) - 1 - entry_idx
        trades.append({
            "Trade #": len(trades) + 1,
            "Entry Date": entry_date,
            "Entry Price (₹)": round(entry_price, 2),
            "Exit Date": exit_date,
            "Exit Price (₹)": round(exit_price, 2),
            "Return (%)": round(trade_return, 2),
            "Holding Days": holding_days,
            "Result": "WIN" if trade_return > 0 else "LOSS",
        })

    trade_log_df = pd.DataFrame(trades)

    # --- Performance Metric Calculations ---
    n_days = len(data)
    n_years = n_days / 252.0 if n_days > 0 else 1.0

    # Strategy Metrics
    strat_total_return = (data["Strategy Equity"].iloc[-1] - initial_capital) / initial_capital * 100.0
    strat_cagr = ((data["Strategy Equity"].iloc[-1] / initial_capital) ** (1.0 / n_years) - 1.0) * 100.0 if n_years > 0 else strat_total_return
    
    strat_daily_std = data["Strategy Daily Ret"].std()
    strat_sharpe = (data["Strategy Daily Ret"].mean() * np.sqrt(252)) / strat_daily_std if strat_daily_std > 0 else 0.0

    strat_peak = data["Strategy Equity"].cummax()
    strat_drawdown = (strat_peak - data["Strategy Equity"]) / strat_peak * 100.0
    strat_max_dd = strat_drawdown.max()

    # Benchmark Metrics
    bm_total_return = (data["Benchmark Equity"].iloc[-1] - initial_capital) / initial_capital * 100.0
    bm_cagr = ((data["Benchmark Equity"].iloc[-1] / initial_capital) ** (1.0 / n_years) - 1.0) * 100.0 if n_years > 0 else bm_total_return
    
    bm_daily_std = data["Benchmark Daily Ret"].std()
    bm_sharpe = (data["Benchmark Daily Ret"].mean() * np.sqrt(252)) / bm_daily_std if bm_daily_std > 0 else 0.0

    bm_peak = data["Benchmark Equity"].cummax()
    bm_drawdown = (bm_peak - data["Benchmark Equity"]) / bm_peak * 100.0
    bm_max_dd = bm_drawdown.max()

    # Trade Metrics
    num_trades = len(trade_log_df)
    if num_trades > 0:
        wins = trade_log_df[trade_log_df["Result"] == "WIN"]
        losses = trade_log_df[trade_log_df["Result"] == "LOSS"]
        win_rate = (len(wins) / num_trades) * 100.0
        avg_profit = wins["Return (%)"].mean() if not wins.empty else 0.0
        avg_loss = losses["Return (%)"].mean() if not losses.empty else 0.0
    else:
        win_rate = 0.0
        avg_profit = 0.0
        avg_loss = 0.0

    metrics_summary = {
        "Metric": [
            "Total Return (%)",
            "CAGR (%)",
            "Win Rate (%)",
            "Sharpe Ratio",
            "Maximum Drawdown (%)",
            "Number of Trades",
            "Average Profit (%)",
            "Average Loss (%)",
            "Initial Capital (₹)",
            "Final Portfolio Value (₹)"
        ],
        "Quantitative Signal Strategy": [
            f"{strat_total_return:.2f}%",
            f"{strat_cagr:.2f}%",
            f"{win_rate:.2f}%",
            f"{strat_sharpe:.2f}",
            f"{strat_max_dd:.2f}%",
            f"{num_trades}",
            f"{avg_profit:.2f}%",
            f"{avg_loss:.2f}%",
            f"₹{initial_capital:,.2f}",
            f"₹{data['Strategy Equity'].iloc[-1]:,.2f}"
        ],
        "Buy-and-Hold Benchmark": [
            f"{bm_total_return:.2f}%",
            f"{bm_cagr:.2f}%",
            "N/A (1 Buy Trade)",
            f"{bm_sharpe:.2f}",
            f"{bm_max_dd:.2f}%",
            "1",
            "N/A",
            "N/A",
            f"₹{initial_capital:,.2f}",
            f"₹{data['Benchmark Equity'].iloc[-1]:,.2f}"
        ]
    }

    metrics_df = pd.DataFrame(metrics_summary)
    return data, metrics_df, trade_log_df
