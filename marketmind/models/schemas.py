from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Stock Price ───────────────────────────────────────────────────────────────

class PriceData(BaseModel):
    symbol: str
    name: str
    current_price: float
    previous_close: float
    open: float
    day_high: float
    day_low: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    change: float                  # absolute change
    change_pct: float              # % change
    currency: str = "USD"
    timestamp: datetime


# ─── Sentiment ────────────────────────────────────────────────────────────────

class NewsSentiment(BaseModel):
    headline: str
    source: str
    url: str
    published_at: str
    sentiment_score: float         # -1.0 (bearish) to +1.0 (bullish)
    sentiment_label: str           # "Bullish" | "Neutral" | "Bearish"


class SentimentSummary(BaseModel):
    symbol: str
    overall_score: float           # aggregate -1 to +1
    overall_label: str
    bullish_count: int
    neutral_count: int
    bearish_count: int
    news_items: list[NewsSentiment]
    buzz_score: float              # 0–100 social buzz proxy
    timestamp: datetime


# ─── Social / Engagement ──────────────────────────────────────────────────────

class SocialEngagement(BaseModel):
    symbol: str
    reddit_mentions: int
    reddit_sentiment: float
    stocktwits_watchlists: Optional[int] = None
    trending_score: float          # composite 0–100
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    top_posts: list[dict]
    timestamp: datetime


# ─── Technical Indicators ─────────────────────────────────────────────────────

class TechnicalIndicators(BaseModel):
    symbol: str
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_mid: Optional[float] = None
    atr: Optional[float] = None
    signal: str                    # "BUY" | "SELL" | "HOLD"


# ─── Price Prediction ─────────────────────────────────────────────────────────

class PricePrediction(BaseModel):
    model_config = {"protected_namespaces": ()}
    symbol: str
    current_price: float
    predicted_price_1d: float
    predicted_price_7d: float
    predicted_price_30d: float
    confidence: float              # 0–1
    model_used: str
    direction: str                 # "UP" | "DOWN" | "SIDEWAYS"
    support_level: float
    resistance_level: float
    timestamp: datetime


# ─── AI Suggestion ────────────────────────────────────────────────────────────

class AISuggestion(BaseModel):
    symbol: str
    action: str                    # "BUY" | "SELL" | "HOLD"
    confidence: str                # "High" | "Medium" | "Low"
    summary: str
    reasons_for: list[str]
    reasons_against: list[str]
    risk_level: str                # "Low" | "Medium" | "High"
    time_horizon: str              # "Short-term" | "Mid-term" | "Long-term"
    disclaimer: str
    timestamp: datetime


# ─── Full Stock Report ────────────────────────────────────────────────────────

class StockReport(BaseModel):
    price: PriceData
    sentiment: SentimentSummary
    social: SocialEngagement
    technical: TechnicalIndicators
    prediction: PricePrediction
    ai_suggestion: AISuggestion


# ─── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code: str
