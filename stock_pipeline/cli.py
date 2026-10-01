"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

from .config import PipelineConfig
from .exceptions import PipelineError
from .pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily -> monthly stock pipeline")
    parser.add_argument("--input", type=Path, help="Path to the daily CSV")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = PipelineConfig()
    if args.input:
        config = replace(config, input_file=args.input)
    if args.output:
        config = replace(config, output_dir=args.output)

    try:
        run_pipeline(config)
    except (PipelineError, FileNotFoundError) as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
