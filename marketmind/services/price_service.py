"""
Stock price fetching service.
Primary source  : yfinance  (free, no key needed)
Fallback source : Alpha Vantage (requires ALPHA_VANTAGE_API_KEY)
"""

import httpx
import yfinance as yf
from datetime import datetime
from models.schemas import PriceData
from utils.config import get_settings
from utils.cache import cache


settings = get_settings()


async def get_price_data(symbol: str) -> PriceData:
    """Fetch current stock price. Tries yfinance first, then Alpha Vantage."""
    cache_key = cache.make_key("price", symbol.upper())
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = await _fetch_yfinance(symbol)
    if data is None and settings.alpha_vantage_api_key:
        data = await _fetch_alpha_vantage(symbol)

    if data is None:
        raise ValueError(f"Could not fetch price data for symbol: {symbol}")

    cache.set(cache_key, data, ttl=60)   # 1 min for live prices
    return data


import requests

async def _fetch_yfinance(symbol: str) -> PriceData | None:
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        ticker = yf.Ticker(symbol, session=session)
        info = ticker.info

        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("ask")
        )
        if not current_price:
            return None

        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or current_price
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        return PriceData(
            symbol=symbol.upper(),
            name=info.get("longName") or info.get("shortName") or symbol.upper(),
            current_price=round(current_price, 4),
            previous_close=round(prev_close, 4),
            open=round(info.get("open") or info.get("regularMarketOpen") or current_price, 4),
            day_high=round(info.get("dayHigh") or info.get("regularMarketDayHigh") or current_price, 4),
            day_low=round(info.get("dayLow") or info.get("regularMarketDayLow") or current_price, 4),
            volume=info.get("volume") or info.get("regularMarketVolume") or 0,
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            change=round(change, 4),
            change_pct=round(change_pct, 2),
            currency=info.get("currency", "USD"),
            timestamp=datetime.utcnow(),
        )
    except Exception:
        return None


async def _fetch_alpha_vantage(symbol: str) -> PriceData | None:
    """Alpha Vantage GLOBAL_QUOTE endpoint as fallback."""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": settings.alpha_vantage_api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            quote = resp.json().get("Global Quote", {})

        if not quote or not quote.get("05. price"):
            return None

        current_price = float(quote["05. price"])
        prev_close = float(quote["08. previous close"])
        change = float(quote["09. change"])
        change_pct = float(quote["10. change percent"].replace("%", ""))

        return PriceData(
            symbol=symbol.upper(),
            name=symbol.upper(),
            current_price=round(current_price, 4),
            previous_close=round(prev_close, 4),
            open=round(float(quote["02. open"]), 4),
            day_high=round(float(quote["03. high"]), 4),
            day_low=round(float(quote["04. low"]), 4),
            volume=int(quote["06. volume"]),
            change=round(change, 4),
            change_pct=round(change_pct, 2),
            timestamp=datetime.utcnow(),
        )
    except Exception:
        return None
