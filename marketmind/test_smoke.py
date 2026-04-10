"""
Quick smoke test — runs without any API keys using yfinance only.
Usage:  python test_smoke.py
"""

import asyncio, sys
sys.path.insert(0, ".")

from services.price_service      import get_price_data
from services.sentiment_service  import get_sentiment
from services.technical_service  import get_technical_indicators
from services.prediction_service import get_prediction
from services.social_service     import get_social_engagement
from services.ai_service         import get_ai_suggestion

SYMBOL = "AAPL"

async def main():
    print(f"\n{'='*50}")
    print(f"  MarketMind Smoke Test — {SYMBOL}")
    print(f"{'='*50}")

    # 1. Price
    print("\n[1] Fetching price data…")
    price = await get_price_data(SYMBOL)
    print(f"    ✓  {price.name}: ${price.current_price} ({price.change_pct:+.2f}%)")

    # 2. Sentiment
    print("[2] Fetching sentiment…")
    sentiment = await get_sentiment(SYMBOL)
    print(f"    ✓  {sentiment.overall_label} (score {sentiment.overall_score:+.2f}), "
          f"{len(sentiment.news_items)} articles")

    # 3. Social
    print("[3] Fetching social engagement…")
    social = await get_social_engagement(SYMBOL)
    print(f"    ✓  Reddit mentions: {social.reddit_mentions}, "
          f"trending: {social.trending_score}/100")

    # 4. Technical
    print("[4] Computing technical indicators…")
    tech = await get_technical_indicators(SYMBOL)
    print(f"    ✓  RSI: {tech.rsi_14}, MACD: {tech.macd}, Signal: {tech.signal}")

    # 5. Prediction
    print("[5] Running ML prediction…")
    pred = await get_prediction(SYMBOL, price.current_price)
    print(f"    ✓  1d: ${pred.predicted_price_1d}  7d: ${pred.predicted_price_7d}  "
          f"30d: ${pred.predicted_price_30d}  ({pred.direction}, "
          f"confidence {pred.confidence:.0%})")

    # 6. AI Suggestion
    print("[6] Generating AI suggestion (rule-based, no Groq key needed)…")
    suggestion = await get_ai_suggestion(SYMBOL, price, sentiment, social, tech, pred)
    print(f"    ✓  Action: {suggestion.action} | Confidence: {suggestion.confidence} | "
          f"Risk: {suggestion.risk_level}")
    print(f"    Summary: {suggestion.summary[:120]}…")

    print(f"\n{'='*50}")
    print("  All checks passed ✓")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    asyncio.run(main())
