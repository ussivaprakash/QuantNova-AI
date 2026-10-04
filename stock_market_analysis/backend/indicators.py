"""
Stage 2: Technical Indicators Module.
Calculates professional technical indicators for trend, momentum, volatility, volume, and oscillator analysis.
"""

import pandas as pd
import numpy as np
from data_loader import PipelineConfig


def calculate_daily_return(data: pd.DataFrame) -> pd.Series:
    """Percentage daily price return based on Close."""
    return data["Close"].pct_change() * 100.0


def calculate_rolling_volatility(data: pd.DataFrame, window: int = 20) -> pd.Series:
    """20-Day Annualized Rolling Volatility (%)."""
    daily_returns = data["Close"].pct_change()
    rolling_std = daily_returns.rolling(window=window).std()
    return rolling_std * np.sqrt(252) * 100.0


def calculate_smas(data: pd.DataFrame) -> pd.DataFrame:
    """Simple Moving Averages for 20, 50, 100, and 200 days."""
    return pd.DataFrame({
        "SMA 20": data["Close"].rolling(window=20).mean(),
        "SMA 50": data["Close"].rolling(window=50).mean(),
        "SMA 100": data["Close"].rolling(window=100).mean(),
        "SMA 200": data["Close"].rolling(window=200).mean(),
    })


def calculate_emas(data: pd.DataFrame) -> pd.DataFrame:
    """Exponential Moving Averages for 20 and 50 days."""
    return pd.DataFrame({
        "EMA 20": data["Close"].ewm(span=20, adjust=False).mean(),
        "EMA 50": data["Close"].ewm(span=50, adjust=False).mean(),
    })


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Relative Strength Index (RSI) with exponential smoothing."""
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_macd(data: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Moving Average Convergence Divergence (MACD)."""
    fast_ema = data["Close"].ewm(span=config.macd_fast_span, adjust=False).mean()
    slow_ema = data["Close"].ewm(span=config.macd_slow_span, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=config.macd_signal_span, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame({
        "MACD": macd_line,
        "MACD Signal": signal_line,
        "MACD Histogram": histogram,
    })


def calculate_bollinger_bands(data: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Bollinger Bands (Upper Band, Middle Band, Lower Band, Bandwidth, %B)."""
    sma = data["Close"].rolling(window=config.bb_window).mean()
    std = data["Close"].rolling(window=config.bb_window).std()
    upper = sma + (std * config.bb_std_dev)
    lower = sma - (std * config.bb_std_dev)
    bandwidth = (upper - lower) / sma
    percent_b = (data["Close"] - lower) / (upper - lower).replace(0, np.nan)

    return pd.DataFrame({
        "BB Upper": upper,
        "BB Middle": sma,
        "BB Lower": lower,
        "BB Bandwidth": bandwidth,
        "BB %B": percent_b,
    })


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (ATR) measuring market volatility."""
    high_low = data["High"] - data["Low"]
    high_prev_close = (data["High"] - data["Close"].shift(1)).abs()
    low_prev_close = (data["Low"] - data["Close"].shift(1)).abs()

    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average Directional Index (ADX) with +DI and -DI."""
    df = data.copy()
    high_diff = df["High"].diff()
    low_diff = -df["Low"].diff()

    pos_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
    neg_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)

    tr = calculate_atr(df, period=1)
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    pos_di = 100 * pd.Series(pos_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / atr.replace(0, np.nan)
    neg_di = 100 * pd.Series(neg_dm, index=df.index).ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / atr.replace(0, np.nan)

    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    return pd.DataFrame({
        "+DI": pos_di,
        "-DI": neg_di,
        "ADX (14)": adx,
    })


def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price (VWAP)."""
    typical_price = (data["High"] + data["Low"] + data["Close"]) / 3.0
    tpv = typical_price * data["Volume"]
    cum_tpv = tpv.cumsum()
    cum_vol = data["Volume"].cumsum().replace(0, np.nan)
    return cum_tpv / cum_vol


def calculate_obv(data: pd.DataFrame) -> pd.Series:
    """On-Balance Volume (OBV)."""
    close_diff = data["Close"].diff()
    direction = np.where(close_diff > 0, 1, np.where(close_diff < 0, -1, 0))
    volume_flow = data["Volume"] * direction
    return volume_flow.cumsum()


def calculate_stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator (%K and %D)."""
    low_min = data["Low"].rolling(window=k_period).min()
    high_max = data["High"].rolling(window=k_period).max()

    stoch_k = 100 * ((data["Close"] - low_min) / (high_max - low_min).replace(0, np.nan))
    stoch_d = stoch_k.rolling(window=d_period).mean()

    return pd.DataFrame({
        "Stoch %K": stoch_k,
        "Stoch %D": stoch_d,
    })


def detect_price_gaps(data: pd.DataFrame) -> pd.DataFrame:
    """Detect Gap-Up and Gap-Down price actions."""
    prev_high = data["High"].shift(1)
    prev_low = data["Low"].shift(1)
    gap_up = data["Open"] > prev_high
    gap_down = data["Open"] < prev_low

    return pd.DataFrame({
        "Previous High": prev_high,
        "Previous Low": prev_low,
        "Gap Up": gap_up,
        "Gap Down": gap_down,
    })


def calculate_supertrend(data: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """SuperTrend Indicator calculating trend direction and dynamic trailing stop level."""
    atr = calculate_atr(data, period)
    hl2 = (data["High"] + data["Low"]) / 2.0

    basic_upper = (hl2 + (multiplier * atr)).values
    basic_lower = (hl2 - (multiplier * atr)).values
    close = data["Close"].values
    n = len(data)

    supertrend = np.zeros(n)
    direction = np.zeros(n, dtype=int)
    upper_band = np.copy(basic_upper)
    lower_band = np.copy(basic_lower)

    for i in range(1, n):
        if basic_upper[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
            upper_band[i] = basic_upper[i]
        else:
            upper_band[i] = upper_band[i-1]

        if basic_lower[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
            lower_band[i] = basic_lower[i]
        else:
            lower_band[i] = lower_band[i-1]

        if i == 1:
            direction[i] = 1 if close[i] > upper_band[i] else -1
        else:
            if direction[i-1] == 1 and close[i] < lower_band[i]:
                direction[i] = -1
            elif direction[i-1] == -1 and close[i] > upper_band[i]:
                direction[i] = 1
            else:
                direction[i] = direction[i-1]

        supertrend[i] = lower_band[i] if direction[i] == 1 else upper_band[i]

    return pd.DataFrame({
        "SuperTrend": pd.Series(supertrend, index=data.index),
        "SuperTrend Direction": pd.Series(direction, index=data.index),  # 1 = Bullish, -1 = Bearish
    })


def calculate_ichimoku(data: pd.DataFrame) -> pd.DataFrame:
    """Ichimoku Kinko Hyo Cloud (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span)."""
    tenkan_sen = (data["High"].rolling(window=9).max() + data["Low"].rolling(window=9).min()) / 2.0
    kijun_sen = (data["High"].rolling(window=26).max() + data["Low"].rolling(window=26).min()) / 2.0
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2.0).shift(26)
    senkou_span_b = ((data["High"].rolling(window=52).max() + data["Low"].rolling(window=52).min()) / 2.0).shift(26)
    chikou_span = data["Close"].shift(-26)

    return pd.DataFrame({
        "Tenkan-sen": tenkan_sen,
        "Kijun-sen": kijun_sen,
        "Senkou Span A": senkou_span_a,
        "Senkou Span B": senkou_span_b,
        "Chikou Span": chikou_span,
    })


def calculate_support_resistance(data: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Calculates Support & Resistance levels based on Pivot Points and Swing Highs/Lows."""
    pivot = (data["High"] + data["Low"] + data["Close"]) / 3.0
    r1 = (2 * pivot) - data["Low"]
    s1 = (2 * pivot) - data["High"]
    r2 = pivot + (data["High"] - data["Low"])
    s2 = pivot - (data["High"] - data["Low"])

    swing_resistance = data["High"].rolling(window=window).max()
    swing_support = data["Low"].rolling(window=window).min()

    return pd.DataFrame({
        "Pivot Point": pivot,
        "Resistance 1": r1,
        "Support 1": s1,
        "Resistance 2": r2,
        "Support 2": s2,
        "Swing Resistance": swing_resistance,
        "Swing Support": swing_support,
    })


def calculate_all_indicators(data: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Master function combining all professional Stage 2 Technical Indicators."""
    df = data.copy()

    # Returns & Volatility
    df["Daily Return (%)"] = calculate_daily_return(df)
    df["Rolling Volatility (20D Ann %)"] = calculate_rolling_volatility(df, 20)

    # Moving Averages (SMA & EMA)
    smas = calculate_smas(df)
    df["5-Day MA"] = df["Close"].rolling(window=5).mean()
    df["20-Day MA"] = smas["SMA 20"]

    df["50-Day MA"] = smas["SMA 50"]
    df["SMA 20"] = smas["SMA 20"]
    df["SMA 50"] = smas["SMA 50"]
    df["SMA 100"] = smas["SMA 100"]
    df["SMA 200"] = smas["SMA 200"]

    emas = calculate_emas(df)
    df["EMA 20"] = emas["EMA 20"]
    df["EMA 50"] = emas["EMA 50"]

    # Momentum & Trend
    df["RSI (14)"] = calculate_rsi(df, config.rsi_period)

    macd_df = calculate_macd(df, config)
    df["MACD"] = macd_df["MACD"]
    df["MACD Signal"] = macd_df["MACD Signal"]
    df["MACD Histogram"] = macd_df["MACD Histogram"]

    adx_df = calculate_adx(df, 14)
    df["+DI"] = adx_df["+DI"]
    df["-DI"] = adx_df["-DI"]
    df["ADX (14)"] = adx_df["ADX (14)"]

    stoch_df = calculate_stochastic(df, 14, 3)
    df["Stoch %K"] = stoch_df["Stoch %K"]
    df["Stoch %D"] = stoch_df["Stoch %D"]

    # SuperTrend & Ichimoku Cloud
    st_df = calculate_supertrend(df, 10, 3.0)
    df["SuperTrend"] = st_df["SuperTrend"]
    df["SuperTrend Direction"] = st_df["SuperTrend Direction"]

    ich_df = calculate_ichimoku(df)
    df["Tenkan-sen"] = ich_df["Tenkan-sen"]
    df["Kijun-sen"] = ich_df["Kijun-sen"]
    df["Senkou Span A"] = ich_df["Senkou Span A"]
    df["Senkou Span B"] = ich_df["Senkou Span B"]

    # Support & Resistance
    sr_df = calculate_support_resistance(df, 20)
    df["Pivot Point"] = sr_df["Pivot Point"]
    df["Support 1"] = sr_df["Support 1"]
    df["Resistance 1"] = sr_df["Resistance 1"]
    df["Support 2"] = sr_df["Support 2"]
    df["Resistance 2"] = sr_df["Resistance 2"]
    df["Swing Support"] = sr_df["Swing Support"]
    df["Swing Resistance"] = sr_df["Swing Resistance"]

    # Volatility & Bands
    bb_df = calculate_bollinger_bands(df, config)
    df["BB Upper"] = bb_df["BB Upper"]
    df["BB Middle"] = bb_df["BB Middle"]
    df["BB Lower"] = bb_df["BB Lower"]
    df["BB Bandwidth"] = bb_df["BB Bandwidth"]
    df["BB %B"] = bb_df["BB %B"]

    df["ATR (14)"] = calculate_atr(df, 14)

    # Volume Indicators & VWAP
    df["VWAP"] = calculate_vwap(df)
    df["OBV"] = calculate_obv(df)
    df["Volume Change (%)"] = df["Volume"].pct_change() * 100.0
    df["Volume 20MA"] = df["Volume"].rolling(20).mean()
    df["Volume Surge"] = df["Volume"] > (df["Volume 20MA"] * 1.5)

    # Price Gaps
    gaps = detect_price_gaps(df)
    df["Previous High"] = gaps["Previous High"]
    df["Previous Low"] = gaps["Previous Low"]
    df["Gap Up"] = gaps["Gap Up"]
    df["Gap Down"] = gaps["Gap Down"]

    return df
