"""
MarketMind FastAPI Backend
Run: uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.frontend_compat import router as frontend_compat_router
from routers.stocks import router as stocks_router
from utils.config import get_settings

settings = get_settings()
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app = FastAPI(
    title="MarketMind API",
    description=(
        "Real-time stock intelligence: price data, news sentiment, "
        "social engagement, technical indicators, ML predictions, "
        "and AI-powered buy/sell/hold recommendations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(stocks_router)
app.include_router(frontend_compat_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "services": {
            "finnhub":       bool(settings.finnhub_api_key),
            "alpha_vantage": bool(settings.alpha_vantage_api_key),
            "groq":          bool(settings.groq_api_key),
        },
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": "MarketMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "price":      "/api/v1/stocks/{symbol}/price",
            "sentiment":  "/api/v1/stocks/{symbol}/sentiment",
            "social":     "/api/v1/stocks/{symbol}/social",
            "technical":  "/api/v1/stocks/{symbol}/technical",
            "prediction": "/api/v1/stocks/{symbol}/prediction",
            "suggest":    "/api/v1/stocks/{symbol}/suggest",
            "report":     "/api/v1/stocks/{symbol}/report",
            "compare":    "/api/v1/stocks/compare/prices?symbols=AAPL,MSFT",
        },
    }
