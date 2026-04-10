"""
Technical indicators service.
Uses yfinance for OHLCV history and the `ta` library for indicators.
"""

import yfinance as yf
import pandas as pd
from models.schemas import TechnicalIndicators
from utils.cache import cache
from datetime import datetime

try:
    import ta
    _TA_AVAILABLE = True
except ImportError:
    _TA_AVAILABLE = False


def _safe(val) -> float | None:
    try:
        v = float(val)
        return None if (v != v) else round(v, 4)   # NaN check
    except Exception:
        return None


async def get_technical_indicators(symbol: str) -> TechnicalIndicators:
    cache_key = cache.make_key("technical", symbol.upper())
    cached = cache.get(cache_key)
    if cached:
        return cached

    result = _compute(symbol)
    cache.set(cache_key, result, ttl=300)
    return result


def _compute(symbol: str) -> TechnicalIndicators:
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 20:
            return _empty(symbol)

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]

        if not _TA_AVAILABLE:
            return _manual_indicators(symbol, close)

        # ── RSI ───────────────────────────────────────────────────────────────
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()

        # ── MACD ─────────────────────────────────────────────────────────────
        macd_ind = ta.trend.MACD(close)
        macd_val   = macd_ind.macd()
        macd_sig   = macd_ind.macd_signal()
        macd_hist  = macd_ind.macd_diff()

        # ── SMA / EMA ─────────────────────────────────────────────────────────
        sma_20 = ta.trend.SMAIndicator(close, window=20).sma_indicator()
        sma_50 = ta.trend.SMAIndicator(close, window=50).sma_indicator()
        ema_12 = ta.trend.EMAIndicator(close, window=12).ema_indicator()

        # ── Bollinger Bands ───────────────────────────────────────────────────
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_mid   = bb.bollinger_mavg()

        # ── ATR ───────────────────────────────────────────────────────────────
        atr = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()

        # ── Signal logic ──────────────────────────────────────────────────────
        latest_rsi   = _safe(rsi.iloc[-1])
        latest_macd  = _safe(macd_val.iloc[-1])
        latest_sig   = _safe(macd_sig.iloc[-1])
        latest_close = _safe(close.iloc[-1])
        latest_sma50 = _safe(sma_50.iloc[-1])

        signal = _derive_signal(latest_rsi, latest_macd, latest_sig, latest_close, latest_sma50)

        return TechnicalIndicators(
            symbol=symbol.upper(),
            rsi_14=latest_rsi,
            macd=latest_macd,
            macd_signal=latest_sig,
            macd_hist=_safe(macd_hist.iloc[-1]),
            sma_20=_safe(sma_20.iloc[-1]),
            sma_50=latest_sma50,
            ema_12=_safe(ema_12.iloc[-1]),
            bb_upper=_safe(bb_upper.iloc[-1]),
            bb_lower=_safe(bb_lower.iloc[-1]),
            bb_mid=_safe(bb_mid.iloc[-1]),
            atr=_safe(atr.iloc[-1]),
            signal=signal,
        )

    except Exception:
        return _empty(symbol)


def _manual_indicators(symbol: str, close: pd.Series) -> TechnicalIndicators:
    """Basic RSI + SMA without ta library."""
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, 1e-9)
    rsi   = 100 - (100 / (1 + rs))

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    latest_rsi   = _safe(rsi.iloc[-1])
    latest_close = _safe(close.iloc[-1])
    latest_sma50 = _safe(sma50.iloc[-1])

    signal = _derive_signal(latest_rsi, None, None, latest_close, latest_sma50)

    return TechnicalIndicators(
        symbol=symbol.upper(),
        rsi_14=latest_rsi,
        sma_20=_safe(sma20.iloc[-1]),
        sma_50=latest_sma50,
        signal=signal,
    )


def _derive_signal(rsi, macd, macd_sig, price, sma50) -> str:
    bull_points = 0
    bear_points = 0

    if rsi is not None:
        if rsi < 35:
            bull_points += 2
        elif rsi > 65:
            bear_points += 2

    if macd is not None and macd_sig is not None:
        if macd > macd_sig:
            bull_points += 1
        else:
            bear_points += 1

    if price is not None and sma50 is not None:
        if price > sma50:
            bull_points += 1
        else:
            bear_points += 1

    if bull_points > bear_points + 1:
        return "BUY"
    if bear_points > bull_points + 1:
        return "SELL"
    return "HOLD"


def _empty(symbol: str) -> TechnicalIndicators:
    return TechnicalIndicators(symbol=symbol.upper(), signal="HOLD")
