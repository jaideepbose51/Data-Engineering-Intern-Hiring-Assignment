"""Standardise raw data types and drop unusable rows."""

from __future__ import annotations

import logging

import pandas as pd

from .config import ESSENTIAL_COLUMNS, NUMERIC_COLUMNS, REQUIRED_COLUMNS
from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy sorted by (ticker, date)."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["ticker"] = df["ticker"].astype("string").str.strip().str.upper()
    df[list(NUMERIC_COLUMNS)] = df[list(NUMERIC_COLUMNS)].apply(
        pd.to_numeric, errors="coerce"
    )

    before = len(df)
    df = df.dropna(subset=list(ESSENTIAL_COLUMNS))
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with missing/invalid essential values", dropped)

    df["ticker"] = df["ticker"].astype(str)
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)
