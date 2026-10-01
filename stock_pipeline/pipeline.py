"""Orchestration: load -> clean -> validate -> resample -> indicators -> write."""

from __future__ import annotations

import logging

import pandas as pd

from .cleaner import clean_data
from .config import PipelineConfig
from .indicators import add_indicators
from .loader import load_data
from .transformer import aggregate_monthly
from .validator import validate_input, validate_output
from .writer import write_partitioned_files

logger = logging.getLogger(__name__)


def run_pipeline(config: PipelineConfig | None = None) -> pd.DataFrame:
    config = config or PipelineConfig()

    daily = clean_data(load_data(config.input_file))
    validate_input(daily, config)

    monthly = aggregate_monthly(daily)
    result = add_indicators(monthly, config)
    validate_output(result, config)

    write_partitioned_files(result, config.output_dir)
    logger.info("Pipeline complete: %d rows, %d columns", *result.shape)
    return result
