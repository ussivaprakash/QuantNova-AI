# QuantNova AI — Quantitative Stock Research & Intelligence Platform

**QuantNova AI** is an institutional quantitative stock research, market forecasting, and scenario planning platform for Indian Stock Markets (NSE & BSE) powered by FastAPI, PostgreSQL, and React.

---

## 🚀 Separate Modular Architecture

The repository is organized into distinct **Frontend**, **Backend**, and **Database** layers:

```text
stock_market_analysis/
├── backend/                  # Python FastAPI Quantitative Engine
│   ├── api.py               # REST API Server with DB Dependency Injection
│   ├── config.py            # Environment & Settings Management (Pydantic / .env)
│   ├── database.py          # SQLAlchemy 2.0 Engine & Connection Pooling
│   ├── models/              # Declarative SQLAlchemy ORM Models
│   │   ├── stock.py         # Equities master catalog (NSE/BSE)
│   │   ├── market_data.py   # Daily OHLCV time-series (scalable to millions of rows)
│   │   ├── fundamentals.py  # Quarterly/annual financial ratios & health scores
│   │   ├── analysis.py      # Quantitative pipeline runs & ML predictions
│   │   ├── signals.py       # BUY/HOLD/SELL trade recommendations & target levels
│   │   ├── risk.py          # Volatility & Kelly position sizing assessments
│   │   └── ai_research.py   # Chatbot queries, intent classification & research plans
│   ├── schemas/             # Pydantic validation models (Request/Response)
│   ├── repositories/        # Clean Data Access Layer (CRUD)
│   ├── migrations/          # Alembic database migrations
│   │   ├── versions/        # Migration version scripts
│   │   └── env.py           # Migration environment runner
│   ├── seed.py              # Sample database seeder for top Indian equities
│   ├── alembic.ini          # Alembic migration configuration
│   ├── data_loader.py       # Stage 1: Market Data Ingestion & DB Cache
│   ├── data_cleaner.py      # Stage 2: Data Audit & Sanitization
│   ├── indicators.py        # Stage 3: Technical Indicators (RSI, MACD, SuperTrend)
│   ├── trend_analysis.py    # Stage 4: Trend Classification
│   ├── fundamentals.py      # Stage 5: Financial Ratios & Fundamental Health
│   ├── market_context.py    # Stage 6: Benchmark Context
│   ├── predictor.py         # Stage 7: Random Forest Classifier
│   ├── signal_engine.py     # Stage 8: Trading Signal Engine
│   ├── risk_analysis.py     # Stage 9: Volatility & Position Sizing
│   ├── backtester.py        # Stage 10: Historical Strategy Backtest
│   ├── pdf_exporter.py      # On-demand PDF report generation
│   ├── dashboard.py         # On-demand Excel and Plotly report generation
│   └── main.py              # CLI Master Pipeline Runner
│
├── frontend/                 # Vite + React + TypeScript + Tailwind Web Application
├── .env.example             # Environment configuration template
├── requirements.txt         # Production backend dependencies
├── start_app.sh             # Application Launcher Script
└── README.md                # Platform Documentation
```

---

## 🏃 Local Quick Start Guide

### 1. Set Up Python Virtual Environment

```bash
cd stock_market_analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` by copying `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL database credentials:

```ini
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/quantnova_db
```

### 3. Run Database Migrations & Seed Sample Equities

```bash
# Apply Alembic database migrations
cd backend
alembic upgrade head

# Seed initial 5 Indian stocks (RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK)
python3 seed.py
cd ..
```

### 4. Launch Application

```bash
chmod +x start_app.sh
./start_app.sh
```

---

## ☁️ Deployment Guide

### Database & Backend on Render

1. **Create PostgreSQL Database on Render**:
   - Go to Render Dashboard → **New +** → **PostgreSQL**.
   - Set Name: `quantnova-db`, Region: `Oregon` (or closest region).
   - Once provisioned, copy the **Internal Database URL** (for services running on Render) or **External Database URL** (for remote access).
   
2. **Deploy Backend Web Service on Render**:
   - Go to Render Dashboard → **New +** → **Web Service**.
   - Connect your GitHub repository.
   - Set Root Directory: `stock_market_analysis`.
   - Runtime: `Python 3`; `.python-version` selects Python 3.11 to match CI.
   - Build Command:
     ```bash
     pip install -r requirements.txt
     ```
   - Start Command: `./start_render.sh` (the script binds Uvicorn to Render's `$PORT`).
   - Set `APP_ENV=production`, `DEBUG=false`, and `CORS_ORIGINS=https://quant-nova-ai-rprt.vercel.app` in the Render service environment. Add the Render PostgreSQL `DATABASE_URL` when a database is provisioned. The API can run without a database, but database-backed caching and persistence will be unavailable.

### Frontend on Vercel

1. In Vercel, import your GitHub repository.
2. Set Root Directory to `stock_market_analysis/frontend`.
3. Set Framework Preset to `Vite`.
4. Optionally set the Production environment variable:
   - `VITE_API_BASE_URL=https://quantnova-ai.onrender.com` (do not append `/api`). Production code uses this verified origin when the variable is missing, blank, or invalid; a valid HTTPS origin can override it.
   - Optionally set `VITE_API_TIMEOUT_MS=180000`.
5. Redeploy after changing either Vite variable because Vite embeds them in the build. The production build checks that the Render origin is present and localhost is absent.

---

## 🌐 REST API Endpoints

- 📊 **Health Check**: `GET /api/health`
- 🏢 **Stocks Catalog**: `GET /api/stocks`
- 🔍 **Symbol Search**: `GET /api/search?q=RELIANCE`
- 📈 **Quantitative Analysis**: `GET /api/analyze?symbol=RELIANCE.NS&period=1y`
- 🎯 **Latest Signals Screener**: `GET /api/signals/latest?limit=20&type=BUY`
- 💬 **AI Research Chatbot**: `GET /api/chat?prompt=growth+outlook&symbol=TCS.NS`
- 📜 **Research History**: `GET /api/research/history`
- 📄 **Export PDF Report**: `GET /api/export/pdf?symbol=RELIANCE.NS`
- 📊 **Export Excel Model**: `GET /api/export/excel?symbol=RELIANCE.NS`
- 📝 **Interactive Swagger Docs**: `http://localhost:8000/docs`
