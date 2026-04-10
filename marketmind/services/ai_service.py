"""
AI suggestion service powered by Groq (llama-3.3-70b-versatile).
Constructs a rich prompt from all data layers and returns a structured
BUY / SELL / HOLD recommendation with reasoning.
"""

import json
import re
from datetime import datetime
from groq import AsyncGroq

from models.schemas import (
    AISuggestion, PriceData, SentimentSummary,
    SocialEngagement, TechnicalIndicators, PricePrediction,
)
from utils.config import get_settings
from utils.cache import cache


settings = get_settings()


def _is_valid_symbol(symbol: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z.-]{0,5}", symbol or ""))


async def resolve_company_ticker(query: str, known_companies: list[dict] | None = None) -> dict | None:
    """Resolve a free-text company query to a likely ticker symbol using Groq."""
    cleaned = (query or "").strip()
    if not cleaned:
        return None

    # Fast path: user entered a ticker directly.
    uppercase = cleaned.upper()
    if _is_valid_symbol(uppercase) and len(cleaned.split()) == 1:
        if known_companies:
            for company in known_companies:
                if company.get("symbol", "").upper() == uppercase:
                    return {
                        "symbol": company["symbol"],
                        "name": company.get("name", company["symbol"]),
                        "sector": company.get("sector", "Unknown"),
                        "source": "direct",
                    }
        return {
            "symbol": uppercase,
            "name": uppercase,
            "sector": "Unknown",
            "source": "direct",
        }

    cache_key = cache.make_key("ticker_resolve", cleaned.lower())
    cached = cache.get(cache_key)
    if cached:
        return cached

    if not settings.groq_api_key:
        return None

    shortlist = ""
    if known_companies:
        shortlist = "\n".join(
            f"- {item.get('symbol', '')}: {item.get('name', '')}"
            for item in known_companies[:120]
        )

    prompt = (
        "Map the company query to the most likely publicly traded ticker symbol.\n"
        "Return ONLY strict JSON with keys: symbol, company_name, confidence.\n"
        "confidence must be High, Medium, or Low.\n"
        "If uncertain, still provide best guess with Low confidence.\n\n"
        f"Query: {cleaned}\n\n"
        "Known tracked companies (optional context):\n"
        f"{shortlist if shortlist else '- none provided'}"
    )

    client = AsyncGroq(api_key=settings.groq_api_key)
    chat = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a financial symbol resolver. Output JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=120,
    )

    raw = (chat.choices[0].message.content or "").strip()
    clean = re.sub(r"```(?:json)?", "", raw).strip()

    symbol = ""
    company_name = cleaned
    confidence = "Low"

    try:
        payload = json.loads(clean)
        symbol = str(payload.get("symbol", "")).upper().strip()
        company_name = str(payload.get("company_name", cleaned)).strip() or cleaned
        confidence = str(payload.get("confidence", "Low")).title()
    except json.JSONDecodeError:
        match = re.search(r"\b[A-Z]{1,6}(?:\.[A-Z])?\b", raw.upper())
        symbol = match.group(0) if match else ""

    if not _is_valid_symbol(symbol):
        return None

    result = {
        "symbol": symbol,
        "name": company_name,
        "sector": "External",
        "source": "llm",
        "confidence": confidence if confidence in {"High", "Medium", "Low"} else "Low",
    }
    cache.set(cache_key, result, ttl=1800)
    return result


async def get_ai_suggestion(
    symbol: str,
    price: PriceData,
    sentiment: SentimentSummary,
    social: SocialEngagement,
    technical: TechnicalIndicators,
    prediction: PricePrediction,
) -> AISuggestion:

    cache_key = cache.make_key("ai_suggestion", symbol.upper(),
                               round(price.current_price, 1))
    cached = cache.get(cache_key)
    if cached:
        return cached

    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is required. Rule-based fallback is disabled.")

    result = await _groq_suggestion(symbol, price, sentiment, social, technical, prediction)

    cache.set(cache_key, result, ttl=900)   # 15 min
    return result


# ── Groq path ─────────────────────────────────────────────────────────────────

async def _groq_suggestion(symbol, price, sentiment, social, technical, prediction) -> AISuggestion:
    prompt = _build_prompt(symbol, price, sentiment, social, technical, prediction)

    client = AsyncGroq(api_key=settings.groq_api_key)
    chat = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert financial analyst. Analyse the provided stock data "
                    "and return ONLY a valid JSON object — no markdown, no extra text. "
                    "Schema:\n"
                    "{\n"
                    '  "action": "BUY" | "SELL" | "HOLD",\n'
                    '  "confidence": "High" | "Medium" | "Low",\n'
                    '  "summary": "<2-3 sentence executive summary>",\n'
                    '  "reasons_for": ["<reason 1>", "<reason 2>", "<reason 3>"],\n'
                    '  "reasons_against": ["<risk 1>", "<risk 2>"],\n'
                    '  "risk_level": "Low" | "Medium" | "High",\n'
                    '  "time_horizon": "Short-term" | "Mid-term" | "Long-term"\n'
                    "}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=600,
    )

    raw = chat.choices[0].message.content.strip()
    return _parse_groq_response(symbol, raw)


def _build_prompt(symbol, price, sentiment, social, technical, prediction) -> str:
    return f"""
Analyse {symbol} ({price.name}) and give a trading recommendation.

## Price
- Current: ${price.current_price}  |  Change: {price.change_pct:+.2f}%
- Day range: ${price.day_low} – ${price.day_high}
- P/E: {price.pe_ratio or 'N/A'}  |  Market Cap: {price.market_cap or 'N/A'}

## Sentiment
- Overall: {sentiment.overall_label} (score {sentiment.overall_score:+.2f})
- Articles: {sentiment.bullish_count} bullish / {sentiment.neutral_count} neutral / {sentiment.bearish_count} bearish
- Buzz score: {sentiment.buzz_score}/100

## Social engagement
- Reddit mentions: {social.reddit_mentions}  (sentiment {social.reddit_sentiment:+.2f})
- Trending score: {social.trending_score}/100
- Positive {social.positive_pct}% / Negative {social.negative_pct}%

## Technical indicators
- RSI(14): {technical.rsi_14}  |  Signal: {technical.signal}
- MACD: {technical.macd}  /  Signal line: {technical.macd_signal}
- Price vs SMA50: ${price.current_price} vs ${technical.sma_50}
- Bollinger: [{technical.bb_lower} – {technical.bb_upper}]

## ML Prediction
- 1-day target: ${prediction.predicted_price_1d}  ({prediction.direction})
- 7-day target: ${prediction.predicted_price_7d}
- 30-day target: ${prediction.predicted_price_30d}
- Model confidence: {prediction.confidence:.0%}
- Support: ${prediction.support_level}  |  Resistance: ${prediction.resistance_level}

Provide your structured JSON recommendation now.
""".strip()


def _parse_groq_response(symbol: str, raw: str) -> AISuggestion:
    # Strip any accidental markdown fences
    clean = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Best-effort regex extraction
        action = "HOLD"
        for a in ("BUY", "SELL", "HOLD"):
            if a in raw.upper():
                action = a
                break
        data = {
            "action": action,
            "confidence": "Low",
            "summary": raw[:300],
            "reasons_for": [],
            "reasons_against": [],
            "risk_level": "Medium",
            "time_horizon": "Short-term",
        }

    return AISuggestion(
        symbol=symbol.upper(),
        action=data.get("action", "HOLD"),
        confidence=data.get("confidence", "Low"),
        summary=data.get("summary", ""),
        reasons_for=data.get("reasons_for", []),
        reasons_against=data.get("reasons_against", []),
        risk_level=data.get("risk_level", "Medium"),
        time_horizon=data.get("time_horizon", "Short-term"),
        disclaimer=(
            "This is AI-generated analysis for informational purposes only. "
            "It does not constitute financial advice. Always do your own research."
        ),
        timestamp=datetime.utcnow(),
    )


