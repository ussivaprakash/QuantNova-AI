"""
Stage 6 & 7: Interactive Plotly HTML Dashboard & Multi-Sheet Excel Export Engine.

Displays:
- Interactive Candlestick OHLC Chart with Moving Averages & Bollinger Bands
- Buy / Sell Signal Markers Overlay (Green ▲ for Buy, Red ▼ for Sell)
- Volume Bar Chart (Colored Green/Red with Volume 20MA)
- RSI Subplot (with 70/30 threshold lines)
- MACD Subplot (MACD Line, Signal Line, Histogram)
- Portfolio Performance Equity Curve (Strategy vs Buy-and-Hold)
- Current Recommendation Card (Signal, Confidence, Risk Level, Stop Loss, Target Price)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import PipelineConfig


def _format_metric(value, precision=2, prefix="", suffix=""):
    if value is None or pd.isna(value):
        return "Unavailable"
    try:
        return f"{prefix}{float(value):.{precision}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def _return_percent(equity, initial_capital=100000.0):
    if equity is None or pd.isna(equity):
        return None
    return (float(equity) - initial_capital) / initial_capital * 100


def generate_html_dashboard(df: pd.DataFrame, config: PipelineConfig) -> Path:
    """
    Builds a full-featured, dark-mode responsive Plotly trading dashboard.
    """
    config.output_dashboard.parent.mkdir(parents=True, exist_ok=True)
    latest = df.iloc[-1]
    strategy_return = _return_percent(latest.get("Strategy Equity"))
    benchmark_return = _return_percent(latest.get("Benchmark Equity"))
    alpha_return = strategy_return - benchmark_return if strategy_return is not None and benchmark_return is not None else None

    # Current recommendation styling
    signal = str(latest.get("Signal", latest.get("Signal Category", "HOLD / WAIT")))
    if "BUY" in signal:
        badge_bg = "rgba(34, 197, 94, 0.15)"
        badge_color = "#22c55e"
        border_color = "#16a34a"
    elif "SELL" in signal:
        badge_bg = "rgba(239, 68, 68, 0.15)"
        badge_color = "#ef4444"
        border_color = "#dc2626"
    else:
        badge_bg = "rgba(234, 179, 8, 0.15)"
        badge_color = "#eab308"
        border_color = "#ca8a04"

    # Create 5-Subplot Layout
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            f"{config.ticker} Price Action & Buy/Sell Execution Signals",
            "Trading Volume & Surge Analysis",
            "RSI Momentum Oscillator (14)",
            "MACD Trend & Histogram",
            "Portfolio Equity Curve: Quantitative Strategy vs. Buy-and-Hold Benchmark"
        ),
        row_heights=[0.40, 0.15, 0.15, 0.15, 0.15]
    )

    # 1. Candlestick Chart
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name="OHLC Price"
        ),
        row=1, col=1
    )

    # Moving Averages Overlay
    if "SMA 20" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA 20"], name="SMA 20", line=dict(color="#f59e0b", width=1.5)), row=1, col=1)
    elif "20-Day MA" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["20-Day MA"], name="SMA 20", line=dict(color="#f59e0b", width=1.5)), row=1, col=1)

    if "SMA 50" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA 50"], name="SMA 50", line=dict(color="#3b82f6", width=1.5)), row=1, col=1)
    if "SMA 200" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA 200"], name="SMA 200", line=dict(color="#a855f7", width=1.5)), row=1, col=1)

    # Bollinger Bands
    if "BB Upper" in df.columns and "BB Lower" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB Upper"], name="BB Upper", line=dict(color="rgba(255,255,255,0.25)", dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["BB Lower"], name="BB Lower", line=dict(color="rgba(255,255,255,0.25)", dash="dot"), fill="tonexty", fillcolor="rgba(255,255,255,0.02)"), row=1, col=1)

    # Buy / Sell Execution Markers
    buy_signals = df[df["Signal"].str.startswith("BUY", na=False)]
    sell_signals = df[df["Signal"].str.startswith("SELL", na=False)]

    if not buy_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_signals["Date"],
                y=buy_signals["Low"] * 0.98,
                mode="markers",
                name="BUY Signal",
                marker=dict(symbol="triangle-up", size=11, color="#22c55e", line=dict(width=1, color="#ffffff"))
            ),
            row=1, col=1
        )

    if not sell_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_signals["Date"],
                y=sell_signals["High"] * 1.02,
                mode="markers",
                name="SELL Signal",
                marker=dict(symbol="triangle-down", size=11, color="#ef4444", line=dict(width=1, color="#ffffff"))
            ),
            row=1, col=1
        )

    # 2. Volume Bar Chart
    vol_colors = ["#22c55e" if c >= o else "#ef4444" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume", marker_color=vol_colors), row=2, col=1)
    if "Volume 20MA" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Volume 20MA"], name="Volume 20MA", line=dict(color="#f59e0b", width=1.5)), row=2, col=1)

    # 3. RSI Subplot
    if "RSI (14)" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI (14)"], name="RSI (14)", line=dict(color="#ec4899", width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#22c55e", row=3, col=1)

    # 4. MACD Subplot
    if "MACD" in df.columns and "MACD Signal" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="#06b6d4", width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD Signal"], name="MACD Signal", line=dict(color="#f97316", width=1.5)), row=4, col=1)
        if "MACD Histogram" in df.columns:
            hist_colors = ["#22c55e" if h >= 0 else "#ef4444" for h in df["MACD Histogram"]]
            fig.add_trace(go.Bar(x=df["Date"], y=df["MACD Histogram"], name="Histogram", marker_color=hist_colors), row=4, col=1)

    # 5. Portfolio Performance Equity Curve
    if "Strategy Equity" in df.columns and "Benchmark Equity" in df.columns:
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Strategy Equity"], name="Strategy Equity (₹)", line=dict(color="#10b981", width=2.5)), row=5, col=1)
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Benchmark Equity"], name="Buy-and-Hold Equity (₹)", line=dict(color="#64748b", width=1.5, dash="dash")), row=5, col=1)

    # Styling Layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(family="Inter, sans-serif", color="#f8fafc"),
        height=1100,
        xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    # Table rows for historical log
    recent_rows = df.tail(15).iloc[::-1]
    table_rows = ""
    for _, row in recent_rows.iterrows():
        sig = str(row.get("Signal", row.get("Signal Category", "HOLD")))
        cls = "bg-emerald-900/40 text-emerald-400 border border-emerald-800" if "BUY" in sig else ("bg-rose-900/40 text-rose-400 border border-rose-800" if "SELL" in sig else "bg-amber-900/40 text-amber-400 border border-amber-800")
        table_rows += f"""
        <tr class="border-b border-slate-800 hover:bg-slate-800/60 transition-colors">
            <td class="py-3 px-4 text-sm text-slate-300">{row['Date'].strftime('%Y-%m-%d')}</td>
            <td class="py-3 px-4 text-sm font-semibold text-white">₹{row['Close']:.2f}</td>
            <td class="py-3 px-4 text-sm text-slate-300">{row.get('Trend Classification', 'N/A')}</td>
            <td class="py-3 px-4 text-sm"><span class="px-2.5 py-1 rounded-md text-xs font-bold {cls}">{sig}</span></td>
            <td class="py-3 px-4 text-sm text-slate-300 font-medium">{row.get('Signal Confidence (%)', 0)}%</td>
            <td class="py-3 px-4 text-sm text-slate-300">{row.get('Risk Level', 'N/A')}</td>
            <td class="py-3 px-4 text-sm text-rose-400 font-medium">₹{row.get('Suggested Stop Loss (₹)', 0):.2f}</td>
            <td class="py-3 px-4 text-sm text-emerald-400 font-medium">₹{row.get('Suggested Target Price (₹)', 0):.2f}</td>
            <td class="py-3 px-4 text-sm text-slate-400 max-w-xs truncate" title="{row.get('Reason for Decision', '')}">{row.get('Reason for Decision', '')}</td>
        </tr>
        """

    # Full HTML Document
    html_content = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.ticker} Quantitative Intelligence & Backtest Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #f8fafc; }}
    </style>
</head>
<body class="min-h-screen pb-16">
    <!-- Header Navbar -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
                <h1 class="text-xl font-bold text-white tracking-tight">{config.ticker} Quantitative Signal & Portfolio Dashboard</h1>
            </div>
            <div class="text-xs text-slate-400">
                Last Updated: <span class="text-slate-200 font-semibold">{latest['Date'].strftime('%Y-%m-%d')}</span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 mt-8 space-y-8">
        <!-- Highlights Card Grid -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <!-- Current Recommendation Card -->
            <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl relative overflow-hidden" style="border-top: 4px solid {border_color};">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Current Recommendation</div>
                <div class="mt-3 flex items-baseline space-x-2">
                    <span class="text-3xl font-black tracking-tight" style="color: {badge_color};">{signal}</span>
                </div>
                <div class="mt-2 text-xs text-slate-300">
                    Confidence: <span class="font-bold text-white">{latest.get('Signal Confidence (%)', 0)}%</span> | Risk: <span class="font-bold text-amber-400">{latest.get('Risk Level', 'N/A')}</span>
                </div>
                <div class="mt-3 grid grid-cols-2 gap-2 text-xs border-t border-slate-800 pt-3">
                    <div>Stop Loss: <span class="font-bold text-rose-400">{_format_metric(latest.get('Suggested Stop Loss (₹)'), 2, '₹')}</span></div>
                    <div>Target: <span class="font-bold text-emerald-400">{_format_metric(latest.get('Suggested Target Price (₹)'), 2, '₹')}</span></div>
                </div>
            </div>

            <!-- Price & Trend Card -->
            <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Market Price & Trend</div>
                <div class="mt-3 text-3xl font-extrabold text-white">₹{latest['Close']:.2f}</div>
                <div class="mt-2 text-xs text-slate-300">
                    Classification: <span class="font-bold text-cyan-400">{latest.get('Trend Classification', 'N/A')}</span>
                </div>
                <div class="mt-1 text-xs text-slate-400">
                    SMA 20: <span class="text-slate-200">{_format_metric(latest.get('SMA 20', latest.get('20-Day MA')), 2, '₹')}</span>
                </div>
            </div>

            <!-- Machine Learning Model Card -->
            <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Random Forest Forecast</div>
                <div class="mt-3 text-3xl font-extrabold text-cyan-400">{_format_metric(latest.get('ML Bull Prob (%)'), 1, suffix='%')}</div>
                <div class="mt-2 text-xs text-slate-300">
                    Bullish Probability | Forecast: <span class="font-bold text-slate-200">{latest.get('ML Prediction', 'N/A')}</span>
                </div>
                <div class="mt-1 text-xs text-slate-400">
                    Model Confidence: <span class="text-slate-200">{latest.get('ML Confidence', 'N/A')}</span>
                </div>
            </div>

            <!-- Portfolio Performance Card -->
            <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
                <div class="text-xs uppercase tracking-wider font-semibold text-slate-400">Strategy vs Benchmark</div>
                <div class="mt-3 text-2xl font-extrabold text-emerald-400">
                    {_format_metric(strategy_return, 2, suffix='%')} Return
                </div>
                <div class="mt-2 text-xs text-slate-300">
                    Buy & Hold: <span class="font-bold text-rose-400">{_format_metric(benchmark_return, 2, suffix='%')}</span>
                </div>
                <div class="mt-1 text-xs text-slate-400">
                    Alpha Generated: <span class="font-bold text-emerald-400">{_format_metric(alpha_return, 2, suffix='%')}</span>
                </div>
            </div>
        </div>

        <!-- Interactive Plotly Chart Panel -->
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl">
            <h2 class="text-lg font-bold text-slate-100 mb-4">Interactive Technical, Signal & Portfolio Visualization</h2>
            {chart_html}
        </div>

        <!-- Historical Signal & Recommendation Log -->
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
            <h2 class="text-lg font-bold text-slate-100 mb-4">Daily Recommendation & Level History (Last 15 Sessions)</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-xs font-bold text-slate-400 uppercase tracking-wider">
                            <th class="py-3 px-4">Date</th>
                            <th class="py-3 px-4">Close</th>
                            <th class="py-3 px-4">Trend Classification</th>
                            <th class="py-3 px-4">Signal</th>
                            <th class="py-3 px-4">Confidence</th>
                            <th class="py-3 px-4">Risk Level</th>
                            <th class="py-3 px-4">Stop Loss</th>
                            <th class="py-3 px-4">Target Price</th>
                            <th class="py-3 px-4">Reason for Decision</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </main>
</body>
</html>
"""

    with open(config.output_dashboard, "w", encoding="utf-8") as f:
        f.write(html_content)

    return config.output_dashboard


def export_to_excel_workbook(
    df: pd.DataFrame,
    config: PipelineConfig,
    audit_report_df: pd.DataFrame = None,
    rf_metrics: dict = None,
    feature_importance_df: pd.DataFrame = None,
    backtest_metrics_df: pd.DataFrame = None,
    trade_log_df: pd.DataFrame = None,
    split_sheets: bool = True,
) -> Path:
    """Exports quantitative results into formatted Excel workbook (split sheets or consolidated)."""
    config.output_excel.parent.mkdir(parents=True, exist_ok=True)

    # Sanitize datetime timezones for openpyxl compatibility
    export_df = df.copy()
    if "Date" in export_df.columns:
        export_df["Date"] = pd.to_datetime(export_df["Date"]).dt.tz_localize(None)

    clean_trade_log = trade_log_df.copy() if trade_log_df is not None else None
    if clean_trade_log is not None:
        for c in clean_trade_log.columns:
            if pd.api.types.is_datetime64_any_dtype(clean_trade_log[c]):
                clean_trade_log[c] = pd.to_datetime(clean_trade_log[c]).dt.tz_localize(None)

    with pd.ExcelWriter(config.output_excel, engine="openpyxl", datetime_format="yyyy-mm-dd") as writer:
        if not split_sheets:
            # Single Consolidated Master Sheet
            export_df.to_excel(writer, sheet_name="Master Stock Data (A-Z)", index=False)
        else:
            # Sheet 1: Executive Cover Page & Summary
            latest_df = export_df.tail(1)[["Date", "Close", "Trend Classification", "ML Bull Prob (%)", "Signal", "Signal Confidence (%)", "Risk Level", "Suggested Stop Loss (₹)", "Suggested Target Price (₹)", "Reason for Decision"]]
            latest_df.to_excel(writer, sheet_name="Executive Summary", index=False)

        # Sheet 2: Complete Historical Market Data (A-Z)
        export_df[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]].to_excel(
            writer, sheet_name="Full History (A-Z)", index=False
        )

        # Sheet 3: Data Quality Audit
        if audit_report_df is not None:
            audit_report_df.to_excel(writer, sheet_name="Data Quality Audit", index=False)

        # Sheet 4: Technical Indicators
        tech_cols = [
            "Date", "Close", "Daily Return (%)", "Rolling Volatility (20D Ann %)",
            "SMA 20", "SMA 50", "SMA 100", "SMA 200",
            "EMA 20", "EMA 50",
            "RSI (14)", "MACD", "MACD Signal", "MACD Histogram",
            "BB Upper", "BB Middle", "BB Lower", "BB Bandwidth", "BB %B",
            "ATR (14)", "ADX (14)", "+DI", "-DI",
            "VWAP", "OBV", "Stoch %K", "Stoch %D",
            "Volume Change (%)", "Volume Surge",
            "Gap Up", "Gap Down"
        ]
        export_df[[c for c in tech_cols if c in export_df.columns]].to_excel(writer, sheet_name="Technical Indicators", index=False)

        # Sheet 5: Trend Analysis
        trend_cols = ["Date", "Close", "Trend Classification", "Trend Score", "Trend Reason", "MA20 Slope (%)"]
        export_df[[c for c in trend_cols if c in export_df.columns]].to_excel(writer, sheet_name="Trend Analysis", index=False)

        # Sheet 6: ML Prediction Model & Out of Sample Predictions
        ml_cols = ["Date", "Close", "ML Bull Prob (%)", "ML Prediction", "ML Confidence"]
        export_df[[c for c in ml_cols if c in export_df.columns]].to_excel(writer, sheet_name="Prediction Model", index=False)

        # Sheet 7: RF Feature Importances
        if feature_importance_df is not None and not feature_importance_df.empty:
            feature_importance_df.to_excel(writer, sheet_name="Feature Importance", index=False)

        # Sheet 8: RF Model Evaluation Metrics
        if rf_metrics:
            metrics_df = pd.DataFrame(list(rf_metrics.items()), columns=["Evaluation Metric", "Value"])
            metrics_df.to_excel(writer, sheet_name="RF Model Metrics", index=False)

        # Sheet 9: Buy Hold Sell Signals
        sig_cols = [
            "Date", "Close", "Signal", "Signal Confidence (%)", "Risk Level",
            "Reason for Decision", "Suggested Stop Loss (₹)", "Suggested Target Price (₹)",
            "Signal Action Plan"
        ]
        export_df[[c for c in sig_cols if c in export_df.columns]].to_excel(writer, sheet_name="Buy Hold Sell Signals", index=False)

        # Sheet 10: Backtest Performance Summary
        if backtest_metrics_df is not None and not backtest_metrics_df.empty:
            backtest_metrics_df.to_excel(writer, sheet_name="Backtest Summary", index=False)

        # Sheet 11: Trade Execution Log
        if clean_trade_log is not None and not clean_trade_log.empty:
            clean_trade_log.to_excel(writer, sheet_name="Trade Execution Log", index=False)

        from openpyxl.styles import Font, PatternFill, Alignment
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")

        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
            for column in worksheet.columns:
                column_letter = column[0].column_letter
                max_len = max(len(str(cell.value or "")) for cell in column)
                worksheet.column_dimensions[column_letter].width = min(max(max_len + 2, 12), 70)


    return config.output_excel
