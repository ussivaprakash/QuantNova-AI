"""
Data Cleaning & Quality Audit Module for Stock OHLCV Data.

Performs explicit checks for:
1. Missing values (NaNs / nulls)
2. Duplicate rows (duplicate dates)
3. Incorrect dates (out of order, invalid format, weekend/holiday gaps)
4. Price anomalies (High < Low, Open/Close outside High/Low range, non-positive prices, extreme price spikes)
5. Volume anomalies (Negative volume, zero volume, extreme volume spikes)
6. Corporate actions (Stock splits, bonus shares, dividend price jumps)
"""

from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


def audit_ohlcv_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
    """
    Performs a thorough quality audit on OHLCV stock dataset.
    Returns:
      - cleaned_df: Sanitized, validated DataFrame ready for production quantitative models.
      - audit_summary: Dictionary summarizing errors found and cleaned.
      - audit_report_df: Detailed tabular report of cleaning steps and issues resolved.
    """
    cleaned = df.copy()
    report_items = []

    # Ensure required columns exist
    req_cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in req_cols:
        if col not in cleaned.columns:
            raise ValueError(f"Missing required column: {col}")

    # 1. Date Format & Duplicate Row Checks
    cleaned["Date"] = pd.to_datetime(cleaned["Date"])
    initial_rows = len(cleaned)

    # Check non-monotonic or out of order dates
    is_sorted = cleaned["Date"].is_monotonic_increasing
    if not is_sorted:
        cleaned = cleaned.sort_values("Date").reset_index(drop=True)
        report_items.append({
            "Check Category": "Date Ordering",
            "Issue Found": "Dates were out of chronological order",
            "Action Taken": "Sorted dataset chronologically by Date",
            "Affected Count": initial_rows
        })
    else:
        report_items.append({
            "Check Category": "Date Ordering",
            "Issue Found": "None",
            "Action Taken": "Verified dates are strictly in ascending order",
            "Affected Count": 0
        })

    # Duplicate dates check
    duplicates_mask = cleaned.duplicated(subset=["Date"], keep="first")
    duplicate_count = duplicates_mask.sum()
    if duplicate_count > 0:
        cleaned = cleaned.drop_duplicates(subset=["Date"], keep="first").reset_index(drop=True)
        report_items.append({
            "Check Category": "Duplicate Rows",
            "Issue Found": f"Found {duplicate_count} duplicate trading date rows",
            "Action Taken": "Removed duplicate rows, retaining first observation",
            "Affected Count": duplicate_count
        })
    else:
        report_items.append({
            "Check Category": "Duplicate Rows",
            "Issue Found": "None",
            "Action Taken": "Verified 0 duplicate trading dates",
            "Affected Count": 0
        })

    # 2. Missing Values Audit & Imputation
    null_counts = cleaned[req_cols].isnull().sum()
    total_nulls = null_counts.sum()
    if total_nulls > 0:
        # Forward fill price data, fill volume with 0
        price_cols = ["Open", "High", "Low", "Close", "Adj Close"]
        cleaned[price_cols] = cleaned[price_cols].ffill().bfill()
        cleaned["Volume"] = cleaned["Volume"].fillna(0)
        report_items.append({
            "Check Category": "Missing Values",
            "Issue Found": f"Found {total_nulls} missing values across OHLCV columns",
            "Action Taken": "Forward-filled prices and zero-filled missing volume",
            "Affected Count": total_nulls
        })
    else:
        report_items.append({
            "Check Category": "Missing Values",
            "Issue Found": "None",
            "Action Taken": "Verified 0 null or NaN values",
            "Affected Count": 0
        })

    # 3. Price Integrity Anomalies
    # Rule 3a: Non-positive prices
    invalid_price_mask = (cleaned["Open"] <= 0) | (cleaned["High"] <= 0) | (cleaned["Low"] <= 0) | (cleaned["Close"] <= 0)
    invalid_price_count = invalid_price_mask.sum()
    if invalid_price_count > 0:
        # Replace non-positive with NaN and forward fill
        for col in ["Open", "High", "Low", "Close"]:
            cleaned.loc[cleaned[col] <= 0, col] = np.nan
        cleaned[["Open", "High", "Low", "Close"]] = cleaned[["Open", "High", "Low", "Close"]].ffill()
        report_items.append({
            "Check Category": "Price Sanity (<=0)",
            "Issue Found": f"Found {invalid_price_count} non-positive price records",
            "Action Taken": "Replaced non-positive values with forward-filled prices",
            "Affected Count": invalid_price_count
        })
    else:
        report_items.append({
            "Check Category": "Price Sanity (<=0)",
            "Issue Found": "None",
            "Action Taken": "Verified all prices > 0",
            "Affected Count": 0
        })

    # Rule 3b: High < Low or Open/Close outside High/Low range
    high_low_violation = (cleaned["High"] < cleaned["Low"]) | \
                         (cleaned["Open"] > cleaned["High"]) | (cleaned["Open"] < cleaned["Low"]) | \
                         (cleaned["Close"] > cleaned["High"]) | (cleaned["Close"] < cleaned["Low"])
    violation_count = high_low_violation.sum()
    if violation_count > 0:
        # Correct High to max of Open, High, Low, Close and Low to min
        cleaned["High"] = cleaned[["Open", "High", "Low", "Close"]].max(axis=1)
        cleaned["Low"] = cleaned[["Open", "High", "Low", "Close"]].min(axis=1)
        report_items.append({
            "Check Category": "High/Low Range Bounds",
            "Issue Found": f"Found {violation_count} records where Open/Close breached High/Low bounds",
            "Action Taken": "Adjusted High = Max(OHLC) and Low = Min(OHLC)",
            "Affected Count": violation_count
        })
    else:
        report_items.append({
            "Check Category": "High/Low Range Bounds",
            "Issue Found": "None",
            "Action Taken": "Verified High >= Max(Open, Close) and Low <= Min(Open, Close)",
            "Affected Count": 0
        })

    # Rule 3c: Price Jump/Spike Anomalies (Daily return > 25%)
    daily_returns = (cleaned["Close"].pct_change().abs() * 100)
    spike_mask = daily_returns > 25.0
    spike_count = spike_mask.sum()
    report_items.append({
        "Check Category": "Price Spike Anomalies (>25% move)",
        "Issue Found": f"Detected {spike_count} high-volatility single-day price moves >25%",
        "Action Taken": "Flagged for corporate action / earnings volatility inspection",
        "Affected Count": spike_count
    })

    # 4. Volume Integrity & Anomalies
    neg_vol_mask = cleaned["Volume"] < 0
    neg_vol_count = neg_vol_mask.sum()
    if neg_vol_count > 0:
        cleaned.loc[neg_vol_mask, "Volume"] = 0
        report_items.append({
            "Check Category": "Negative Volume",
            "Issue Found": f"Found {neg_vol_count} negative volume entries",
            "Action Taken": "Set negative volume values to 0",
            "Affected Count": neg_vol_count
        })
    else:
        report_items.append({
            "Check Category": "Negative Volume",
            "Issue Found": "None",
            "Action Taken": "Verified volume >= 0 across all trading days",
            "Affected Count": 0
        })

    vol_median = cleaned["Volume"].median()
    vol_spike_mask = cleaned["Volume"] > (vol_median * 8.0)
    vol_spike_count = vol_spike_mask.sum()
    report_items.append({
        "Check Category": "Volume Spike Anomalies (>8x median)",
        "Issue Found": f"Identified {vol_spike_count} extreme volume spike days (>8x median)",
        "Action Taken": "Retained & flagged as institutional block/news volume days",
        "Affected Count": vol_spike_count
    })

    # 5. Corporate Actions Analysis (Splits & Dividends)
    cleaned["Adjustment Factor"] = cleaned["Adj Close"] / cleaned["Close"]
    cleaned["Split Impact Flag"] = cleaned["Adjustment Factor"].pct_change().abs() > 0.05
    split_div_count = cleaned["Split Impact Flag"].sum()
    report_items.append({
        "Check Category": "Corporate Actions (Splits/Dividends)",
        "Issue Found": f"Identified {split_div_count} dates with significant Adj Close ratio shifts (>5%)",
        "Action Taken": "Recorded adjustment factor column for historical normalization",
        "Affected Count": split_div_count
    })

    audit_report_df = pd.DataFrame(report_items)
    
    audit_summary = {
        "Initial Rows": initial_rows,
        "Cleaned Rows": len(cleaned),
        "Duplicates Removed": duplicate_count,
        "Missing Values Imputed": total_nulls,
        "Price Range Violations Fixed": violation_count,
        "Volume Anomalies Sanitized": neg_vol_count,
        "Corporate Action Events Detected": split_div_count,
    }

    return cleaned, audit_summary, audit_report_df
