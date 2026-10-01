"""Daily -> monthly resampling."""

from __future__ import annotations

import pandas as pd


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily bars into one OHLCV row per (ticker, month).

    open  = first trading day's open   close = last trading day's close
    high  = max of month's highs       low   = min of month's lows
    volume = sum of month's volume
    """
    df = df.sort_values(["ticker", "date"])
    month = df["date"].dt.to_period("M").rename("month")

    monthly = (
        df.groupby(["ticker", month])
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        )
        .reset_index()
    )
    monthly["month"] = monthly["month"].astype(str)  # "YYYY-MM"
    return monthly
