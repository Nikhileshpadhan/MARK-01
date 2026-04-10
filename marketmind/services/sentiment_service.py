"""
Sentiment service.
News source : Finnhub /company-news  (requires FINNHUB_API_KEY)
Scoring     : keyword-based heuristic (no extra dependency)
"""

import httpx
import re
from datetime import datetime, timedelta
from models.schemas import SentimentSummary, NewsSentiment
from utils.config import get_settings
from utils.cache import cache


settings = get_settings()

# ── Simple lexicon ────────────────────────────────────────────────────────────
_BULLISH = {
    "beat", "surge", "rally", "profit", "growth", "record", "strong", "upgrade",
    "bullish", "buy", "positive", "outperform", "gain", "rise", "high", "above",
    "exceed", "increase", "expand", "soar", "boom", "revenue", "upside",
}
_BEARISH = {
    "miss", "drop", "fall", "loss", "weak", "downgrade", "bearish", "sell",
    "negative", "underperform", "decline", "low", "below", "disappoint",
    "concern", "risk", "lawsuit", "fraud", "crash", "debt", "layoff", "cut",
}


def _score_text(text: str) -> float:
    """Return sentiment score in [-1, +1]."""
    words = set(re.sub(r"[^a-z ]", "", text.lower()).split())
    bull = len(words & _BULLISH)
    bear = len(words & _BEARISH)
    total = bull + bear
    if total == 0:
        return 0.0
    return round((bull - bear) / total, 3)


def _label(score: float) -> str:
    if score > 0.1:
        return "Bullish"
    if score < -0.1:
        return "Bearish"
    return "Neutral"


async def get_sentiment(symbol: str) -> SentimentSummary:
    cache_key = cache.make_key("sentiment", symbol.upper())
    cached = cache.get(cache_key)
    if cached:
        return cached

    news_items = await _fetch_finnhub_news(symbol)
    if not news_items:
        # Return neutral sentiment when no news available
        result = SentimentSummary(
            symbol=symbol.upper(),
            overall_score=0.0,
            overall_label="Neutral",
            bullish_count=0,
            neutral_count=0,
            bearish_count=0,
            news_items=[],
            buzz_score=0.0,
            timestamp=datetime.utcnow(),
        )
        cache.set(cache_key, result)
        return result

    scored = []
    for item in news_items:
        score = _score_text(item["headline"] + " " + item.get("summary", ""))
        scored.append(
            NewsSentiment(
                headline=item["headline"],
                source=item.get("source", ""),
                url=item.get("url", ""),
                published_at=str(item.get("datetime", "")),
                sentiment_score=score,
                sentiment_label=_label(score),
            )
        )

    bull = sum(1 for s in scored if s.sentiment_label == "Bullish")
    bear = sum(1 for s in scored if s.sentiment_label == "Bearish")
    neut = sum(1 for s in scored if s.sentiment_label == "Neutral")
    avg_score = round(sum(s.sentiment_score for s in scored) / len(scored), 3)

    # Buzz score: normalised count of articles in last 24 h (capped at 100)
    buzz = min(len(scored) * 5, 100)

    result = SentimentSummary(
        symbol=symbol.upper(),
        overall_score=avg_score,
        overall_label=_label(avg_score),
        bullish_count=bull,
        neutral_count=neut,
        bearish_count=bear,
        news_items=scored[:10],     # top 10 for response size
        buzz_score=float(buzz),
        timestamp=datetime.utcnow(),
    )
    cache.set(cache_key, result, ttl=600)   # 10 min
    return result


async def _fetch_finnhub_news(symbol: str) -> list[dict]:
    if not settings.finnhub_api_key:
        return []

    end = datetime.utcnow()
    start = end - timedelta(days=3)
    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": symbol.upper(),
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "token": settings.finnhub_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json() or []
    except Exception:
        return []
