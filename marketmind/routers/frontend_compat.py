from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from models.schemas import PriceData, PricePrediction, TechnicalIndicators
from services.ai_service import get_ai_suggestion
from services.ai_service import resolve_company_ticker
from services.sentiment_service import get_sentiment
from services.social_service import get_social_engagement
from utils.cache import cache
from utils.config import get_settings


router = APIRouter(tags=["Frontend Compatibility"])
settings = get_settings()


TRACKED_COMPANIES = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Communication Services"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Communication Services"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "INTC", "name": "Intel Corp.", "sector": "Technology"},
    {"symbol": "ORCL", "name": "Oracle Corp.", "sector": "Technology"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
    {"symbol": "IBM", "name": "International Business Machines", "sector": "Technology"},
    {"symbol": "QCOM", "name": "Qualcomm Inc.", "sector": "Technology"},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology"},
    {"symbol": "TXN", "name": "Texas Instruments", "sector": "Technology"},
    {"symbol": "MU", "name": "Micron Technology", "sector": "Technology"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financials"},
    {"symbol": "WFC", "name": "Wells Fargo & Co.", "sector": "Financials"},
    {"symbol": "C", "name": "Citigroup Inc.", "sector": "Financials"},
    {"symbol": "GS", "name": "Goldman Sachs Group", "sector": "Financials"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "Financials"},
    {"symbol": "BLK", "name": "BlackRock Inc.", "sector": "Financials"},
    {"symbol": "SCHW", "name": "Charles Schwab Corp.", "sector": "Financials"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financials"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Financials"},
    {"symbol": "AXP", "name": "American Express", "sector": "Financials"},
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy"},
    {"symbol": "CVX", "name": "Chevron Corp.", "sector": "Energy"},
    {"symbol": "COP", "name": "ConocoPhillips", "sector": "Energy"},
    {"symbol": "SLB", "name": "Schlumberger Ltd.", "sector": "Energy"},
    {"symbol": "EOG", "name": "EOG Resources", "sector": "Energy"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "MRK", "name": "Merck & Co.", "sector": "Healthcare"},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare"},
    {"symbol": "LLY", "name": "Eli Lilly and Co.", "sector": "Healthcare"},
    {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "MCD", "name": "McDonald's Corp.", "sector": "Consumer Discretionary"},
    {"symbol": "SBUX", "name": "Starbucks Corp.", "sector": "Consumer Discretionary"},
    {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Communication Services"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples"},
    {"symbol": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer Staples"},
    {"symbol": "KO", "name": "Coca-Cola Co.", "sector": "Consumer Staples"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Staples"},
    {"symbol": "PG", "name": "Procter & Gamble", "sector": "Consumer Staples"},
]


_ranking_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=120))
_refresh_lock = asyncio.Lock()
_skip_live_until: datetime | None = None


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _company_info(symbol: str) -> dict:
    symbol = symbol.upper()
    for company in TRACKED_COMPANIES:
        if company["symbol"] == symbol:
            return company
    return {"symbol": symbol, "name": symbol, "sector": "Unknown"}


def _register_company(symbol: str, name: str | None = None, sector: str | None = None) -> dict:
    """Ensure a symbol is tracked so it can appear in ranking/latest."""
    sym = symbol.strip().upper()
    for company in TRACKED_COMPANIES:
        if company["symbol"] == sym:
            if name and (company.get("name") in {None, "", sym}):
                company["name"] = name
            if sector and company.get("sector") in {None, "", "Unknown"}:
                company["sector"] = sector
            return company

    company = {
        "symbol": sym,
        "name": (name or sym).strip(),
        "sector": (sector or "External").strip() or "External",
    }
    TRACKED_COMPANIES.append(company)
    cache.invalidate(cache.make_key("frontend", "ranking", "latest"))
    return company


def _build_history_point(snapshot: dict) -> dict:
    return {
        "symbol": snapshot["symbol"],
        "rank": snapshot["rank"],
        "price_score": snapshot["price_score"],
        "engagement_score": snapshot["engagement_score"],
        "final_score": snapshot["final_score"],
        "timestamp": snapshot["timestamp"],
    }


def _synthetic_stock_snapshot(symbol: str) -> dict:
    info = _company_info(symbol)
    now = datetime.utcnow()
    seed = sum(ord(ch) for ch in symbol.upper())
    base_price = 80 + (seed % 420)
    minute_wave = ((now.minute + (seed % 11)) % 12) - 6
    change_percent = round(minute_wave * 0.22, 2)
    price = round(base_price * (1 + (change_percent / 100.0)), 4)
    volume = int(500_000 + (seed % 900_000) * 3)
    return {
        "symbol": symbol.upper(),
        "name": info["name"],
        "sector": info["sector"],
        "price": price,
        "change_percent": change_percent,
        "volume": volume,
        "timestamp": now,
        "is_fallback": True,
    }


async def _get_stock_snapshot(symbol: str) -> dict:
    """Fast, deterministic snapshot for frontend compatibility."""
    cache_key = cache.make_key("frontend", "stock", symbol.upper())
    cached = cache.get(cache_key)
    if cached:
        return cached

    snapshot = _synthetic_stock_snapshot(symbol)
    cache.set(cache_key, snapshot, ttl=45)
    return snapshot


async def _build_snapshot(company: dict) -> dict | None:
    symbol = company["symbol"]
    try:
        stock, social = await asyncio.gather(
            _get_stock_snapshot(symbol),
            get_social_engagement(symbol),
        )

        mention_count = int((social.reddit_mentions or 0) + (social.stocktwits_watchlists or 0))
        price_score = round(_clamp(50 + (stock["change_percent"] * 5)), 2)
        engagement_score = round(_clamp(social.trending_score), 2)
        final_score = round((price_score * 0.6) + (engagement_score * 0.4), 2)

        return {
            "symbol": symbol,
            "name": company["name"] or stock["name"],
            "sector": company["sector"],
            "price": stock["price"],
            "change_percent": stock["change_percent"],
            "mention_count": mention_count,
            "price_score": price_score,
            "engagement_score": engagement_score,
            "final_score": final_score,
            "timestamp": stock["timestamp"],
        }
    except Exception:
        return None


async def _get_ranking_latest() -> list[dict]:
    cache_key = cache.make_key("frontend", "ranking", "latest")
    cached = cache.get(cache_key)
    if cached:
        return cached

    snapshots = await asyncio.gather(*[_build_snapshot(company) for company in TRACKED_COMPANIES])
    ranked = [item for item in snapshots if item is not None]

    ranked.sort(key=lambda item: item["final_score"], reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
        _ranking_history[item["symbol"]].appendleft(_build_history_point(item))

    cache.set(cache_key, ranked, ttl=60)
    return ranked


def _synthetic_market_history(symbol: str, days: int) -> list[dict]:
    now = datetime.utcnow()
    snapshot = _synthetic_stock_snapshot(symbol)
    base_price = float(snapshot["price"])
    base_volume = int(snapshot["volume"])
    seed = sum(ord(ch) for ch in symbol.upper())

    rows = []
    for i in range(days):
        day_index = days - i
        curve = ((seed + day_index * 7) % 11) - 5
        drift = (curve * 0.0025)
        day_price = round(base_price * (1 - drift), 4)
        day_volume = max(1, int(base_volume * (1 + (curve * 0.03))))
        rows.append(
            {
                "timestamp": now - timedelta(days=day_index),
                "price": day_price,
                "volume": day_volume,
                "is_stale": False,
            }
        )
    return rows


async def _derived_signal_items(symbol: str, limit: int) -> list[dict]:
    """Build internal signal updates when external news is unavailable."""
    sym = symbol.strip().upper()
    stock, social = await asyncio.gather(
        _get_stock_snapshot(sym),
        get_social_engagement(sym),
    )
    prediction = _build_prediction(sym, stock)

    now = datetime.utcnow()
    direction_text = "upside" if prediction.direction == "UP" else "downside" if prediction.direction == "DOWN" else "sideways"
    expected_move = prediction.predicted_price_1d - prediction.current_price
    expected_move_pct = (expected_move / prediction.current_price * 100) if prediction.current_price else 0.0

    base_items = [
        {
            "title": f"{sym} price momentum signal",
            "summary": (
                f"Current price is {stock['price']:.2f} with intraday change {stock['change_percent']:+.2f}%. "
                f"Price score is computed from the same ranking formula: 50 + change_pct x 5."
            ),
            "source": "MarketMind Signal",
            "url": "",
            "published_at": now.isoformat(),
        },
        {
            "title": f"{sym} engagement participation signal",
            "summary": (
                f"Engagement uses social metrics: trending score {social.trending_score:.1f}, "
                f"mentions {int((social.reddit_mentions or 0) + (social.stocktwits_watchlists or 0))}, "
                f"sentiment mix {social.positive_pct:.1f}% positive / {social.negative_pct:.1f}% negative."
            ),
            "source": "MarketMind Signal",
            "url": "",
            "published_at": (now - timedelta(minutes=20)).isoformat(),
        },
        {
            "title": f"{sym} one-day model outlook",
            "summary": (
                f"Model direction is {direction_text}; expected 1-day move {expected_move:+.2f} "
                f"({expected_move_pct:+.2f}%), confidence {prediction.confidence:.2f}."
            ),
            "source": "MarketMind Model",
            "url": "",
            "published_at": (now - timedelta(minutes=40)).isoformat(),
        },
    ]
    return base_items[: max(1, min(limit, len(base_items)))]


async def _ensure_symbol_ranking_history(symbol: str, points: int = 30) -> None:
    sym = symbol.strip().upper()
    if _ranking_history[sym]:
        return

    if any(company["symbol"] == sym for company in TRACKED_COMPANIES):
        await _get_ranking_latest()
        if _ranking_history[sym]:
            return

    stock, social = await asyncio.gather(
        _get_stock_snapshot(sym),
        get_social_engagement(sym),
    )

    # Generate history from the same market-history path used by charts.
    history_rows = _synthetic_market_history(sym, points)
    social_mentions = max(1.0, float((social.reddit_mentions or 0) + (social.stocktwits_watchlists or 0)))
    base_engagement = _clamp(to_float(getattr(social, "trending_score", 0)))
    prev_price = None
    computed_points = []

    for row in history_rows:
        current_price = to_float(row.get("price"))
        current_volume = max(1.0, to_float(row.get("volume")))

        if prev_price and prev_price > 0:
            change_pct = ((current_price - prev_price) / prev_price) * 100.0
        else:
            change_pct = to_float(stock.get("change_percent"))

        price_score = round(_clamp(50 + (change_pct * 5)), 2)
        volume_factor = max(0.8, min(1.2, current_volume / max(1.0, social_mentions * 10.0)))
        engagement_score = round(_clamp(base_engagement * volume_factor), 2)
        final_score = round((price_score * 0.6) + (engagement_score * 0.4), 2)

        computed_points.append(
            {
                "symbol": sym,
                "price_score": price_score,
                "engagement_score": engagement_score,
                "final_score": final_score,
                "timestamp": row["timestamp"],
            }
        )
        prev_price = current_price

    latest_ranked = await _get_ranking_latest()
    latest_score = computed_points[-1]["final_score"] if computed_points else 0.0
    rank = 1 + sum(1 for item in latest_ranked if to_float(item.get("final_score")) > latest_score)

    for point in reversed(computed_points):
        _ranking_history[sym].appendleft(
            {
                **point,
                "rank": rank,
            }
        )


def to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_price_data(stock: dict) -> PriceData:
    current = float(stock["price"])
    change_pct = float(stock["change_percent"])
    previous = current / (1 + (change_pct / 100.0)) if change_pct != -100 else current
    return PriceData(
        symbol=stock["symbol"],
        name=stock["name"],
        current_price=round(current, 4),
        previous_close=round(previous, 4),
        open=round(previous, 4),
        day_high=round(max(current, previous) * 1.01, 4),
        day_low=round(min(current, previous) * 0.99, 4),
        volume=int(stock["volume"]),
        market_cap=None,
        pe_ratio=None,
        change=round(current - previous, 4),
        change_pct=round(change_pct, 2),
        currency="USD",
        timestamp=stock["timestamp"],
    )


def _build_prediction(symbol: str, stock: dict) -> PricePrediction:
    current = float(stock["price"])
    drift_pct = round(float(stock["change_percent"]) * 0.6, 2)
    pred_1d = round(current * (1 + (drift_pct / 100.0)), 4)
    pred_7d = round(current * (1 + (drift_pct / 100.0)) ** 7, 4)
    pred_30d = round(current * (1 + (drift_pct / 100.0)) ** 30, 4)
    return PricePrediction(
        symbol=symbol,
        current_price=round(current, 4),
        predicted_price_1d=pred_1d,
        predicted_price_7d=pred_7d,
        predicted_price_30d=pred_30d,
        confidence=0.25,
        model_used="Compatibility synthetic predictor",
        direction="UP" if drift_pct > 0 else "DOWN" if drift_pct < 0 else "SIDEWAYS",
        support_level=round(current * 0.96, 4),
        resistance_level=round(current * 1.04, 4),
        timestamp=datetime.utcnow(),
    )


def _build_technical(symbol: str, stock: dict) -> TechnicalIndicators:
    change_pct = float(stock["change_percent"])
    signal = "BUY" if change_pct > 0.4 else "SELL" if change_pct < -0.4 else "HOLD"
    rsi = 50 + min(20, max(-20, change_pct * 4))
    return TechnicalIndicators(
        symbol=symbol,
        rsi_14=round(rsi, 2),
        signal=signal,
    )


def _require_key(key_value: str, key_name: str) -> None:
    if not key_value:
        raise HTTPException(status_code=503, detail=f"{key_name} is required and fallback is disabled")


@router.get("/ranking/latest")
async def ranking_latest():
    return await _get_ranking_latest()


@router.get("/ranking/history/{symbol}")
async def ranking_history(symbol: str):
    sym = symbol.strip().upper()
    if not _ranking_history[sym]:
        await _ensure_symbol_ranking_history(sym)
    return list(_ranking_history[sym])


@router.get("/stock/{symbol}/latest")
async def stock_latest(symbol: str):
    sym = symbol.strip().upper()
    try:
        return await _get_stock_snapshot(sym)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock snapshot: {exc}")


@router.get("/stock/{symbol}/market-history")
async def stock_market_history(symbol: str, days: int = Query(30, ge=1, le=180)):
    sym = symbol.strip().upper()
    return _synthetic_market_history(sym, days)


@router.get("/stock/{symbol}/history")
async def stock_history_legacy(symbol: str, limit: int = Query(30, ge=1, le=180)):
    return await stock_market_history(symbol, days=limit)


@router.get("/engagement/{symbol}/latest")
async def engagement_latest(symbol: str):
    sym = symbol.strip().upper()
    social, sentiment = await asyncio.gather(
        get_social_engagement(sym),
        get_sentiment(sym),
    )
    mention_count = int((social.reddit_mentions or 0) + (social.stocktwits_watchlists or 0))
    raw_sentiment = to_float(sentiment.overall_score)
    if sentiment.bullish_count == 0 and sentiment.bearish_count == 0 and sentiment.neutral_count == 0:
        # No live news available; use social sentiment proxy to avoid flat zero output.
        raw_sentiment = to_float(social.reddit_sentiment)
    normalized_sentiment = round((raw_sentiment + 1.0) / 2.0, 3)
    return {
        "symbol": sym,
        "mention_count": mention_count,
        "sentiment_score": normalized_sentiment,
        "timestamp": sentiment.timestamp,
    }


@router.get("/engagement/{symbol}/history")
async def engagement_history(symbol: str, limit: int = Query(30, ge=1, le=120)):
    sym = symbol.strip().upper()
    if not _ranking_history[sym]:
        await _ensure_symbol_ranking_history(sym)

    latest = await engagement_latest(sym)
    history_rows = list(_ranking_history[sym])[:limit]
    if not history_rows:
        return [{"id": f"{sym}-0", **latest}]

    result = []
    for idx, row in enumerate(history_rows):
        scaled_mentions = int(max(0, round(row["engagement_score"] * 15)))
        result.append(
            {
                "id": f"{sym}-{idx}",
                "symbol": sym,
                "mention_count": scaled_mentions,
                "sentiment_score": latest["sentiment_score"],
                "timestamp": row["timestamp"],
            }
        )
    return result


@router.get("/prediction/{symbol}/live")
async def prediction_live(symbol: str):
    sym = symbol.strip().upper()
    stock = await _get_stock_snapshot(sym)
    drift_pct = round(stock["change_percent"] * 0.6, 2)
    predicted_price = round(stock["price"] * (1 + (drift_pct / 100.0)), 4)
    return {
        "symbol": sym,
        "predicted_price": predicted_price,
        "predicted_change_percent": drift_pct,
        "confidence": 0.25,
        "direction": "UP" if drift_pct > 0 else "DOWN" if drift_pct < 0 else "SIDEWAYS",
        "timestamp": datetime.utcnow(),
    }


@router.get("/news/{symbol}")
async def company_news(symbol: str, limit: int = Query(8, ge=1, le=20)):
    sym = symbol.strip().upper()
    sentiment = await get_sentiment(sym)
    items = [
        {
            "title": news.headline,
            "summary": "",
            "source": news.source,
            "url": news.url,
            "published_at": news.published_at,
        }
        for news in sentiment.news_items[:limit]
    ]
    if not items:
        items = await _derived_signal_items(sym, limit)
    return {"symbol": sym, "items": items}


@router.get("/recommendation/{symbol}/live")
async def recommendation_live(symbol: str):
    _require_key(settings.groq_api_key, "GROQ_API_KEY")
    _require_key(settings.finnhub_api_key, "FINNHUB_API_KEY")
    sym = symbol.strip().upper()
    stock = await _get_stock_snapshot(sym)
    price_data = _build_price_data(stock)
    prediction = _build_prediction(sym, stock)
    technical = _build_technical(sym, stock)
    sentiment, social = await asyncio.gather(
        get_sentiment(sym),
        get_social_engagement(sym),
    )

    suggestion = await get_ai_suggestion(
        sym,
        price_data,
        sentiment,
        social,
        technical,
        prediction,
    )
    return {
        "symbol": suggestion.symbol,
        "action": suggestion.action,
        "confidence": suggestion.confidence,
        "summary": suggestion.summary,
        "risk_level": suggestion.risk_level,
        "time_horizon": suggestion.time_horizon,
        "reasons_for": suggestion.reasons_for,
        "reasons_against": suggestion.reasons_against,
        "timestamp": suggestion.timestamp,
    }


@router.post("/refresh")
async def refresh_data():
    async with _refresh_lock:
        cache.clear()
        latest = await _get_ranking_latest()
        return {
            "ok": True,
            "updated": len(latest),
            "timestamp": datetime.utcnow(),
        }


@router.get("/companies/search")
async def companies_search(q: str = Query(..., min_length=1)):
    needle = q.strip().lower()
    if not needle:
        return []

    candidates = []
    for company in TRACKED_COMPANIES:
        if needle in company["symbol"].lower() or needle in company["name"].lower():
            candidates.append(company)

    # Keep symbol prefix matches first for type-ahead behavior.
    candidates.sort(key=lambda item: (not item["symbol"].lower().startswith(needle), item["symbol"]))
    if candidates:
        return candidates[:12]

    # Fallback: resolve non-tracked company names into a likely ticker via LLM.
    resolved = await resolve_company_ticker(q, TRACKED_COMPANIES)
    if not resolved:
        return []

    symbol = resolved.get("symbol", "").upper()
    for company in TRACKED_COMPANIES:
        if company["symbol"].upper() == symbol:
            return [company]

    company = _register_company(
        symbol=symbol,
        name=resolved.get("name") or symbol,
        sector=resolved.get("sector", "External"),
    )
    await _ensure_symbol_ranking_history(symbol)
    return [company]