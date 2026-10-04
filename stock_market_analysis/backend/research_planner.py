"""
Research Planner Module for QuantNova AI Financial Research Agent.

Generates dynamic, step-by-step financial research plans based on parsed
intent, entity context, timeframe, and depth parameters.
"""

from typing import Dict, Any, List


class ResearchStep:
    def __init__(self, step_id: str, title: str, description: str, tools_required: List[str]):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.tools_required = tools_required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "tools_required": self.tools_required
        }


def build_research_plan(parsed_question: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Constructs a tailored research plan detailing the data sources,
    analytical modules, and cross-checks required to address the user's question.
    """
    intent = parsed_question.get("intent", "stock_movement")
    symbol = parsed_question.get("primary_symbol", "TATAMOTORS.NS")
    peers = parsed_question.get("comparison_peers", [])

    steps: List[ResearchStep] = []

    # Step 1: Base Quote & Intraday Market Context
    steps.append(ResearchStep(
        step_id="market_context",
        title="Collect Market & Intraday Data",
        description=f"Fetch latest real-time quote, intraday price action, volume, NIFTY/Sensex benchmark movement, and sector index for {symbol}.",
        tools_required=["MarketDataProvider", "get_quote", "get_intraday", "get_market_context"]
    ))

    # Intent-driven tailored research steps
    if intent == "stock_movement":
        steps.append(ResearchStep(
            step_id="news_disclosures",
            title="Gather Live News & Exchange Disclosures",
            description=f"Search today's breaking news, corporate announcements, BSE/NSE regulatory filings, and results for {symbol}.",
            tools_required=["NewsProvider", "FilingsProvider", "search_news", "get_announcements"]
        ))
        steps.append(ResearchStep(
            step_id="technical_indicators",
            title="Evaluate Technical Regime & Volatility",
            description=f"Compute 25+ technical indicators (RSI, MACD, Moving Averages, Support/Resistance levels) using TechnicalAnalysisService.",
            tools_required=["TechnicalAnalysisService", "TrendAnalysisService"]
        ))
        steps.append(ResearchStep(
            step_id="peer_intraday",
            title="Analyze Peer Sector Movement",
            description=f"Compare price action with peer stocks ({', '.join(peers) if peers else 'sector benchmark'}) to isolate company-specific vs market-wide moves.",
            tools_required=["MarketDataProvider", "get_quote"]
        ))
        steps.append(ResearchStep(
            step_id="event_correlation",
            title="Correlate Events with Price & Volume Spikes",
            description="Align news timestamps with intraday price dips/rallies and volume bursts to establish causal drivers.",
            tools_required=["EventCorrelationEngine", "NewsRelevanceScorer"]
        ))

    elif intent == "business_model":
        steps.append(ResearchStep(
            step_id="company_profile",
            title="Fetch Company Profile & Revenue Breakdown",
            description=f"Retrieve core business description, product segments, key markets, and geographical revenue split for {symbol}.",
            tools_required=["CompanyDataProvider", "get_company_profile"]
        ))
        steps.append(ResearchStep(
            step_id="segment_financials",
            title="Analyze Segment Margins & Growth",
            description="Evaluate revenue contribution and profitability margins by operating segment.",
            tools_required=["FinancialDataProvider", "get_segment_financials"]
        ))
        steps.append(ResearchStep(
            step_id="future_expansion",
            title="Review Capacity & Manufacturing Footprint",
            description="Examine production capacity, manufacturing plants, key customer contracts, and product portfolio.",
            tools_required=["CompanyDataProvider", "get_expansion_plans"]
        ))

    elif intent == "growth_analysis":
        steps.append(ResearchStep(
            step_id="financial_growth",
            title="Analyze Multi-Quarter Revenue & Profit Trajectory",
            description=f"Examine quarterly and annual revenue growth, profit margin expansion (EBITDA %, PAT %), and production trends.",
            tools_required=["FinancialDataProvider", "FundamentalAnalysisService"]
        ))
        steps.append(ResearchStep(
            step_id="growth_drivers",
            title="Identify Key Revenue & Demand Drivers",
            description="Extract growth catalysts (volume growth, pricing power, export expansion, new product launches).",
            tools_required=["NewsProvider", "CompanyDataProvider"]
        ))

    elif intent == "future_projects":
        steps.append(ResearchStep(
            step_id="expansion_projects",
            title="Analyze Future Projects & Capex Investments",
            description=f"Identify upcoming manufacturing plants, R&D investments, EV initiatives, and strategic partnerships for {symbol}.",
            tools_required=["CompanyDataProvider", "FilingsProvider"]
        ))
        steps.append(ResearchStep(
            step_id="management_outlook",
            title="Examine Management Guidance & Future Strategy",
            description="Extract management commentary from earnings transcripts and strategic disclosures.",
            tools_required=["FilingsProvider", "get_exchange_filings"]
        ))

    elif intent == "financial_analysis":
        steps.append(ResearchStep(
            step_id="fundamental_health",
            title="Evaluate Profitability & Return Ratios",
            description="Compute ROE, ROCE, Operating Margins, Net Debt-to-Equity ratio, and Free Cash Flow generation.",
            tools_required=["FundamentalAnalysisService", "FinancialDataProvider"]
        ))
        steps.append(ResearchStep(
            step_id="balance_sheet_risk",
            title="Assess Solvency & Capital Structure",
            description="Examine total debt, cash reserves, working capital cycle, and interest coverage ratio.",
            tools_required=["RiskAnalysisService", "FinancialDataProvider"]
        ))

    elif intent == "peer_comparison":
        steps.append(ResearchStep(
            step_id="peer_financials",
            title=f"Side-by-Side Peer Analysis ({symbol} vs Peers)",
            description=f"Compare revenue growth, EBITDA margin, ROE, ROCE, P/E ratio, and market cap with {', '.join(peers) if peers else 'competitors'}.",
            tools_required=["FinancialDataProvider", "FundamentalAnalysisService"]
        ))
        steps.append(ResearchStep(
            step_id="relative_valuation",
            title="Evaluate Relative Valuation & Market Performance",
            description="Compare 1-Year price return, valuation multiples (P/E, P/B), and relative strength index.",
            tools_required=["MarketDataProvider", "FundamentalAnalysisService"]
        ))

    else:
        # Standard Comprehensive Research Plan
        steps.append(ResearchStep(
            step_id="news_disclosures",
            title="Gather News & Filings",
            description=f"Retrieve recent news and exchange disclosures for {symbol}.",
            tools_required=["NewsProvider", "FilingsProvider"]
        ))
        steps.append(ResearchStep(
            step_id="technical_indicators",
            title="Quantitative Indicators Analysis",
            description="Execute Technical Analysis & Signal Engine.",
            tools_required=["TechnicalAnalysisService", "SignalService"]
        ))
        steps.append(ResearchStep(
            step_id="fundamental_health",
            title="Fundamental Health Analysis",
            description="Execute Fundamental Analysis & Risk Scoring.",
            tools_required=["FundamentalAnalysisService", "RiskAnalysisService"]
        ))

    # Synthesis Step (Common to all)
    steps.append(ResearchStep(
        step_id="cross_checking_synthesis",
        title="Cross-Check Evidence & Synthesize AI Research Report",
        description="Correlate findings, eliminate contradictions, format evidence cards, and generate final institutional research response.",
        tools_required=["CrossCheckingEngine", "SynthesisEngine"]
    ))

    return [s.to_dict() for s in steps]
