from fastapi import APIRouter, HTTPException, Query
import asyncio

from models.schemas import (
    PriceData, SentimentSummary, SocialEngagement,
    TechnicalIndicators, PricePrediction, AISuggestion, StockReport,
)
from services.price_service      import get_price_data
from services.sentiment_service  import get_sentiment
from services.social_service     import get_social_engagement
from services.technical_service  import get_technical_indicators
from services.prediction_service import get_prediction
from services.ai_service         import get_ai_suggestion

router = APIRouter(prefix="/api/v1/stocks", tags=["Stocks"])


def _symbol(s: str) -> str:
    return s.strip().upper()


# ── Price ──────────────────────────────────────────────────────────────────────

@router.get("/{symbol}/price", response_model=PriceData, summary="Current price data")
async def price(symbol: str):
    """Fetch real-time price, change %, volume and key fundamentals."""
    try:
        return await get_price_data(_symbol(symbol))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {e}")


# ── Sentiment ─────────────────────────────────────────────────────────────────

@router.get("/{symbol}/sentiment", response_model=SentimentSummary, summary="News sentiment")
async def sentiment(symbol: str):
    """Aggregate news sentiment from Finnhub. Scores: +1 bullish, -1 bearish."""
    try:
        return await get_sentiment(_symbol(symbol))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment fetch failed: {e}")


# ── Social ────────────────────────────────────────────────────────────────────

@router.get("/{symbol}/social", response_model=SocialEngagement, summary="Social media engagement")
async def social(symbol: str):
    """Reddit + StockTwits engagement metrics and trending score."""
    try:
        return await get_social_engagement(_symbol(symbol))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Social fetch failed: {e}")


# ── Technical ─────────────────────────────────────────────────────────────────

@router.get("/{symbol}/technical", response_model=TechnicalIndicators,
            summary="Technical indicators")
async def technical(symbol: str):
    """RSI, MACD, Bollinger Bands, SMA/EMA and a composite BUY/SELL/HOLD signal."""
    try:
        return await get_technical_indicators(_symbol(symbol))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Technical analysis failed: {e}")


# ── Prediction ────────────────────────────────────────────────────────────────

@router.get("/{symbol}/prediction", response_model=PricePrediction,
            summary="ML price prediction")
async def prediction(symbol: str):
    """Ridge regression price forecast for 1d / 7d / 30d with confidence score."""
    try:
        price_data = await get_price_data(_symbol(symbol))
        return await get_prediction(_symbol(symbol), price_data.current_price)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


# ── AI Suggestion ─────────────────────────────────────────────────────────────

@router.get("/{symbol}/suggest", response_model=AISuggestion,
            summary="AI buy/sell/hold recommendation")
async def suggest(symbol: str):
    """
    Full AI recommendation powered by Groq (llama3-70b).
    Falls back to rule-based analysis when GROQ_API_KEY is not set.
    """
    try:
        sym = _symbol(symbol)
        price_data = await get_price_data(sym)

        # Fetch all supporting data in parallel
        sentiment_data, social_data, technical_data = await asyncio.gather(
            get_sentiment(sym),
            get_social_engagement(sym),
            get_technical_indicators(sym),
        )
        prediction_data = await get_prediction(sym, price_data.current_price)

        return await get_ai_suggestion(
            sym, price_data, sentiment_data, social_data, technical_data, prediction_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {e}")


# ── Full Report ───────────────────────────────────────────────────────────────

@router.get("/{symbol}/report", response_model=StockReport,
            summary="Full MarketMind report")
async def full_report(symbol: str):
    """
    Single endpoint that returns **everything** in parallel:
    price + sentiment + social + technical + ML prediction + AI suggestion.
    """
    try:
        sym = _symbol(symbol)
        price_data = await get_price_data(sym)

        sentiment_data, social_data, technical_data = await asyncio.gather(
            get_sentiment(sym),
            get_social_engagement(sym),
            get_technical_indicators(sym),
        )
        prediction_data = await get_prediction(sym, price_data.current_price)
        ai_data = await get_ai_suggestion(
            sym, price_data, sentiment_data, social_data, technical_data, prediction_data
        )

        return StockReport(
            price=price_data,
            sentiment=sentiment_data,
            social=social_data,
            technical=technical_data,
            prediction=prediction_data,
            ai_suggestion=ai_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full report failed: {e}")


# ── Multi-stock compare ───────────────────────────────────────────────────────

@router.get("/compare/prices", summary="Compare prices for multiple symbols")
async def compare_prices(
    symbols: str = Query(..., description="Comma-separated symbols, e.g. AAPL,MSFT,TSLA")
):
    """Fetch current prices for up to 10 symbols simultaneously."""
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()][:10]
    if not syms:
        raise HTTPException(status_code=400, detail="Provide at least one symbol")

    results = await asyncio.gather(*[get_price_data(s) for s in syms], return_exceptions=True)
    return {
        sym: (r.model_dump() if isinstance(r, PriceData) else {"error": str(r)})
        for sym, r in zip(syms, results)
    }
