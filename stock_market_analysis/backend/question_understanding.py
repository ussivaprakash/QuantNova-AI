"""
Question Understanding Module for QuantNova AI Financial Research Agent.

Extracts structured intent, entities, timeframe, comparisons, and query depth
from natural language user queries regarding Indian stock market equities (NSE/BSE).
"""

import re
import urllib.parse
import json
import urllib.request
from typing import Dict, Any, List, Optional

# Indian Stock Ticker Directory for High-Accuracy Named Entity Recognition & Resolution
TICKER_MAP = {
    # Automotive
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "TATA MOTOR": "TATAMOTORS.NS",
    "TMPV": "TMPV.NS",
    "MAHINDRA": "M&M.NS",
    "M&M": "M&M.NS",
    "MARUTI": "MARUTI.NS",
    "MARUTI SUZUKI": "MARUTI.NS",
    "ASHOK LEYLAND": "ASHOKLEY.NS",
    "ASHOKLEY": "ASHOKLEY.NS",
    "EICHER": "EICHERMOT.NS",
    "EICHER MOTORS": "EICHERMOT.NS",
    "BAJAJ AUTO": "BAJAJ-AUTO.NS",
    "TVS MOTOR": "TVSMOTOR.NS",
    "HERO MOTOCORP": "HEROMOTOCO.NS",

    # Banking & Financials
    "HDFC BANK": "HDFCBANK.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBI": "SBIN.NS",
    "STATE BANK": "SBIN.NS",
    "SBIN": "SBIN.NS",
    "AXIS BANK": "AXISBANK.NS",
    "KOTAK BANK": "KOTAKBANK.NS",
    "KOTAK": "KOTAKBANK.NS",
    "INDUSIND": "INDUSINDBK.NS",
    "INDIAN OVERSEAS BANK": "IOB.NS",
    "IOB": "IOB.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "BAJAJ FINSERV": "BAJAJFINSV.NS",

    # IT & Tech
    "TCS": "TCS.NS",
    "TATA CONSULTANCY": "TCS.NS",
    "INFOSYS": "INFY.NS",
    "INFY": "INFY.NS",
    "WIPRO": "WIPRO.NS",
    "HCLTECH": "HCLTECH.NS",
    "HCL TECH": "HCLTECH.NS",
    "TECH MAHINDRA": "TECHM.NS",
    "LTIMINDTREE": "LTIM.NS",

    # Conglomerates & Energy
    "RELIANCE": "RELIANCE.NS",
    "RIL": "RELIANCE.NS",
    "RELIANCE INDUSTRIES": "RELIANCE.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS",
    "ADANI PORTS": "ADANIPORTS.NS",
    "ADANI GREEN": "ADANIGREEN.NS",
    "NTPC": "NTPC.NS",
    "POWER GRID": "POWERGRID.NS",
    "ONGC": "ONGC.NS",
    "COAL INDIA": "COALINDIA.NS",
    "TATA POWER": "TATAPOWER.NS",

    # FMCG & Consumer
    "ITC": "ITC.NS",
    "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
    "HUL": "HINDUNILVR.NS",
    "TITAN": "TITAN.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS",
    "NESTLE": "NESTLEIND.NS",
    "BRITANNIA": "BRITANNIA.NS",

    # Metals & Infra
    "TATA STEEL": "TATASTEEL.NS",
    "JSW STEEL": "JSWSTEEL.NS",
    "HINDALCO": "HINDALCO.NS",
    "L&T": "LT.NS",
    "LARSEN": "LT.NS",
    "LARSEN & TOUBRO": "LT.NS",
    "ULTRATECH": "ULTRACEMCO.NS",
    "ULTRATECH CEMENT": "ULTRACEMCO.NS",

    # Pharma
    "SUN PHARMA": "SUNPHARMA.NS",
    "SUNPHARMA": "SUNPHARMA.NS",
    "DR REDDY": "DRREDDY.NS",
    "CIPLA": "CIPLA.NS",
    "DIVIS LAB": "DIVISLAB.NS",

    # Indices
    "NIFTY": "^NSEI",
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
    "BSE SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "AUTO INDEX": "^CNXAUTO",
    "NIFTY AUTO": "^CNXAUTO",
    "IT INDEX": "^CNXIT",
    "NIFTY IT": "^CNXIT",
}


def resolve_symbol_from_text(text: str) -> Optional[str]:
    """Resolves company name or symbol mentioned in user query."""
    text_upper = text.upper()

    # 1. Match explicitly configured ticker aliases
    for key, sym in TICKER_MAP.items():
        # Match word boundaries or substring
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, text_upper):
            return sym

    # 2. Check for symbols with explicit .NS or .BO suffix
    raw_symbols = re.findall(r'\b[A-Z0-9\-]{2,12}\.(?:NS|BO)\b', text_upper)
    if raw_symbols:
        return raw_symbols[0]

    # 3. Live search lookup via Yahoo Finance API fallback
    words = [w for w in re.findall(r'\b[A-Za-z0-9]+\b', text) if len(w) > 2 and w.lower() not in [
        "why", "did", "how", "what", "is", "are", "the", "stock", "company", "fall", "rise", "today", "down", "up",
        "drop", "jump", "grow", "make", "money", "future", "plans", "profit", "revenue", "compare", "with"
    ]]
    
    if words:
        search_query = " ".join(words[:2])
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(search_query)}&quotesCount=5&newsCount=0"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                quotes = data.get("quotes", [])
                for q in quotes:
                    sym = q.get("symbol", "")
                    if sym.endswith(".NS") or sym.endswith(".BO"):
                        return sym
        except Exception:
            pass

    return "TATAMOTORS.NS"  # Default Indian stock reference if unassigned


def classify_intent(query: str) -> str:
    """Classifies user intent from natural language question."""
    q_lower = query.lower()

    if any(k in q_lower for k in ["why did", "why is", "fall", "falling", "rose", "rising", "dropped", "down today", "up today", "plunge", "rally", "suddenly moving"]):
        return "stock_movement"
    elif any(k in q_lower for k in ["how does", "make money", "products", "customers", "revenue sources", "business model", "where operate", "segments"]):
        return "business_model"
    elif any(k in q_lower for k in ["growth", "why revenue", "why profit", "margins improving", "driving growth", "growth drivers", "production increasing"]):
        return "growth_analysis"
    elif any(k in q_lower for k in ["future", "planning next", "projects", "investing", "new plants", "expansion", "management plans", "future plans"]):
        return "future_projects"
    elif any(k in q_lower for k in ["debt", "cash", "cash flow", "free cash flow", "roe", "roce", "balance sheet", "margin", "profitability"]):
        return "financial_analysis"
    elif any(k in q_lower for k in ["nifty", "sensex", "market falling", "banking stocks", "automobile sector", "market moving"]):
        return "market_analysis"
    elif any(k in q_lower for k in ["compare", "vs", "versus", "better than", "competitors", "peers"]):
        return "peer_comparison"
    elif any(k in q_lower for k in ["historical", "fallen like this before", "last time", "earn reaction", "similar events", "five years ago"]):
        return "historical_analysis"
    elif any(k in q_lower for k in ["rsi", "macd", "moving average", "support", "resistance", "technical", "chart"]):
        return "technical_analysis"
    elif any(k in q_lower for k in ["pe ratio", "pb", "valuation", "undervalued", "overvalued", "target price"]):
        return "valuation"
    elif any(k in q_lower for k in ["deep analysis", "everything important", "opportunities and risks", "full research", "overview"]):
        return "deep_research"
    else:
        return "custom_research"


def detect_timeframe(query: str) -> str:
    """Detects query timeframe context."""
    q_lower = query.lower()
    if any(k in q_lower for k in ["today", "intraday", "now"]):
        return "today"
    elif any(k in q_lower for k in ["this week", "recent", "recent days"]):
        return "1w"
    elif any(k in q_lower for k in ["quarter", "q1", "q2", "q3", "q4", "results"]):
        return "quarterly"
    elif any(k in q_lower for k in ["year", "1y", "annually", "annual"]):
        return "1y"
    elif any(k in q_lower for k in ["5 years", "historical", "before", "ever"]):
        return "5y"
    elif any(k in q_lower for k in ["future", "next", "plans", "coming", "2026", "2027"]):
        return "future"
    return "today"


def extract_comparison_peers(query: str, primary_symbol: str) -> List[str]:
    """Detects mentioned peer companies for comparison."""
    peers = []
    text_upper = query.upper()
    for name, sym in TICKER_MAP.items():
        if sym != primary_symbol and not sym.startswith("^"):
            pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(pattern, text_upper):
                if sym not in peers:
                    peers.append(sym)

    # Standard auto peer default if intent is peer_comparison
    if not peers and classify_intent(query) == "peer_comparison":
        if primary_symbol in ["TATAMOTORS.NS", "TMPV.NS"]:
            peers = ["M&M.NS", "MARUTI.NS"]
        elif primary_symbol == "RELIANCE.NS":
            peers = ["TCS.NS", "ADANIENT.NS"]
        elif primary_symbol == "HDFCBANK.NS":
            peers = ["ICICIBANK.NS", "SBIN.NS"]
        elif primary_symbol == "TCS.NS":
            peers = ["INFY.NS", "WIPRO.NS"]

    return peers


def parse_user_question(query: str) -> Dict[str, Any]:
    """
    Main entry point for Question Understanding module.
    Returns structured representation of the question.
    """
    primary_symbol = resolve_symbol_from_text(query)
    intent = classify_intent(query)
    timeframe = detect_timeframe(query)
    peers = extract_comparison_peers(query, primary_symbol)
    
    # Is deep query check
    is_deep = any(k in query.lower() for k in ["deep", "detailed", "everything", "full analysis", "comprehensive"]) or intent == "deep_research"

    return {
        "raw_query": query,
        "intent": intent,
        "primary_symbol": primary_symbol,
        "entities": [
            {"type": "company", "symbol": primary_symbol}
        ] + [{"type": "peer", "symbol": p} for p in peers],
        "timeframe": timeframe,
        "comparison_peers": peers,
        "depth": "deep" if is_deep else "standard",
        "language": "en"
    }


# Function alias for backwards compatibility and API imports
understand_user_question = parse_user_question
