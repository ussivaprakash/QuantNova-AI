import React, { useState, useRef } from 'react';
import Plot from 'react-plotly.js';
import {
  Search,
  TrendingUp,
  Activity,
  Award,
  FileSpreadsheet,
  FileText,
  BarChart3,
  BrainCircuit,
  AlertTriangle,
  RefreshCw,
  Layers,
  Shield,
  Compass,
  CheckCircle2,
  Calculator,
  X,
  Sparkles,
  Globe,
} from 'lucide-react';

interface AnalysisData {
  symbol: string;
  company_name: string;
  sector: string;
  latest_price: number;
  date: string;
  market_data_source: string;
  stage_1_collection: { records_count: number; date_min: string; date_max: string };
  stage_2_cleaning: {
    "Duplicates Removed": number;
    "Missing Values Imputed": number;
    "Price Range Violations Fixed": number;
    "Rows Excluded for Missing Values": number;
  };
  stage_3_indicators: {
    rsi: number | null;
    macd_hist: number | null;
    sma20: number | null;
    sma50: number | null;
    atr: number;
    adx: number | null;
    vwap: number | null;
    obv: number | null;
    supertrend: number | null;
    support1: number | null;
    resistance1: number | null;
  };
  stage_4_trend: {
    classification: string;
    score: number;
    reason: string;
    ma20_slope: number;
  };
  stage_5_fundamentals: {
    "Fundamental Score": number | null;
    "Fundamental Rating": string;
    "Fundamental Summary": string;
    "Revenue Growth (%)": number | null;
    "Profit Growth (%)": number | null;
    "PE Ratio": number | null;
    "PB Ratio": number | null;
    "ROE (%)": number | null;
    "ROCE (%)": number | null;
    "Debt to Equity": number | null;
    "Promoter Holding (%)": number | null;
    "Institutional Holding (%)": number | null;
    "Key Highlights": string[];
  };
  stage_6_market_context: {
    "Benchmark Symbol": string;
    "Nifty 1M Return (%)": number | null;
    "Nifty Market Trend": string;
    "Relative Strength Rating": number | null;
    "Market Volatility State": string;
    "Market Context Explanation": string;
  };
  stage_7_machine_learning: {
    bullish_probability: number | null;
    prediction: string;
    confidence: string;
    metrics: { Accuracy?: number; Precision?: number; Recall?: number; "F1 Score"?: number };
    feature_importances: Array<{ Feature: string; Importance: number }>;
  };
  stage_8_backtesting: {
    metrics: Array<{ Metric: string; "Quantitative Signal Strategy": string; "Buy-and-Hold Benchmark": string }>;
    total_trades: number;
    recent_trades: Array<any>;
  };
  stage_9_risk_analysis: {
    "Risk Score": number;
    "Risk Category": string;
    "Annualized Volatility (%)": number;
    "Suggested Entry Price (₹)": number;
    "Suggested Stop Loss (₹)": number;
    "Suggested Target Price (₹)": number;
    "Risk-to-Reward Ratio": string;
    "Recommended Shares": number;
    "Suggested Position Value (₹)": number;
    "Suggested Portfolio Size (%)": number;
  };
  stage_10_decision_engine: {
    signal: string;
    confidence_score: number;
    technical_score: number;
    fundamental_score: number | null;
    risk_score: number;
    risk_level: string;
    entry_price: number;
    stop_loss: number;
    target_price: number;
    risk_reward_ratio: string;
    expected_time_horizon: string;
    pros: string[];
    cons: string[];
    risks: string[];
    reason_for_decision: string;
    ai_explanation: string;
  };
  chart_series: {
    dates: string[];
    open: number[];
    high: number[];
    low: number[];
    close: number[];
    volume: number[];
    sma20: number[];
    sma50: number[];
    sma200: number[];
    supertrend: number[];
    support1: number[];
    resistance1: number[];
    rsi: number[];
    macd: number[];
    macd_signal: number[];
    macd_hist: number[];
    strategy_equity: number[];
    benchmark_equity: number[];
    signals: string[];
  };
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : ''))
  .replace(/\/+$/, '')
  .replace(/\/api$/i, '');
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 180_000;
const displayOptional = (value: number | string | null | undefined) => value == null ? 'Unavailable' : value;

async function apiFetch(path: string, signal?: AbortSignal) {
  if (!API_BASE_URL) throw new Error('The analysis API is not configured. Set VITE_API_BASE_URL to the Render backend URL and redeploy.');
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new Error('Could not connect to the analysis service. Check your connection and try again.');
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof body?.detail === 'string' ? body.detail : `The analysis service returned HTTP ${response.status}.`;
    throw new Error(detail);
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('The analysis service returned an invalid response.');
  if (path.startsWith('/api/analyze') && (!body.stage_10_decision_engine || !body.chart_series || typeof body.latest_price !== 'number')) {
    throw new Error('The analysis service returned an incomplete stock analysis. Please retry or contact support.');
  }
  return body;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'intro' | 'dashboard'>('intro');





  const [ticker, setTicker] = useState("TATAMOTORS.NS");
  const [searchInput, setSearchInput] = useState("");

  const [selectedPeriod, setSelectedPeriod] = useState<string>("1y");
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<Array<{ symbol: string; name: string }>>([]);
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const analysisController = useRef<AbortController | null>(null);

  // Custom Pending Limit Order & Trade Planning Simulator State
  const [customPriceInput, setCustomPriceInput] = useState<string>("");
  const [customTargetInput, setCustomTargetInput] = useState<string>("");
  const [customStopLossInput, setCustomStopLossInput] = useState<string>("");

  const fetchAnalysis = async (symbolToFetch: string, periodToFetch: string = selectedPeriod) => {
    if (analysisController.current) return;
    const controller = new AbortController();
    analysisController.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    setLoading(true);
    setError(null);
    setShowDropdown(false);
    try {
      const result = await apiFetch(`/api/analyze?symbol=${encodeURIComponent(symbolToFetch)}&period=${encodeURIComponent(periodToFetch)}`, controller.signal) as AnalysisData;
      setData(result);
      setTicker(result.symbol);
      setSelectedPeriod(periodToFetch);
      setCustomPriceInput(result.stage_10_decision_engine.entry_price.toString());
      setCustomTargetInput(result.stage_10_decision_engine.target_price.toString());
      setCustomStopLossInput(result.stage_10_decision_engine.stop_loss.toString());
    } catch (err: any) {
      setError(err instanceof DOMException && err.name === 'AbortError'
        ? `Analysis exceeded ${Math.round(API_TIMEOUT_MS / 1000)} seconds. Please retry; the service may still be processing the request.`
        : err instanceof Error ? err.message : 'Analysis failed. Please try again.');
    } finally {
      window.clearTimeout(timeout);
      analysisController.current = null;
      setLoading(false);
    }
  };

  const handleSearchChange = async (val: string) => {
    setSearchInput(val);
    if (val.trim().length >= 2) {
      try {
        const items = await apiFetch(`/api/search?q=${encodeURIComponent(val)}`) as Array<{ symbol: string; name: string }>;
        setSearchResults(items);
        setShowDropdown(true);
      } catch {
        // ignore
      }
    } else {
      setShowDropdown(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      fetchAnalysis(searchInput.trim(), selectedPeriod);
      setActiveTab('dashboard');
    }
  };


  const handlePeriodChange = (newPeriod: string) => {
    setSelectedPeriod(newPeriod);
    fetchAnalysis(ticker, newPeriod);
  };

  // Live Viewer Modal States & Export Handlers
  const [showExcelViewerModal, setShowExcelViewerModal] = useState<boolean>(false);
  const [showPdfViewerModal, setShowPdfViewerModal] = useState<boolean>(false);
  const [excelTab, setExcelTab] = useState<'ohlcv' | 'indicators' | 'fundamentals' | 'backtest'>('ohlcv');

  const splitPages = true;
  const splitSheets = true;

  const handleDownloadPDFDirect = () => {
    const sym = data?.symbol || ticker;
    if (API_BASE_URL) window.open(`${API_BASE_URL}/api/export/pdf?symbol=${encodeURIComponent(sym)}&period=${encodeURIComponent(selectedPeriod)}&split_pages=${splitPages}&inline=false`, '_blank');
  };

  const handleDownloadExcelDirect = () => {
    const sym = data?.symbol || ticker;
    if (API_BASE_URL) window.open(`${API_BASE_URL}/api/export/excel?symbol=${encodeURIComponent(sym)}&period=${encodeURIComponent(selectedPeriod)}&split_sheets=${splitSheets}`, '_blank');
  };

  // Planned Trade Scenario Simulator Metrics
  const plannedBuyPrice = parseFloat(customPriceInput) || (data?.latest_price || 0);
  const plannedTargetPrice = parseFloat(customTargetInput) || (data?.stage_10_decision_engine?.target_price || 0);
  const plannedStopLoss = parseFloat(customStopLossInput) || (data?.stage_10_decision_engine?.stop_loss || 0);

  const marketPrice = data?.latest_price || 0;
  const distanceToBuyPct = marketPrice > 0 && plannedBuyPrice > 0 
    ? ((plannedBuyPrice - marketPrice) / marketPrice) * 100 
    : 0;

  const targetGainPct = plannedBuyPrice > 0 && plannedTargetPrice > plannedBuyPrice
    ? ((plannedTargetPrice - plannedBuyPrice) / plannedBuyPrice) * 100
    : 0;

  const stopLossRiskPct = plannedBuyPrice > 0 && plannedStopLoss < plannedBuyPrice
    ? ((plannedBuyPrice - plannedStopLoss) / plannedBuyPrice) * 100
    : 0;

  const rewardVal = Math.abs(plannedTargetPrice - plannedBuyPrice);
  const riskVal = Math.abs(plannedBuyPrice - plannedStopLoss);
  const plannedRiskRewardRatio = riskVal > 0 ? (rewardVal / riskVal).toFixed(2) : "0.00";

  const plannedShares = plannedBuyPrice > 0 ? Math.max(1, Math.floor(100000 / plannedBuyPrice)) : 0;
  const plannedCapitalRequired = plannedShares * plannedBuyPrice;
  const plannedProfitAmt = plannedShares * rewardVal;
  const plannedLossAmt = plannedShares * riskVal;




  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col pb-16">
      {/* Navbar */}
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('intro')}>
              <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center shadow-sm">
                <BrainCircuit className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  QuantNova AI <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">13 STAGES</span>
                </h1>
                <p className="text-[11px] text-slate-500">Institutional Quantitative Research & AI Stock Intelligence Platform</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="hidden md:flex items-center space-x-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
              <button
                onClick={() => setActiveTab('intro')}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'intro'
                    ? "bg-white text-indigo-700 border border-slate-200 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Product Overview</span>
              </button>

              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-3 py-1.5 rounded-lg font-semibold transition-all flex items-center space-x-1.5 ${
                  activeTab === 'dashboard'
                    ? "bg-white text-indigo-700 border border-slate-200 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Live Dashboard</span>
              </button>
            </div>


          </div>

          {/* Search Form with Dropdown Autocomplete */}
          <div className="relative w-full md:w-auto">
            <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onFocus={() => searchInput.trim().length >= 2 && setShowDropdown(true)}
                  placeholder="Search any stock ticker or company name..."

                  className="w-full bg-white border border-slate-300 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 transition-colors shadow-sm"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs px-4 py-2.5 rounded-xl transition-all flex items-center space-x-1 shadow-sm"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Analyze</span>}
              </button>
            </form>

            {/* Autocomplete Dropdown */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute left-0 right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto divide-y divide-slate-100">
                {searchResults.map((item) => (
                  <div
                    key={item.symbol}
                    onClick={() => {
                      setSearchInput(item.symbol);
                      fetchAnalysis(item.symbol);
                    }}
                    className="p-3 hover:bg-slate-50 cursor-pointer flex justify-between items-center text-xs transition-colors"
                  >
                    <div>
                      <span className="font-bold text-slate-900 block">{item.symbol}</span>
                      <span className="text-slate-500 text-[11px]">{item.name}</span>
                    </div>
                    <span className="text-indigo-600 font-semibold text-[10px] px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100">NSE</span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        <div className="border-t border-b border-slate-200 bg-slate-900 text-white py-2.5 overflow-x-auto shadow-inner">
          <div className="flex items-center gap-3 px-4 whitespace-nowrap text-xs">
            <span className="text-slate-300 font-semibold">Quick analysis:</span>
            {[
              { label: 'Nifty 50', symbol: '^NSEI' },
              { label: 'BSE Sensex', symbol: '^BSESN' },
              { label: 'Bank Nifty', symbol: '^NSEBANK' },
              { label: 'Gold', symbol: 'GC=F' },
              { label: 'Crude Oil', symbol: 'CL=F' },
              { label: 'USD/INR', symbol: 'INR=X' },
              { label: 'Tata Motors', symbol: 'TMPV.NS' },
              { label: 'Reliance', symbol: 'RELIANCE.NS' },
            ].map(({ label, symbol }) => (
              <button key={symbol} type="button" disabled={loading} onClick={() => { setSearchInput(symbol); fetchAnalysis(symbol); setActiveTab('dashboard'); }} className="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 hover:border-indigo-400 disabled:opacity-50">
                {label} <span className="text-slate-400">{symbol}</span>
              </button>
            ))}
          </div>
        </div>

      </header>

      {error && (
        <div className="max-w-7xl mx-auto px-6 mt-4">
          <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center justify-between text-xs shadow-sm">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 font-bold ml-4">✕</button>
          </div>
        </div>
      )}


      {/* ========================================================================= */}
      {/* 1. 🌐 TAB 1: PLATFORM OVERVIEW & COMPREHENSIVE PROJECT GUIDE */}
      {/* ========================================================================= */}
      {activeTab === 'intro' && (
        <main className="max-w-7xl mx-auto px-6 mt-8 space-y-12 w-full animate-in fade-in duration-300">

          {/* Executive Company Hero Banner */}
          <div className="relative p-8 md:p-12 rounded-3xl bg-white border border-slate-200 shadow-sm overflow-hidden text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="space-y-4 max-w-2xl">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Institutional Stock Intelligence Platform</span>
              </div>
              <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
                Empowering Traders with <span className="text-indigo-600">10-Stage Quantitative</span> Research
              </h1>
              <p className="text-slate-600 text-sm md:text-base leading-relaxed">
                <strong>QuantNova AI</strong> is an institutional-grade quantitative research and stock intelligence engine. It combines multi-year market data ingestion, 25+ technical indicators, Random Forest machine learning models, fundamental financial audits, and interactive trade limit order simulation into one seamless platform formatted in Indian Rupees (<strong>₹</strong>).
              </p>
            </div>


            {/* Quick Stats Grid */}
            <div className="grid grid-cols-2 gap-4 w-full md:w-auto">
              <div className="p-5 rounded-2xl bg-indigo-50/70 border border-indigo-100 text-center">
                <div className="text-2xl font-black text-indigo-700">13</div>
                <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mt-1">Research Stages</div>
              </div>
              <div className="p-5 rounded-2xl bg-emerald-50/70 border border-emerald-100 text-center">
                <div className="text-2xl font-black text-emerald-700">25+</div>
                <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mt-1">Technical Indicators</div>
              </div>
              <div className="p-5 rounded-2xl bg-blue-50/70 border border-blue-100 text-center">
                <div className="text-2xl font-black text-blue-700">0ms</div>
                <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mt-1">Timeframe Latency</div>
              </div>
              <div className="p-5 rounded-2xl bg-amber-50/70 border border-amber-100 text-center">
                <div className="text-2xl font-black text-amber-700">₹ Rupee</div>
                <div className="text-xs font-bold text-slate-600 uppercase tracking-wider mt-1">Standard Currency</div>
              </div>
            </div>
          </div>

          {/* 5-Step Website User Guide: How to Run & Use This Platform */}
          <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
              <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center">
                <Compass className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">How to Run & Use This Platform (5-Step User Guide)</h2>
                <p className="text-xs text-slate-500">Step-by-step workflow to analyze any stock and simulate pending trade scenarios</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              {/* Step 1 */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white font-extrabold text-xs flex items-center justify-center">1</div>
                <h3 className="text-sm font-bold text-slate-900">Search Any Stock</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Type any Indian or global stock ticker (e.g., <code className="text-indigo-600 font-bold">TMPV.NS</code>, <code className="text-indigo-600 font-bold">RELIANCE.NS</code>, <code className="text-indigo-600 font-bold">^NSEI</code>) in the top search bar or click any ticker item in the live continuous marquee feed.
                </p>
              </div>

              {/* Step 2 */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white font-extrabold text-xs flex items-center justify-center">2</div>
                <h3 className="text-sm font-bold text-slate-900">Instant Timeframe Slicing</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Select your desired analysis horizon (<code className="text-emerald-700 font-bold">1m</code>, <code className="text-emerald-700 font-bold">2m</code>, <code className="text-emerald-700 font-bold">3m</code>, <code className="text-emerald-700 font-bold">1y</code>, <code className="text-emerald-700 font-bold">5y</code>) for instant 0ms client-side dataset slicing with zero screen reload latency.
                </p>
              </div>

              {/* Step 3 */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-8 h-8 rounded-xl bg-blue-600 text-white font-extrabold text-xs flex items-center justify-center">3</div>
                <h3 className="text-sm font-bold text-slate-900">Quantitative Signal & Data Audit</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Inspect the quantitative decision engine recommendation (<strong className="text-emerald-600">BUY</strong>, <strong className="text-rose-600">SELL</strong>, <strong className="text-amber-600">HOLD</strong>), confidence score, technical indicator ratings, and market-data audit metrics.
                </p>
              </div>

              {/* Step 4 */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-8 h-8 rounded-xl bg-amber-600 text-white font-extrabold text-xs flex items-center justify-center">4</div>
                <h3 className="text-sm font-bold text-slate-900">Simulate Pending Limit Orders</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Input your custom Planned Buy Limit Price, Target Sell Level, and Stop Loss Price to instantly simulate Risk:Reward ratios and potential P&L in Indian Rupees (<strong className="text-amber-700">₹</strong>).
                </p>
              </div>

              {/* Step 5 */}
              <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="w-8 h-8 rounded-xl bg-violet-600 text-white font-extrabold text-xs flex items-center justify-center">5</div>
                <h3 className="text-sm font-bold text-slate-900">Interactive Plotly Visuals</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Analyze synchronized 5-subplot Candlestick charts, RSI, MACD, Volume, SuperTrend, and Strategy vs Buy-and-Hold Equity Curve performance.
                </p>
              </div>
            </div>
          </div>

          {/* Quantitative Science & Business Thesis Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Quantitative Theory Card */}
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-indigo-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">The Quantitative Theory & Science</h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                <strong>QuantNova AI</strong> runs a ten-step quantitative analysis over provider-sourced daily market data, validates OHLCV records, and calculates technical indicators. Incomplete OHLCV rows are excluded rather than filled with invented prices or volume.
              </p>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex items-start space-x-2">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span><strong>Random Forest Classifier:</strong> Predicts directional momentum across multi-day horizons.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span><strong>SuperTrend & Moving Averages:</strong> Identifies macro trend regimes and dynamic support/resistance zones.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span><strong>Relative Strength vs Nifty 50:</strong> Evaluates sector leadership and benchmark relative strength outperformance.</span>
                </li>
              </ul>
            </div>

            {/* Core Business Thesis Card */}
            <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-emerald-600" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">The Core Business Thesis</h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Our business mission is to democratize institutional-grade quantitative research for individual investors and professional analysts in India.
              </p>
              <ul className="space-y-2 text-xs text-slate-700">
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span><strong>100% Explainable AI Decisions:</strong> Every rating includes clear Pros, Cons, and Key Investment Risks without black-box opacity.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span><strong>Strict Currency Standardization:</strong> All metrics, execution limits, and commodity benchmarks are formatted in Indian Rupees (<strong>₹</strong>).</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-600 font-bold">•</span>
                  <span><strong>Zero Latency Performance:</strong> Bypasses external network delays with instant symbol resolution and local client-side dataset slicing.</span>
                </li>
              </ul>
            </div>
          </div>
        </main>
      )}


      {/* ========================================================================= */}
      {/* 📊 LIVE DASHBOARD: UNIFIED SINGLE-PAGE PRO TRADING TERMINAL */}
      {/* ========================================================================= */}
      {activeTab === 'dashboard' && loading && (
        <main className="max-w-7xl mx-auto px-6 mt-16 flex flex-col items-center justify-center space-y-4 w-full py-20">
          <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-600 text-sm font-medium animate-pulse">Running quantitative research for {ticker}…</p>
        </main>
      )}

      {activeTab === 'dashboard' && !loading && !data && error && (
        <main className="max-w-7xl mx-auto px-6 mt-16 flex flex-col items-center justify-center space-y-4 w-full py-20">
          <AlertTriangle className="w-10 h-10 text-rose-500" />
          <p className="text-slate-700 text-sm">Analysis could not be completed.</p>
          <button onClick={() => fetchAnalysis(searchInput.trim() || ticker, selectedPeriod)} className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm px-4 py-2 rounded-xl">Retry analysis</button>
        </main>
      )}

      {activeTab === 'dashboard' && !loading && !data && !error && (
        <main className="max-w-7xl mx-auto px-6 mt-16 flex flex-col items-center justify-center space-y-4 w-full py-20">
          <BarChart3 className="w-10 h-10 text-indigo-500" />
          <p className="text-slate-700 text-sm">Search for a symbol and select Analyze to run the quantitative research pipeline.</p>
        </main>
      )}

      {data && activeTab === 'dashboard' && (

        <main className="max-w-7xl mx-auto px-6 mt-8 space-y-8 w-full animate-in fade-in duration-200">
          {/* Prominent & Elegant Timeframe Selection Control Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center space-x-2">
              <Compass className="w-5 h-5 text-indigo-600" />
              <span className="font-bold text-slate-900 text-sm">Select Analysis Timeframe:</span>
            </div>

            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              {[
                { label: "1m", val: "1m" },
                { label: "2m", val: "2m" },
                { label: "3m", val: "3m" },
                { label: "1y", val: "1y" },
                { label: "5y", val: "5y" }
              ].map((tf) => (
                <button
                  key={tf.val}
                  onClick={() => handlePeriodChange(tf.val)}
                  className={`px-4 py-2 rounded-xl font-bold text-xs transition-all flex items-center space-x-1 border ${
                    selectedPeriod === tf.val
                      ? "bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-100 scale-105"
                      : "bg-slate-50 text-slate-700 hover:bg-slate-100 border-slate-200"
                  }`}
                >
                  <span>{tf.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Product Executive Overview Hero Section */}
          <div className="p-6 md:p-8 rounded-3xl bg-white border border-slate-200 shadow-sm relative overflow-hidden space-y-6">
            {/* Overview Header & Title Bar */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-6 border-b border-slate-100">
              <div className="space-y-2">
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Product Executive Overview</span>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="text-3xl font-black text-slate-900 tracking-tight">{data.symbol}</h1>
                  <span className="text-sm font-semibold text-slate-700 px-3 py-1 rounded-full bg-slate-100 border border-slate-200">
                    {data.company_name}
                  </span>
                  <span className="text-xs font-bold text-indigo-700 px-2.5 py-0.5 rounded-md bg-indigo-50 border border-indigo-200">
                    {data.symbol.endsWith('.NS') ? 'NSE' : data.symbol.endsWith('.BO') ? 'BSE' : 'Yahoo Finance symbol'}
                  </span>
                </div>
                <div className="text-xs text-slate-500 flex flex-wrap items-center gap-3 pt-1">
                  <span>Sector: <strong className="text-slate-800">{data.sector}</strong></span>
                  <span>•</span>
                  <span>Latest close: <strong className="text-slate-900 text-sm">₹{data.latest_price.toFixed(2)}</strong></span>
                  <span>•</span>
                  <span>As of: <strong className="text-slate-800">{data.date}</strong></span>
                  <span>•</span>
                  <span>Source: <strong className="text-slate-800">{data.market_data_source === 'postgresql_cache' ? 'PostgreSQL cache' : 'Yahoo Finance'}</strong></span>
                </div>
              </div>

              {/* Recommendation & Confidence Score Badges */}
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-[11px] uppercase tracking-widest font-bold text-slate-500">AI Signal Rating</div>
                  <div className={`text-4xl font-black tracking-tight ${
                    data.stage_10_decision_engine.signal.includes("BUY")
                      ? "text-emerald-600"
                      : data.stage_10_decision_engine.signal.includes("SELL")
                      ? "text-rose-600"
                      : "text-amber-600"
                  }`}>
                    {data.stage_10_decision_engine.signal}
                  </div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-center min-w-[110px]">
                  <div className="text-[10px] uppercase font-bold text-slate-500">Confidence</div>
                  <div className="text-2xl font-black text-indigo-600">{data.stage_10_decision_engine.confidence_score}%</div>
                  <div className="text-[10px] font-semibold text-amber-700">{data.stage_10_decision_engine.risk_level}</div>
                </div>
              </div>
            </div>


            {/* Trade Order Planning & Pending Limit Scenario Simulator Bar */}
            <div className="mt-6 p-5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col space-y-4 text-xs">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-3 border-b border-slate-200">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center">
                    <Calculator className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 text-sm block">Pending Order & Trade Scenario Planner</span>
                    <span className="text-[11px] text-slate-500">Set your planned Buy Limit Price, Target Sell Price & Stop Loss level to simulate trade risk/reward:</span>
                  </div>
                </div>

                {/* Interactive Numeric Inputs */}
                <div className="flex flex-wrap items-center gap-3 w-full md:w-auto justify-end">
                  <div className="flex items-center space-x-1.5 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm">
                    <span className="font-semibold text-slate-600 text-[11px]">1. Planned Buy (₹):</span>
                    <input
                      type="number"
                      step="0.05"
                      value={customPriceInput}
                      onChange={(e) => setCustomPriceInput(e.target.value)}
                      placeholder="Buy Price"
                      className="w-28 bg-slate-50 border border-emerald-300 rounded-lg px-2 py-1 text-xs font-bold text-emerald-700 focus:outline-none text-right"
                    />
                  </div>

                  <div className="flex items-center space-x-1.5 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm">
                    <span className="font-semibold text-slate-600 text-[11px]">2. Target Sell (₹):</span>
                    <input
                      type="number"
                      step="0.05"
                      value={customTargetInput}
                      onChange={(e) => setCustomTargetInput(e.target.value)}
                      placeholder="Target Price"
                      className="w-28 bg-slate-50 border border-blue-300 rounded-lg px-2 py-1 text-xs font-bold text-blue-700 focus:outline-none text-right"
                    />
                  </div>

                  <div className="flex items-center space-x-1.5 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm">
                    <span className="font-semibold text-slate-600 text-[11px]">3. Stop Loss (₹):</span>
                    <input
                      type="number"
                      step="0.05"
                      value={customStopLossInput}
                      onChange={(e) => setCustomStopLossInput(e.target.value)}
                      placeholder="Stop Loss"
                      className="w-28 bg-slate-50 border border-rose-300 rounded-lg px-2 py-1 text-xs font-bold text-rose-700 focus:outline-none text-right"
                    />
                  </div>
                </div>
              </div>

              {/* Dynamic Derivations Grid */}
              <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-center">
                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Buy Trigger Distance</span>
                  <span className={`text-xs font-extrabold ${distanceToBuyPct <= 0 ? 'text-amber-700' : 'text-blue-700'}`}>
                    {distanceToBuyPct === 0 ? "At Market Price" : distanceToBuyPct < 0 ? `${distanceToBuyPct.toFixed(2)}% below close` : `+${distanceToBuyPct.toFixed(2)}% above close`}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Planned Target Gain %</span>
                  <span className="text-xs font-extrabold text-emerald-600">
                    +{targetGainPct.toFixed(2)}%
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Planned Stop Risk %</span>
                  <span className="text-xs font-extrabold text-rose-600">
                    -{stopLossRiskPct.toFixed(2)}%
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Planned Risk / Reward</span>
                  <span className="text-xs font-extrabold text-indigo-700">1:{plannedRiskRewardRatio}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Potential Profit (₹100k)</span>
                  <span className="text-xs font-extrabold text-emerald-600">+₹{plannedProfitAmt.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-slate-200 shadow-sm">
                  <span className="text-[10px] text-slate-500 block mb-0.5">Potential Loss (₹100k)</span>
                  <span className="text-xs font-extrabold text-rose-600">-₹{plannedLossAmt.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                </div>
              </div>

              {/* Trade Workflow Note */}
              <div className="pt-2 text-[11px] text-slate-500 border-t border-slate-200 flex items-center justify-between">
                <span>
                  💡 <strong>Pending Order Logic:</strong> When market price hits <strong>₹{plannedBuyPrice.toFixed(2)}</strong>, buy order triggers. If price moves up to <strong>₹{plannedTargetPrice.toFixed(2)}</strong>, target profit is executed. If price falls to <strong>₹{plannedStopLoss.toFixed(2)}</strong>, stop-loss exits trade.
                </span>
                <span className="font-semibold text-slate-700">Capital Required: ₹{plannedCapitalRequired.toLocaleString('en-IN', { maximumFractionDigits: 0 })} ({plannedShares} Shares)</span>
              </div>
            </div>

            {/* Score Metrics Grid */}
            <div className="mt-6 pt-6 border-t border-slate-200 grid grid-cols-2 md:grid-cols-5 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block mb-1">Technical Score</span>
                <span className="text-xl font-extrabold text-indigo-700">{data.stage_10_decision_engine.technical_score} / 100</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block mb-1">Fundamental Score</span>
          <span className="text-xl font-extrabold text-blue-700">{data.stage_10_decision_engine.fundamental_score ?? 'Unavailable'}{data.stage_10_decision_engine.fundamental_score !== null ? ' / 100' : ''}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block mb-1">Risk Score</span>
                <span className="text-xl font-extrabold text-rose-600">{data.stage_10_decision_engine.risk_score} / 100</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block mb-1">Suggested Entry</span>
                <span className="text-xl font-extrabold text-emerald-600">₹{plannedBuyPrice.toFixed(2)}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-slate-500 block mb-1">Target / Stop Loss</span>
                <span className="text-xs font-bold text-slate-800 block">₹{plannedTargetPrice.toFixed(2)} / ₹{plannedStopLoss.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Quantitative analysis stages */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Stage 1 & 2 Card */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                <Layers className="w-4 h-4 text-indigo-600" />
                <span>Stage 1 & 2: Audit</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Downloaded Days</span>
                  <span className="font-semibold text-slate-900">{data.stage_1_collection.records_count}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Duplicates Removed</span>
                  <span className="font-semibold text-emerald-600">{data.stage_2_cleaning["Duplicates Removed"]}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Incomplete Rows Excluded</span>
                  <span className="font-semibold text-emerald-600">{data.stage_2_cleaning["Rows Excluded for Missing Values"]}</span>
                </div>
              </div>
            </div>

            {/* Stage 3 Technicals Card */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                <Activity className="w-4 h-4 text-blue-600" />
                <span>Stage 3: Technicals</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">RSI (14)</span>
                <span className="font-semibold text-pink-600">{data.stage_3_indicators.rsi ?? 'Unavailable'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">SuperTrend</span>
                <span className="font-semibold text-emerald-600">{data.stage_3_indicators.supertrend == null ? 'Unavailable' : `₹${data.stage_3_indicators.supertrend}`}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Pivot S1 / R1</span>
                <span className="font-semibold text-slate-800">{data.stage_3_indicators.support1 == null || data.stage_3_indicators.resistance1 == null ? 'Unavailable' : `₹${data.stage_3_indicators.support1} / ₹${data.stage_3_indicators.resistance1}`}</span>
                </div>
              </div>
            </div>

            {/* Stage 4 Trend Card */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                <TrendingUp className="w-4 h-4 text-amber-600" />
                <span>Stage 4: Trend</span>
              </div>
              <div className="text-base font-bold text-slate-900 mb-1">{data.stage_4_trend.classification}</div>
              <p className="text-[11px] text-slate-500 leading-tight truncate" title={data.stage_4_trend.reason}>{data.stage_4_trend.reason}</p>
            </div>

            {/* Stage 6 Market Context Card */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                <Compass className="w-4 h-4 text-indigo-600" />
                <span>Stage 6: Market Context</span>
              </div>
              <div className="text-sm font-bold text-slate-900 mb-1">Nifty RS: {data.stage_6_market_context["Relative Strength Rating"] ?? 'Unavailable'}{data.stage_6_market_context["Relative Strength Rating"] !== null ? '/99' : ''}</div>
              <p className="text-[11px] text-slate-500 leading-tight truncate" title={data.stage_6_market_context["Market Context Explanation"]}>{data.stage_6_market_context["Nifty Market Trend"]}</p>
            </div>
          </div>

          {/* Pros, Cons, and Key Risks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
            <div className="p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200">
              <div className="flex items-center space-x-2 font-bold text-emerald-800 mb-3 uppercase tracking-wider">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Investment Pros</span>
              </div>
              <ul className="space-y-2 text-slate-700">
                {data.stage_10_decision_engine.pros.map((p, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-amber-50/60 border border-amber-200">
              <div className="flex items-center space-x-2 font-bold text-amber-800 mb-3 uppercase tracking-wider">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Cons & Friction Points</span>
              </div>
              <ul className="space-y-2 text-slate-700">
                {data.stage_10_decision_engine.cons.map((c, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-5 rounded-2xl bg-rose-50/60 border border-rose-200">
              <div className="flex items-center space-x-2 font-bold text-rose-800 mb-3 uppercase tracking-wider">
                <Shield className="w-4 h-4 text-rose-600" />
                <span>Key Investment Risks</span>
              </div>
              <ul className="space-y-2 text-slate-700">
                {data.stage_10_decision_engine.risks.map((r, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="text-rose-600 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Interactive Plotly 5-Subplot Visual Chart */}
          <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-indigo-600" />
              <span>Interactive Price, Indicator & Backtest Dashboard</span>
            </h2>
            <div className="w-full overflow-hidden">
              <Plot
                data={[
                  {
                    x: data.chart_series.dates,
                    open: data.chart_series.open,
                    high: data.chart_series.high,
                    low: data.chart_series.low,
                    close: data.chart_series.close,
                    type: 'candlestick',
                    name: 'OHLC Price',
                    yaxis: 'y1'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.sma20,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'SMA 20',
                    line: { color: '#d97706', width: 1.5 },
                    yaxis: 'y1'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.sma50,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'SMA 50',
                    line: { color: '#2563eb', width: 1.5 },
                    yaxis: 'y1'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.volume,
                    type: 'bar',
                    name: 'Volume',
                    marker: { color: data.chart_series.close.map((c, idx) => (c >= data.chart_series.open[idx] ? '#16a34a' : '#dc2626')) },
                    yaxis: 'y2'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.rsi,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'RSI (14)',
                    line: { color: '#db2777', width: 1.5 },
                    yaxis: 'y3'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.macd,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'MACD',
                    line: { color: '#0891b2', width: 1.5 },
                    yaxis: 'y4'
                  },
                  {
                    x: data.chart_series.dates,
                    y: data.chart_series.strategy_equity,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'Strategy Equity (₹)',
                    line: { color: '#16a34a', width: 2 },
                    yaxis: 'y5'
                  }
                ]}
                layout={{
                  grid: { rows: 5, columns: 1, pattern: 'independent' },
                  template: 'plotly_white',
                  paper_bgcolor: '#ffffff',
                  plot_bgcolor: '#ffffff',
                  font: { family: 'Inter, sans-serif', color: '#1e293b' },
                  height: 1000,
                  margin: { l: 40, r: 40, t: 40, b: 40 },
                  xaxis: { rangeslider: { visible: false } },
                  yaxis1: { domain: [0.60, 1.0], title: 'Price (₹)' },
                  yaxis2: { domain: [0.45, 0.57], title: 'Volume' },
                  yaxis3: { domain: [0.30, 0.42], title: 'RSI' },
                  yaxis4: { domain: [0.15, 0.27], title: 'MACD' },
                  yaxis5: { domain: [0.0, 0.12], title: 'Equity (₹)' },
                  showlegend: true,
                  legend: { orientation: 'h', y: 1.02 }
                }}
                useResizeHandler={true}
                className="w-full h-auto"
              />
            </div>
          </div>

          {/* Stage 5: Fundamentals & Stage 10: Backtest Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Fundamental Financials Table */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Award className="w-5 h-5 text-amber-600" />
                <span>Stage 5: Fundamental Analysis & Financial Health</span>
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-2 border-b border-slate-100">
                  <span className="text-slate-500">Revenue Growth (YoY)</span>
                  <span className="font-semibold text-slate-900">{displayOptional(data.stage_5_fundamentals["Revenue Growth (%)"])}{data.stage_5_fundamentals["Revenue Growth (%)"] == null ? '' : '%'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-100">
                  <span className="text-slate-500">Profit Growth (YoY)</span>
                  <span className="font-semibold text-slate-900">{displayOptional(data.stage_5_fundamentals["Profit Growth (%)"])}{data.stage_5_fundamentals["Profit Growth (%)"] == null ? '' : '%'}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-100">
                  <span className="text-slate-500">P/E Ratio</span>
                  <span className="font-semibold text-slate-900">{displayOptional(data.stage_5_fundamentals["PE Ratio"])}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-100">
                  <span className="text-slate-500">P/B Ratio</span>
                  <span className="font-semibold text-slate-900">{displayOptional(data.stage_5_fundamentals["PB Ratio"])}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-slate-100">
                  <span className="text-slate-500">ROE %</span>
                  <span className="font-semibold text-indigo-700">{displayOptional(data.stage_5_fundamentals["ROE (%)"])}{data.stage_5_fundamentals["ROE (%)"] == null ? '' : '%'}</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-slate-500">Promoter Holding</span>
                  <span className="font-semibold text-indigo-700">{displayOptional(data.stage_5_fundamentals["Promoter Holding (%)"])}{data.stage_5_fundamentals["Promoter Holding (%)"] == null ? '' : '%'}</span>
                </div>
              </div>
            </div>

            {/* Backtest Strategy Metrics Table */}
            <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                <span>Stage 10: Strategy Backtest vs Buy-and-Hold Benchmark</span>
              </h3>
              <div className="overflow-x-auto text-xs">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
                      <th className="py-2">Metric</th>
                      <th className="py-2">Strategy</th>
                      <th className="py-2">Benchmark</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.stage_8_backtesting.metrics.map((m: any, idx: number) => (
                      <tr key={idx}>
                        <td className="py-2 font-medium text-slate-600">{m["Performance Metric"]}</td>
                        <td className="py-2 font-bold text-indigo-700">{m["Quantitative Signal Strategy"]}</td>
                        <td className="py-2 font-medium text-slate-500">{m["Buy-and-Hold Benchmark"]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* ========================================================================= */}
      {/* 📊 INTERACTIVE LIVE EXCEL SHEET DATA VIEWER MODAL */}
      {/* ========================================================================= */}
      {showExcelViewerModal && (
        <div className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
                  <FileSpreadsheet className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    QuantNova AI — Interactive Live Excel Sheet Data
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 font-bold">
                      11 Sheets Ready
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-500">Live Data Table Viewer for {data?.symbol || ticker} ({data?.company_name || "Asset"}) — Download on demand when ready</p>
                </div>
              </div>

              <div className="flex items-center space-x-3 w-full md:w-auto justify-end">
                {/* Download Button inside Modal */}
                <button
                  onClick={handleDownloadExcelDirect}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition-all flex items-center space-x-2 shadow-sm"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>Download Excel File (.xlsx)</span>
                </button>
                <button
                  onClick={() => setShowExcelViewerModal(false)}
                  className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Interactive Excel Sheet Tabs & Timeframe Filter */}
            <div className="border-b border-slate-200 bg-white px-4 py-2 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-2 overflow-x-auto">
                <button
                  onClick={() => setExcelTab('ohlcv')}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    excelTab === 'ohlcv'
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  📊 Sheet 1: Daily OHLCV Price & Volume History
                </button>
                <button
                  onClick={() => setExcelTab('indicators')}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    excelTab === 'indicators'
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  📈 Sheet 2: 25+ Technical Indicators Audit
                </button>
                <button
                  onClick={() => setExcelTab('fundamentals')}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    excelTab === 'fundamentals'
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  🏢 Sheet 3: Fundamental Ratios & Health
                </button>
                <button
                  onClick={() => setExcelTab('backtest')}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    excelTab === 'backtest'
                      ? "bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-sm"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  🎯 Sheet 4: Strategy Backtest & Trade Logs
                </button>
              </div>

              {/* Timeframe Filter in Modal Header */}
              <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl">
                <span className="text-slate-500 font-bold text-[10px] uppercase px-1">Filter Range:</span>
                {[
                  { label: "1M", val: "1m" },
                  { label: "3M", val: "3m" },
                  { label: "1Y (This Year)", val: "1y" },
                  { label: "5Y", val: "5y" },
                  { label: "MAX", val: "max" }
                ].map((tf) => (
                  <button
                    key={tf.val}
                    onClick={() => handlePeriodChange(tf.val)}
                    className={`px-2 py-0.5 rounded-lg font-bold text-[10px] transition-all ${
                      selectedPeriod === tf.val
                        ? "bg-emerald-600 text-white shadow-sm"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Live Data Sheet Content Table */}
            <div className="flex-1 overflow-auto p-4 bg-slate-50">
              {data && excelTab === 'ohlcv' && (
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 text-[11px] uppercase tracking-wider">
                        <th className="p-3">Date</th>
                        <th className="p-3 text-right">Open (₹)</th>
                        <th className="p-3 text-right">High (₹)</th>
                        <th className="p-3 text-right">Low (₹)</th>
                        <th className="p-3 text-right">Close (₹)</th>
                        <th className="p-3 text-right">Volume</th>
                        <th className="p-3 text-center">Signal</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                      {data.chart_series.dates.map((d: string, actualIdx: number) => {
                        const c = data.chart_series.close[actualIdx];
                        const o = data.chart_series.open[actualIdx];
                        const h = data.chart_series.high[actualIdx];
                        const l = data.chart_series.low[actualIdx];
                        const v = data.chart_series.volume[actualIdx];
                        const sig = data.chart_series.signals[actualIdx] || "HOLD";
                        return (
                          <tr key={actualIdx} className="hover:bg-slate-50">
                            <td className="p-3 font-semibold text-slate-800">{d}</td>
                            <td className="p-3 text-right text-slate-700">₹{o?.toFixed(2)}</td>
                            <td className="p-3 text-right text-emerald-700">₹{h?.toFixed(2)}</td>
                            <td className="p-3 text-right text-rose-700">₹{l?.toFixed(2)}</td>
                            <td className="p-3 text-right font-bold text-slate-900">₹{c?.toFixed(2)}</td>
                            <td className="p-3 text-right text-slate-600">{v?.toLocaleString('en-IN')}</td>
                            <td className="p-3 text-center">
                              <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                                sig.includes('BUY') ? 'bg-emerald-100 text-emerald-800' : sig.includes('SELL') ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-700'
                              }`}>
                                {sig}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {data && excelTab === 'indicators' && (
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 text-[11px] uppercase tracking-wider">
                        <th className="p-3">Date</th>
                        <th className="p-3 text-right">Close</th>
                        <th className="p-3 text-right">SMA 20</th>
                        <th className="p-3 text-right">SMA 50</th>
                        <th className="p-3 text-right">RSI (14)</th>
                        <th className="p-3 text-right">MACD</th>
                        <th className="p-3 text-right">SuperTrend</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                      {data.chart_series.dates.map((d: string, actualIdx: number) => {
                        return (
                          <tr key={actualIdx} className="hover:bg-slate-50">
                            <td className="p-3 font-semibold text-slate-800">{d}</td>
                            <td className="p-3 text-right font-bold text-slate-900">₹{data.chart_series.close[actualIdx]?.toFixed(2)}</td>
                            <td className="p-3 text-right text-amber-700">₹{data.chart_series.sma20[actualIdx]?.toFixed(2)}</td>
                            <td className="p-3 text-right text-blue-700">₹{data.chart_series.sma50[actualIdx]?.toFixed(2)}</td>
                            <td className="p-3 text-right text-pink-700 font-bold">{data.chart_series.rsi[actualIdx]?.toFixed(2)}</td>
                            <td className="p-3 text-right text-cyan-700">{data.chart_series.macd[actualIdx]?.toFixed(2)}</td>
                            <td className="p-3 text-right text-emerald-700 font-bold">₹{data.chart_series.supertrend[actualIdx]?.toFixed(2)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {data && excelTab === 'fundamentals' && (
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-4">
                  <h4 className="font-bold text-slate-900 text-sm">Fundamental Financial Metrics & Health Audit</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(data.stage_5_fundamentals).map(([k, v]) => (
                      <div key={k} className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                        <span className="text-slate-500 text-[11px] block">{k}</span>
                        <span className="text-base font-extrabold text-indigo-700">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {data && excelTab === 'backtest' && (
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-4">
                  <h4 className="font-bold text-slate-900 text-sm">Backtest Performance Strategy Metrics vs Benchmark</h4>
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-bold text-[11px] uppercase">
                        <th className="py-2">Metric</th>
                        <th className="py-2 text-indigo-700">Strategy</th>
                        <th className="py-2 text-slate-500">Buy & Hold Benchmark</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.stage_8_backtesting.metrics.map((m: any, idx: number) => (
                        <tr key={idx}>
                          <td className="py-2.5 font-medium text-slate-700">{m["Performance Metric"]}</td>
                          <td className="py-2.5 font-extrabold text-indigo-700">{m["Quantitative Signal Strategy"]}</td>
                          <td className="py-2.5 font-medium text-slate-500">{m["Buy-and-Hold Benchmark"]}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 📄 INTERACTIVE LIVE PDF REPORT PREVIEW MODAL */}
      {/* ========================================================================= */}
      {showPdfViewerModal && (
        <div className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-3xl w-full max-w-5xl h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    QuantNova AI — PDF Report Live Preview
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 font-bold border border-indigo-200">
                      4 Pages PDF
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-500">Viewing PDF Report inline for {data?.symbol || ticker} — Download on demand when ready</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleDownloadPDFDirect}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition-all flex items-center space-x-1.5 shadow-sm"
                >
                  <FileText className="w-4 h-4" />
                  <span>Download PDF File (.pdf)</span>
                </button>
                <button
                  onClick={() => setShowPdfViewerModal(false)}
                  className="p-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Embedded PDF Viewer Iframe */}
            <div className="flex-1 bg-slate-100">
              <iframe
                src={`${API_BASE_URL}/api/export/pdf?symbol=${encodeURIComponent(data?.symbol || ticker)}&split_pages=true&inline=true`}
                className="w-full h-full border-0"
                title="PDF Report Live Preview"
              />
            </div>
          </div>
        </div>
      )}


      {/* Floating Bottom-Centered Navigation Pill Bar */}


      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-slate-900/95 text-white backdrop-blur-md px-3.5 py-2 rounded-2xl border border-slate-700 shadow-2xl flex items-center space-x-2 text-xs font-bold">
        <button
          onClick={() => setActiveTab('intro')}
          className={`px-4 py-2 rounded-xl transition-all flex items-center space-x-2 ${
            activeTab === 'intro'
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/30 scale-105"
              : "text-slate-300 hover:text-white hover:bg-slate-800"
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>Product Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-4 py-2 rounded-xl transition-all flex items-center space-x-2 ${
            activeTab === 'dashboard'
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-500/30 scale-105"
              : "text-slate-300 hover:text-white hover:bg-slate-800"
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Live Dashboard</span>
        </button>
      </div>
    </div>
  );
}

