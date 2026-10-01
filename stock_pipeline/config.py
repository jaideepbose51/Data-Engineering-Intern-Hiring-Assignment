"""Central configuration. Change behaviour here, not in the logic modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_COLUMNS: tuple[str, ...] = (
    "date", "volume", "open", "high", "low", "close", "adjclose", "ticker",
)
NUMERIC_COLUMNS: tuple[str, ...] = (
    "volume", "open", "high", "low", "close", "adjclose",
)
ESSENTIAL_COLUMNS: tuple[str, ...] = (
    "date", "ticker", "open", "high", "low", "close",
)


@dataclass(frozen=True)
class PipelineConfig:
    input_file: Path = PROJECT_ROOT / "data" / "stock_data.csv"
    output_dir: Path = PROJECT_ROOT / "output"

    tickers: tuple[str, ...] = (
        "AAPL", "AMD", "AMZN", "AVGO", "CSCO",
        "MSFT", "NFLX", "PEP", "TMUS", "TSLA",
    )
    expected_months: int = 24

    sma_windows: tuple[int, ...] = (10, 20)
    ema_windows: tuple[int, ...] = (10, 20)
    donchian_window: int = 20
    bollinger_window: int = 20
    bollinger_std: float = 2.0
    zscore_window: int = 20
