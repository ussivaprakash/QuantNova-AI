# QuantNova AI — Quantitative Stock Research & Intelligence Platform

**QuantNova AI** is an institutional 13-stage quantitative stock research, market forecasting, and scenario planning web application for Indian Stock Markets (NSE & BSE).

---

## 🚀 Separate Modular Architecture

The repository is organized into distinct **Frontend** and **Backend** directories:

```text
stock_market_analysis/
├── backend/                  # Python FastAPI Quantitative Engine
│   ├── api.py               # REST API Server (Endpoints for search, analysis, exports)
│   ├── data_loader.py       # Stage 1: Yahoo Finance Market Data Ingestion
│   ├── data_cleaner.py      # Stage 2: Data Audit & Sanitization
│   ├── indicators.py        # Stage 3: 25+ Technical Indicators (RSI, MACD, SuperTrend, Pivots)
│   ├── trend_analysis.py    # Stage 4: 5-Tier Trend Classification Engine
│   ├── fundamentals.py      # Stage 5: Financial Ratios & Fundamental Health Score
│   ├── market_context.py    # Stage 6: Nifty 50 Relative Strength & Sector Context
│   ├── predictor.py         # Stage 7: Random Forest Machine Learning Classifier
│   ├── backtester.py        # Stage 8: Historical Backtesting Engine vs Buy-and-Hold
│   ├── risk_analysis.py     # Stage 9: Volatility & Position Sizing Engine
│   ├── signal_engine.py     # Stage 10: Explainable Signal Engine (Pros/Cons/Risks)
│   ├── pdf_exporter.py      # Stage 11: Professional ReportLab PDF Report Generator
│   ├── dashboard.py         # Stage 12: 11-Sheet Excel & Plotly Dashboard Engine
│   └── main.py              # CLI Master Pipeline Runner
│
├── frontend/                 # Vite + React + TypeScript + Tailwind Web Application
│   ├── src/
│   │   ├── App.tsx          # QuantNova AI Dashboard & Scenario Simulator
│   │   ├── main.tsx         # Application Entry Point
│   │   └── index.css        # Tailwind & Glassmorphism Design System
│   ├── index.html           # Document Title & Meta Config
│   └── package.json         # Frontend Dependencies
│
├── start_app.sh              # Single-Command Application Launcher Script
└── README.md                # Platform Documentation
```

---

## 🏃 Quick Start Guide

### 1. Launch Everything via Launcher Script

```bash
chmod +x start_app.sh
./start_app.sh
```

### 2. Run Backend & Frontend Separately

**Backend Server (Port 8000)**:
```bash
cd backend
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Frontend UI (Port 5173)**:
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 🌐 Endpoints & Web Services

- 🎨 **QuantNova AI Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- ⚡ **Backend REST API**: [http://localhost:8000](http://localhost:8000)
- 📝 **OpenAPI Swagger Specs**: [http://localhost:8000/docs](http://localhost:8000/docs)
