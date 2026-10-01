"""Data-quality checks for the cleaned input and the final output."""

from __future__ import annotations

import logging

import pandas as pd

from .config import PipelineConfig
from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


def _check_tickers(df: pd.DataFrame, config: PipelineConfig) -> list[str]:
    actual, expected = set(df["ticker"]), set(config.tickers)
    errors = []
    if actual - expected:
        errors.append(f"Unexpected tickers: {sorted(actual - expected)}")
    if expected - actual:
        errors.append(f"Missing tickers: {sorted(expected - actual)}")
    return errors


def _check_ohlc(df: pd.DataFrame) -> list[str]:
    bad = (
        (df["high"] < df[["open", "close", "low"]].max(axis=1))
        | (df["low"] > df[["open", "close", "high"]].min(axis=1))
    )
    return [f"{int(bad.sum())} rows with invalid OHLC relationships"] if bad.any() else []


def _check_duplicates(df: pd.DataFrame) -> list[str]:
    n = int(df.duplicated(subset=["date", "ticker"]).sum())
    return [f"{n} duplicate (date, ticker) rows"] if n else []


def _check_month_coverage(df: pd.DataFrame, config: PipelineConfig) -> list[str]:
    counts = df.groupby("ticker")["date"].agg(lambda s: s.dt.to_period("M").nunique())
    bad = counts[counts != config.expected_months]
    return (
        [f"Tickers without {config.expected_months} months: {bad.to_dict()}"]
        if not bad.empty
        else []
    )


def validate_input(df: pd.DataFrame, config: PipelineConfig) -> None:
    """Run all input checks and raise one error listing every problem."""
    errors = (
        _check_tickers(df, config)
        + _check_ohlc(df)
        + _check_duplicates(df)
        + _check_month_coverage(df, config)
    )
    if errors:
        raise DataValidationError("; ".join(errors))
    logger.info("Input validation passed")


def validate_output(df: pd.DataFrame, config: PipelineConfig) -> None:
    """Each ticker must have exactly `expected_months` rows."""
    counts = df.groupby("ticker").size()
    bad = counts[counts != config.expected_months]
    if bad.any() or set(counts.index) != set(config.tickers):
        raise DataValidationError(f"Unexpected output row counts: {counts.to_dict()}")
    logger.info("Output validation passed")
