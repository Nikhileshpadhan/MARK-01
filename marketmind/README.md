# MarketMind API 📈

A production-ready **FastAPI** backend for real-time stock intelligence.

| Layer | What it does | Source |
|---|---|---|
| **Price** | Current price, change %, volume, P/E, market cap | yfinance → Alpha Vantage (fallback) |
| **Sentiment** | News sentiment scoring (Bullish / Neutral / Bearish) | Finnhub company-news |
| **Social** | Reddit + StockTwits mentions, trending score | Finnhub social-sentiment |
| **Technical** | RSI, MACD, Bollinger Bands, SMA/EMA, ATR + signal | yfinance history + `ta` library |
| **Prediction** | 1d / 7d / 30d price forecast + confidence | Ridge regression (15 features) |
| **AI Suggest** | BUY / SELL / HOLD with structured reasoning | Groq llama3-70b (rule-based fallback) |

---

## Quick Start

### 1. Clone & install

```bash
git clone <your-repo>
cd marketmind
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your keys:
```

| Key | Where to get it | Required? |
|---|---|---|
| `FINNHUB_API_KEY` | https://finnhub.io (free tier) | For news & social |
| `ALPHA_VANTAGE_API_KEY` | https://www.alphavantage.co/support/#api-key | Price fallback |
| `GROQ_API_KEY` | https://console.groq.com | AI suggestions |

> **Without any keys** — yfinance still works for price, technicals, and ML prediction.
> Rule-based suggestions are used as a fallback when `GROQ_API_KEY` is absent.

### 3. Run

```bash
uvicorn main:app --reload
```

→ API docs: **http://localhost:8000/docs**
→ Health check: **http://localhost:8000/health**

### 4. Smoke test

```bash
python test_smoke.py
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/stocks`.

```
GET /api/v1/stocks/{symbol}/price       → Real-time price
GET /api/v1/stocks/{symbol}/sentiment   → News sentiment
GET /api/v1/stocks/{symbol}/social      → Reddit + StockTwits
GET /api/v1/stocks/{symbol}/technical   → RSI, MACD, BB, SMA…
GET /api/v1/stocks/{symbol}/prediction  → ML price forecast
GET /api/v1/stocks/{symbol}/suggest     → AI BUY/SELL/HOLD
GET /api/v1/stocks/{symbol}/report      → Everything in one call ✨
GET /api/v1/stocks/compare/prices?symbols=AAPL,MSFT,TSLA
```

### Example — Full report

```bash
curl http://localhost:8000/api/v1/stocks/AAPL/report
```

```jsonc
{
  "price": {
    "symbol": "AAPL",
    "current_price": 189.30,
    "change_pct": 1.24,
    ...
  },
  "sentiment": {
    "overall_label": "Bullish",
    "overall_score": 0.32,
    "bullish_count": 8,
    ...
  },
  "technical": {
    "rsi_14": 58.4,
    "macd": 1.23,
    "signal": "BUY",
    ...
  },
  "prediction": {
    "predicted_price_1d": 191.50,
    "direction": "UP",
    "confidence": 0.72,
    ...
  },
  "ai_suggestion": {
    "action": "BUY",
    "confidence": "High",
    "summary": "AAPL shows strong bullish signals...",
    "reasons_for": [...],
    "reasons_against": [...],
    ...
  }
}
```

---

## Project Structure

```
marketmind/
├── main.py                    # FastAPI app & CORS
├── requirements.txt
├── .env.example
├── test_smoke.py              # Smoke tests (no keys needed)
│
├── models/
│   └── schemas.py             # All Pydantic response models
│
├── routers/
│   └── stocks.py              # Route definitions
│
├── services/
│   ├── price_service.py       # yfinance + Alpha Vantage
│   ├── sentiment_service.py   # Finnhub news + lexicon scoring
│   ├── social_service.py      # Finnhub social sentiment
│   ├── technical_service.py   # ta-lib indicators
│   ├── prediction_service.py  # Ridge regression ML model
│   └── ai_service.py          # Groq LLM suggestions
│
└── utils/
    ├── config.py              # Pydantic settings loader
    └── cache.py               # In-memory TTL cache
```

---

## Caching

All services use an in-memory TTL cache:

| Data | TTL |
|---|---|
| Live prices | 60 seconds |
| Sentiment & social | 10 minutes |
| Technical indicators | 5 minutes |
| ML predictions | 60 minutes |
| AI suggestions | 15 minutes |

For production, swap `utils/cache.py` with a Redis-backed implementation.

---

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t marketmind .
docker run -p 8000:8000 --env-file .env marketmind
```

### Environment variables in production

Never commit `.env`. Use your platform's secrets manager:
- **Railway / Render** → Environment Variables UI
- **AWS** → Parameter Store / Secrets Manager
- **Docker Swarm / K8s** → Secrets

---

## Extending MarketMind

| Feature | How |
|---|---|
| More social data | Add Twitter/X API in `social_service.py` |
| Better ML | Replace Ridge with LSTM in `prediction_service.py` |
| WebSockets | Add `fastapi.WebSocket` route for live price streaming |
| Auth | Add `fastapi.security.APIKeyHeader` middleware |
| Database | Store history in PostgreSQL via `SQLAlchemy` async |
| Rate limiting | Add `slowapi` middleware to `main.py` |

---

> ⚠️ **Disclaimer**: MarketMind is for informational purposes only and does not constitute financial advice.
