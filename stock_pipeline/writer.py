"""Output: one CSV per ticker."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def write_partitioned_files(df: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Write `result_{TICKER}.csv` for every ticker; return the paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for ticker, part in df.groupby("ticker"):
        path = output_dir / f"result_{ticker}.csv"
        part.to_csv(path, index=False)
        logger.info("Wrote %s (%d rows)", path, len(part))
        paths.append(path)
    return paths
