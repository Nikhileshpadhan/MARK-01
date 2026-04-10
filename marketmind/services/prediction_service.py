"""
Price prediction service.
Model : Ridge regression on 15 engineered features (returns, momentum,
        rolling stats, volume ratio). Predictions for 1d / 7d / 30d.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from models.schemas import PricePrediction
from utils.cache import cache
from utils.config import get_settings

settings = get_settings()


async def get_prediction(symbol: str, current_price: float) -> PricePrediction:
    cache_key = cache.make_key("prediction", symbol.upper())
    cached = cache.get(cache_key)
    if cached:
        return cached

    result = _run_model(symbol, current_price)
    cache.set(cache_key, result, ttl=3600)   # predictions are slow-moving
    return result


def _run_model(symbol: str, current_price: float) -> PricePrediction:
    lookback = settings.prediction_lookback_days
    try:
        df = yf.download(symbol, period=f"{lookback + 60}d", interval="1d",
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 40:
            return _flat_prediction(symbol, current_price)

        df = _build_features(df)
        if df.empty:
            return _flat_prediction(symbol, current_price)

        # Train on all but last row, predict future
        X = df.drop(columns=["target_1d"]).values
        y = df["target_1d"].values

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("ridge",  Ridge(alpha=1.0)),
        ])
        model.fit(X[:-1], y[:-1])

        latest_features = X[-1].reshape(1, -1)
        pred_1d = float(model.predict(latest_features)[0])
        r2 = max(0.0, model.score(X[:-1], y[:-1]))
        confidence = round(min(r2, 0.95), 2)

        # Extrapolate 7d / 30d naively via compounded daily return
        daily_return = (pred_1d - current_price) / current_price
        pred_7d  = round(current_price * (1 + daily_return) ** 7, 4)
        pred_30d = round(current_price * (1 + daily_return) ** 30, 4)

        # Support / resistance from rolling 20-day high/low
        close = df.index   # use original price series
        recent = yf.download(symbol, period="30d", interval="1d",
                              progress=False, auto_adjust=True)
        if isinstance(recent.columns, pd.MultiIndex):
            recent.columns = recent.columns.get_level_values(0)

        support    = round(float(recent["Low"].min()), 4)
        resistance = round(float(recent["High"].max()), 4)

        direction = (
            "UP" if pred_1d > current_price * 1.002
            else "DOWN" if pred_1d < current_price * 0.998
            else "SIDEWAYS"
        )

        result = PricePrediction(
            symbol=symbol.upper(),
            current_price=round(current_price, 4),
            predicted_price_1d=round(pred_1d, 4),
            predicted_price_7d=pred_7d,
            predicted_price_30d=pred_30d,
            confidence=confidence,
            model_used="Ridge Regression (15 technical features)",
            direction=direction,
            support_level=support,
            resistance_level=resistance,
            timestamp=datetime.utcnow(),
        )
        return result

    except Exception:
        return _flat_prediction(symbol, current_price)


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    c = df["Close"]

    df["ret_1"]    = c.pct_change(1)
    df["ret_3"]    = c.pct_change(3)
    df["ret_5"]    = c.pct_change(5)
    df["ret_10"]   = c.pct_change(10)
    df["sma_5"]    = c.rolling(5).mean()
    df["sma_20"]   = c.rolling(20).mean()
    df["std_5"]    = c.rolling(5).std()
    df["std_20"]   = c.rolling(20).std()
    df["rsi"]      = _rsi(c, 14)
    df["mom_10"]   = c - c.shift(10)
    df["vol_ratio"]= df["Volume"] / df["Volume"].rolling(20).mean()
    df["hl_range"] = (df["High"] - df["Low"]) / c
    df["gap"]      = (df["Open"] - c.shift(1)) / c.shift(1)
    df["close_pos"]= (c - df["Low"]) / (df["High"] - df["Low"] + 1e-9)
    df["target_1d"]= c.shift(-1)   # next day's close

    df = df.dropna()
    feature_cols = [
        "ret_1","ret_3","ret_5","ret_10",
        "sma_5","sma_20","std_5","std_20",
        "rsi","mom_10","vol_ratio","hl_range","gap","close_pos",
        "target_1d",
    ]
    return df[feature_cols]


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(window).mean()
    loss  = (-delta.clip(upper=0)).rolling(window).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _flat_prediction(symbol: str, current_price: float) -> PricePrediction:
    return PricePrediction(
        symbol=symbol.upper(),
        current_price=round(current_price, 4),
        predicted_price_1d=round(current_price, 4),
        predicted_price_7d=round(current_price, 4),
        predicted_price_30d=round(current_price, 4),
        confidence=0.0,
        model_used="Insufficient data",
        direction="SIDEWAYS",
        support_level=round(current_price * 0.95, 4),
        resistance_level=round(current_price * 1.05, 4),
        timestamp=datetime.utcnow(),
    )
