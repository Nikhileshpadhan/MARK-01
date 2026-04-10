"""
Frontend-backend contract smoke test.
Run: python test_frontend_contract.py
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from main import app
import routers.frontend_compat as frontend_compat


def _assert_keys(payload: dict, required: set[str], label: str) -> None:
    missing = required.difference(payload.keys())
    assert not missing, f"{label} missing keys: {sorted(missing)}"


def run() -> None:
    # Keep test deterministic and independent from external rate limits.
    frontend_compat._skip_live_until = datetime.now() + timedelta(minutes=30)

    client = TestClient(app)

    r = client.get("/ranking/latest")
    assert r.status_code == 200, f"/ranking/latest failed: {r.status_code}"
    ranking = r.json()
    assert isinstance(ranking, list), "ranking/latest should return a list"
    assert len(ranking) == 50, f"ranking/latest should return 50 rows, got {len(ranking)}"
    _assert_keys(
        ranking[0],
        {"symbol", "name", "sector", "price", "change_percent", "mention_count", "rank", "price_score", "engagement_score", "final_score", "timestamp"},
        "ranking row",
    )

    symbol = ranking[0]["symbol"]

    r = client.get(f"/ranking/history/{symbol}")
    assert r.status_code == 200, f"/ranking/history/{symbol} failed: {r.status_code}"
    history = r.json()
    assert isinstance(history, list), "ranking/history should return a list"

    r = client.get(f"/stock/{symbol}/latest")
    assert r.status_code == 200, f"/stock/{symbol}/latest failed: {r.status_code}"
    _assert_keys(r.json(), {"symbol", "name", "sector", "price", "change_percent", "volume", "timestamp"}, "stock latest")

    r = client.get(f"/stock/{symbol}/market-history", params={"days": 7})
    assert r.status_code == 200, f"/stock/{symbol}/market-history failed: {r.status_code}"
    market_history = r.json()
    assert isinstance(market_history, list), "market-history should return a list"
    assert len(market_history) > 0, "market-history should return at least one row"
    _assert_keys(market_history[0], {"timestamp", "price", "volume", "is_stale"}, "market history row")

    r = client.get(f"/stock/{symbol}/history", params={"limit": 7})
    assert r.status_code == 200, f"/stock/{symbol}/history failed: {r.status_code}"

    r = client.get(f"/engagement/{symbol}/latest")
    assert r.status_code == 200, f"/engagement/{symbol}/latest failed: {r.status_code}"
    _assert_keys(r.json(), {"symbol", "mention_count", "sentiment_score", "timestamp"}, "engagement latest")

    r = client.get(f"/engagement/{symbol}/history", params={"limit": 5})
    assert r.status_code == 200, f"/engagement/{symbol}/history failed: {r.status_code}"
    engagement_history = r.json()
    assert isinstance(engagement_history, list), "engagement/history should return a list"
    assert len(engagement_history) > 0, "engagement/history should return at least one row"
    _assert_keys(engagement_history[0], {"id", "symbol", "mention_count", "sentiment_score", "timestamp"}, "engagement history row")

    r = client.get(f"/prediction/{symbol}/live")
    assert r.status_code == 200, f"/prediction/{symbol}/live failed: {r.status_code}"
    _assert_keys(r.json(), {"symbol", "predicted_price", "predicted_change_percent", "confidence", "direction", "timestamp"}, "prediction live")

    r = client.get(f"/news/{symbol}", params={"limit": 4})
    assert r.status_code == 200, f"/news/{symbol} failed: {r.status_code}"
    news = r.json()
    _assert_keys(news, {"symbol", "items"}, "news response")
    assert isinstance(news["items"], list), "news.items should be a list"

    r = client.get("/companies/search", params={"q": symbol[:2]})
    assert r.status_code == 200, f"/companies/search failed: {r.status_code}"
    companies = r.json()
    assert isinstance(companies, list), "companies/search should return a list"
    if companies:
        _assert_keys(companies[0], {"symbol", "name", "sector"}, "companies/search row")

    r = client.post("/refresh")
    assert r.status_code == 200, f"/refresh failed: {r.status_code}"
    _assert_keys(r.json(), {"ok", "updated", "timestamp"}, "refresh response")

    print("Frontend contract test passed")


if __name__ == "__main__":
    run()
