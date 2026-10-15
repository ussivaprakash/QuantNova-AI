"""
Stage 10: PDF Investment Report Generator Module.
Creates a professional PDF Investment Memo for any analyzed stock symbol using ReportLab.
"""

from pathlib import Path
from typing import Dict, Any
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def _format_metric(value, precision=2, prefix="", suffix=""):
    if value is None or pd.isna(value):
        return "Unavailable"
    try:
        return f"{prefix}{float(value):.{precision}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)

def generate_pdf_report(
    ticker: str,
    latest_row: pd.Series,
    fundamental_data: Dict[str, Any],
    rf_metrics: Dict[str, Any],
    backtest_metrics: Dict[str, Any],
    output_path: Path,
    split_pages: bool = True,
) -> Path:
    """
    Generates a PDF Investment Memo.
    If split_pages=True, places each major section on a dedicated separate page.
    If split_pages=False, flows content continuously.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a')
    )

    heading2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # ==========================================
    # PAGE 1: EXECUTIVE MEMO & RECOMMENDATION
    # ==========================================
    company_name = fundamental_data.get("Company Name", ticker)
    sector = fundamental_data.get("Sector", "Unknown")
    date_str = latest_row["Date"].strftime("%Y-%m-%d") if hasattr(latest_row["Date"], "strftime") else str(latest_row["Date"])
    signal = str(latest_row.get("Signal", "Unavailable"))

    if "BUY" in signal:
        sig_color = colors.HexColor("#16a34a")
    elif "SELL" in signal:
        sig_color = colors.HexColor("#dc2626")
    else:
        sig_color = colors.HexColor("#ca8a04")

    header_table = Table(
        [
            [
                Paragraph(f"<b>QuantNova AI</b> — Research Report<br/><font size=13 color='#0f172a'><b>{ticker}</b> ({company_name})</font><br/><font size=8.5 color='#64748b'>Sector: {sector} | Analysis Date: {date_str}</font>", title_style),
                Paragraph(f"<font color='{sig_color.hexval()}'><b>RECOMMENDATION</b></font><br/><font size=18 color='{sig_color.hexval()}'><b>{signal}</b></font>", ParagraphStyle('SigBox', parent=styles['Normal'], alignment=2))
            ]
        ],
        colWidths=[380, 160]
    )
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=10))

    fund_score = fundamental_data.get("Fundamental Score")
    trend_class = latest_row.get("Trend Classification", "Unavailable")
    ml_prob = latest_row.get("ML Bull Prob (%)")
    conf = latest_row.get("Signal Confidence (%)")
    risk_lvl = latest_row.get("Risk Level", "Unavailable")
    stop_loss = latest_row.get("Suggested Stop Loss (₹)")
    target_p = latest_row.get("Suggested Target Price (₹)")

    summary_data = [
        ["Close Price", _format_metric(latest_row["Close"], 2, "₹"), "Fundamental Score", f"{_format_metric(fund_score, 0)} / 100" if fund_score is not None else "Unavailable"],
        ["Trend Regime", f"{trend_class}", "ML Bullish Prob", _format_metric(ml_prob, 1, suffix="%")],
        ["Confidence Score", _format_metric(conf, 0, suffix="%"), "Risk Level", f"{risk_lvl}"],
        ["Suggested Stop Loss", _format_metric(stop_loss, 2, "₹"), "Suggested Target Price", _format_metric(target_p, 2, "₹")]
    ]
    
    summary_table = Table(summary_data, colWidths=[130, 140, 140, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Executive Investment Thesis & Action Plan", heading2_style))
    reason = latest_row.get("Reason for Decision", "Unavailable")
    fund_summary = fundamental_data.get("Fundamental Summary", "")
    
    thesis_text = (
        f"<b>Trading Signal Rationale</b>: {reason}<br/><br/>"
        f"<b>Fundamental Health Context</b>: {fund_summary}<br/><br/>"
        f"<b>Action Plan</b>: {latest_row.get('Signal Action Plan', '')}"
    )
    story.append(Paragraph(thesis_text, body_style))
    story.append(PageBreak() if split_pages else Spacer(1, 15))

    # ==========================================
    # PAGE 2: TECHNICAL INDICATORS & TREND
    # ==========================================
    story.append(Paragraph("2. Quantitative Technical Indicators & Trend Audit", heading2_style))
    tech_data = [
        ["Indicator Metric", "Value", "Technical Role"],
        ["RSI (14)", _format_metric(latest_row.get("RSI (14)"), 1), "Momentum Oscillator (Overbought > 70 / Oversold < 30)"],
        ["MACD Histogram", _format_metric(latest_row.get("MACD Histogram")), "Trend Momentum Crossover Spread"],
        ["SMA 20 / SMA 50", f"{_format_metric(latest_row.get('SMA 20'), 2, '₹')} / {_format_metric(latest_row.get('SMA 50'), 2, '₹')}", "Short & Medium Term Trend Baselines"],
        ["ATR (14)", _format_metric(latest_row.get("ATR (14)"), 2, "₹"), "14-Period Volatility & Stop Loss Range"],
        ["ADX (14)", _format_metric(latest_row.get("ADX (14)"), 1), "Trend Strength Velocity Meter (>25 = Strong)"],
        ["VWAP", _format_metric(latest_row.get("VWAP"), 2, "₹"), "Volume Weighted Average Price Benchmark"]
    ]
    tech_table = Table(tech_data, colWidths=[130, 110, 300])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tech_table)
    story.append(PageBreak() if split_pages else Spacer(1, 15))

    # ==========================================
    # PAGE 3: FUNDAMENTAL FINANCIAL RATIOS
    # ==========================================
    story.append(Paragraph("3. Fundamental Financial Ratios & Shareholding Structure", heading2_style))
    fund_table_data = [
        ["Financial Metric", "Value", "Benchmark Status"],
        ["Revenue Growth (%)", _format_metric(fundamental_data.get("Revenue Growth (%)"), suffix="%"), "YoY Top-Line Expansion"],
        ["Profit Growth (%)", _format_metric(fundamental_data.get("Profit Growth (%)"), suffix="%"), "YoY Net Profit Expansion"],
        ["P/E Ratio", _format_metric(fundamental_data.get("PE Ratio"), suffix="x"), "Trailing Price-to-Earnings Valuation"],
        ["P/B Ratio", _format_metric(fundamental_data.get("PB Ratio"), suffix="x"), "Price-to-Book Valuation"],
        ["ROE (%) / ROCE (%)", f"{_format_metric(fundamental_data.get('ROE (%)'), suffix='%')} / {_format_metric(fundamental_data.get('ROCE (%)'), suffix='%')}", "Return on Equity & Capital Efficiency"],
        ["Debt to Equity", _format_metric(fundamental_data.get("Debt to Equity"), suffix="x"), "Solvency Risk (<0.5x ideal)"],
        ["Promoter / Inst. Holding", f"{_format_metric(fundamental_data.get('Promoter Holding (%)'), suffix='%')} / {_format_metric(fundamental_data.get('Institutional Holding (%)'), suffix='%')}", "Ownership & Institutional Support"]
    ]
    fund_table = Table(fund_table_data, colWidths=[150, 120, 270])
    fund_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(fund_table)
    story.append(PageBreak() if split_pages else Spacer(1, 15))

    # ==========================================
    # PAGE 4: ML FORECASTS & BACKTEST PERFORMANCE
    # ==========================================
    story.append(Paragraph("4. Machine Learning Model Forecasts & Strategy Backtest Logs", heading2_style))
    accuracy = rf_metrics.get("Accuracy") if rf_metrics else None
    ml_accuracy = accuracy * 100 if accuracy is not None else None
    backtest_return = backtest_metrics.get("Strategy Total Return (%)") if backtest_metrics else None
    
    perf_data = [
        ["Evaluation Metric", "Quantitative System Score"],
        ["Random Forest Model Accuracy", _format_metric(ml_accuracy, 1, suffix="%")],
        ["Strategy Total Backtest Return", _format_metric(backtest_return, suffix="%")],
        ["Benchmark Buy & Hold Return", _format_metric(backtest_metrics.get("Buy & Hold Return (%)") if backtest_metrics else None, suffix="%")],
        ["Max Strategy Drawdown", _format_metric(backtest_metrics.get("Max Drawdown (%)") if backtest_metrics else None, suffix="%")]
    ]
    perf_table = Table(perf_data, colWidths=[240, 300])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(perf_table)

    doc.build(story)
    return output_path
