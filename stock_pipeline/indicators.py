"""Technical indicators computed on monthly bars, per ticker."""

from __future__ import annotations

import pandas as pd
from pandas.core.groupby import SeriesGroupBy

from .config import PipelineConfig


def _rolling(grouped: SeriesGroupBy, window: int, func: str) -> pd.Series:
    """Per-group rolling stat; NaN until a full window exists."""
    rolled = getattr(grouped.rolling(window, min_periods=window), func)()
    return rolled.droplevel(0)  # back to the original row index


def _sma_seeded_ema(close: pd.Series, span: int) -> pd.Series:
    """EMA seeded with the SMA of the first `span` values.

    multiplier = 2 / (span + 1); EMA_t = (P_t - EMA_{t-1}) * k + EMA_{t-1}
    Values before the first full window are NaN.
    """
    if len(close) < span:
        return pd.Series(float("nan"), index=close.index)
    seeded = close.astype(float).copy()
    seeded.iloc[: span - 1] = float("nan")
    seeded.iloc[span - 1] = close.iloc[:span].mean()
    return seeded.ewm(span=span, adjust=False).mean()


def add_indicators(monthly: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Return `monthly` plus SMA, EMA, Donchian, Bollinger and Z-score columns."""
    df = monthly.sort_values(["ticker", "month"]).reset_index(drop=True)
    close = df.groupby("ticker")["close"]
    high = df.groupby("ticker")["high"]
    low = df.groupby("ticker")["low"]

    for n in config.sma_windows:
        df[f"sma_{n}"] = _rolling(close, n, "mean")

    for n in config.ema_windows:
        df[f"ema_{n}"] = close.transform(lambda s, n=n: _sma_seeded_ema(s, n))

    n = config.donchian_window
    df[f"donchian_high_{n}"] = _rolling(high, n, "max")
    df[f"donchian_low_{n}"] = _rolling(low, n, "min")

    n = config.bollinger_window
    mid, sd = _rolling(close, n, "mean"), _rolling(close, n, "std")
    df[f"bb_middle_{n}"] = mid
    df[f"bb_upper_{n}"] = mid + config.bollinger_std * sd
    df[f"bb_lower_{n}"] = mid - config.bollinger_std * sd

    n = config.zscore_window
    z_mean, z_std = _rolling(close, n, "mean"), _rolling(close, n, "std")
    df[f"zscore_{n}"] = (df["close"] - z_mean) / z_std

    return df
