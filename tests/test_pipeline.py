import numpy as np
import pandas as pd
import pytest

from stock_pipeline.config import PipelineConfig
from stock_pipeline.exceptions import DataValidationError
from stock_pipeline.indicators import add_indicators
from stock_pipeline.pipeline import run_pipeline
from stock_pipeline.transformer import aggregate_monthly
from stock_pipeline.validator import validate_input


CFG = PipelineConfig()


# ============================================================
# TEST DATA GENERATOR
# ============================================================

def make_daily(tickers=CFG.tickers, months=24, seed=0):
    """
    Generate deterministic fake daily stock data for testing.

    This avoids depending on the real assignment CSV during
    unit tests.
    """

    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(
        "2023-01-02",
        periods=months * 22 + 40
    )

    dates = dates[
        dates < pd.Timestamp("2023-01-01")
        + pd.DateOffset(months=months)
    ]

    frames = []

    for ticker in tickers:

        close = (
            100
            + rng.normal(0, 1, len(dates)).cumsum()
        )

        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "volume": 1000,
                    "open": close - 0.1,
                    "high": close + 1,
                    "low": close - 1,
                    "close": close,
                    "adjclose": close,
                    "ticker": ticker,
                }
            )
        )

    return pd.concat(
        frames,
        ignore_index=True
    )


# ============================================================
# MONTHLY AGGREGATION TESTS
# ============================================================

def test_monthly_ohlc_uses_first_and_last_day():

    df = make_daily(["AAPL"])

    monthly = aggregate_monthly(df)

    january = df[
        df["date"]
        .dt.to_period("M")
        .astype(str)
        == "2023-01"
    ]

    row = monthly[
        monthly["month"] == "2023-01"
    ].iloc[0]

    # Open = first trading day's open
    assert row["open"] == january.iloc[0]["open"]

    # Close = last trading day's close
    assert row["close"] == january.iloc[-1]["close"]

    # High = maximum high during month
    assert row["high"] == january["high"].max()

    # Low = minimum low during month
    assert row["low"] == january["low"].min()

    # Exactly 24 months
    assert len(monthly) == 24


def test_monthly_volume_is_sum():

    df = make_daily(["AAPL"])

    monthly = aggregate_monthly(df)

    january = df[
        df["date"]
        .dt.to_period("M")
        .astype(str)
        == "2023-01"
    ]

    row = monthly[
        monthly["month"] == "2023-01"
    ].iloc[0]

    assert row["volume"] == january["volume"].sum()


def test_monthly_output_has_one_row_per_ticker_month():

    df = make_daily(
        ["AAPL", "AMD"]
    )

    monthly = aggregate_monthly(df)

    assert len(monthly) == 48

    counts = monthly.groupby("ticker").size()

    assert counts["AAPL"] == 24
    assert counts["AMD"] == 24


# ============================================================
# SMA TESTS
# ============================================================

def test_sma_10():

    monthly = aggregate_monthly(
        make_daily(["AAPL"])
    )

    output = add_indicators(
        monthly,
        CFG
    )

    close = output["close"]

    # First 9 values don't have enough observations
    assert output["sma_10"].iloc[:9].isna().all()

    # 10th value = mean of first 10 closes
    assert output["sma_10"].iloc[9] == pytest.approx(
        close.iloc[:10].mean()
    )


def test_sma_20():

    monthly = aggregate_monthly(
        make_daily(["AAPL"])
    )

    output = add_indicators(
        monthly,
        CFG
    )

    close = output["close"]

    # First 19 values don't have enough observations
    assert output["sma_20"].iloc[:19].isna().all()

    # 20th value = mean of first 20 closes
    assert output["sma_20"].iloc[19] == pytest.approx(
        close.iloc[:20].mean()
    )


# ============================================================
# EMA TESTS
# ============================================================

def test_ema_10_seed():

    monthly = aggregate_monthly(
        make_daily(["AAPL"])
    )

    output = add_indicators(
        monthly,
        CFG
    )

    close = output["close"]

    # EMA 10 smoothing constant
    k = 2 / (10 + 1)

    # First EMA is seeded using SMA 10
    expected_first_ema = close.iloc[:10].mean()

    assert output["ema_10"].iloc[9] == pytest.approx(
        expected_first_ema
    )

    # Next EMA uses recursive formula
    expected_second_ema = (
        (close.iloc[10] - output["ema_10"].iloc[9])
        * k
        + output["ema_10"].iloc[9]
    )

    assert output["ema_10"].iloc[10] == pytest.approx(
        expected_second_ema
    )


def test_ema_20_seed():

    monthly = aggregate_monthly(
        make_daily(["AAPL"])
    )

    output = add_indicators(
        monthly,
        CFG
    )

    close = output["close"]

    expected_first_ema = close.iloc[:20].mean()

    assert output["ema_20"].iloc[19] == pytest.approx(
        expected_first_ema
    )


# ============================================================
# BOLLINGER BAND TESTS
# ============================================================

def test_bollinger_bands():

    output = add_indicators(
        aggregate_monthly(
            make_daily(["AAPL"])
        ),
        CFG
    )

    close_window = output["close"].iloc[:20]

    mean = close_window.mean()
    std = close_window.std()

    expected_upper = mean + 2 * std
    expected_lower = mean - 2 * std

    assert output["bb_upper_20"].iloc[19] == pytest.approx(
        expected_upper
    )

    assert output["bb_lower_20"].iloc[19] == pytest.approx(
        expected_lower
    )


# ============================================================
# Z-SCORE TEST
# ============================================================

def test_zscore():

    output = add_indicators(
        aggregate_monthly(
            make_daily(["AAPL"])
        ),
        CFG
    )

    window = output["close"].iloc[:20]

    expected_zscore = (
        (window.iloc[-1] - window.mean())
        / window.std()
    )

    assert output["zscore_20"].iloc[19] == pytest.approx(
        expected_zscore
    )


# ============================================================
# DONCHIAN CHANNEL TESTS
# ============================================================

def test_donchian_high():

    output = add_indicators(
        aggregate_monthly(
            make_daily(["AAPL"])
        ),
        CFG
    )

    high_window = output["high"].iloc[:20]

    expected_high = high_window.max()

    assert output["donchian_high_20"].iloc[19] == pytest.approx(
        expected_high
    )


def test_donchian_low():

    output = add_indicators(
        aggregate_monthly(
            make_daily(["AAPL"])
        ),
        CFG
    )

    low_window = output["low"].iloc[:20]

    expected_low = low_window.min()

    assert output["donchian_low_20"].iloc[19] == pytest.approx(
        expected_low
    )


# ============================================================
# INDICATOR LEAKAGE TEST
# ============================================================

def test_indicators_do_not_leak_across_tickers():

    monthly = aggregate_monthly(
        make_daily(
            ["AAPL", "AMD"]
        )
    )

    output = add_indicators(
        monthly,
        CFG
    )

    for ticker, group in output.groupby("ticker"):

        # Every ticker must independently
        # have 9 NaN values for SMA 10
        assert group["sma_10"].iloc[:9].isna().all()

        # Every ticker must independently
        # have 19 NaN values for SMA 20
        assert group["sma_20"].iloc[:19].isna().all()


# ============================================================
# VALIDATION TESTS
# ============================================================

def test_validator_rejects_duplicates():

    df = make_daily()

    duplicate_df = pd.concat(
        [
            df,
            df.iloc[:1]
        ],
        ignore_index=True
    )

    with pytest.raises(DataValidationError):

        validate_input(
            duplicate_df,
            CFG
        )


def test_validator_rejects_missing_ticker():

    df = make_daily()

    # Remove TSLA completely
    df = df[
        df["ticker"] != "TSLA"
    ]

    with pytest.raises(DataValidationError):

        validate_input(
            df,
            CFG
        )


def test_validator_rejects_invalid_ohlc():

    df = make_daily(["AAPL"])

    # Make close higher than high
    df.loc[
        df.index[0],
        "close"
    ] = 1000

    df.loc[
        df.index[0],
        "high"
    ] = 500

    with pytest.raises(DataValidationError):

        validate_input(
            df,
            CFG
        )


# ============================================================
# END-TO-END PIPELINE TEST
# ============================================================

def test_end_to_end_writes_ten_files_with_24_rows(
    tmp_path
):

    # Create temporary input file
    input_file = tmp_path / "input.csv"

    make_daily().to_csv(
        input_file,
        index=False
    )

    # Temporary output directory
    output_dir = tmp_path / "output"

    config = PipelineConfig(
        input_file=input_file,
        output_dir=output_dir
    )

    # Run entire pipeline
    result = run_pipeline(config)

    # --------------------------------------------------------
    # Check final DataFrame
    # --------------------------------------------------------

    assert len(result) == 240

    assert result["ticker"].nunique() == 10

    counts = result.groupby("ticker").size()

    assert all(counts == 24)

    # --------------------------------------------------------
    # Check output files
    # --------------------------------------------------------

    files = sorted(
        output_dir.glob(
            "result_*.csv"
        )
    )

    # Exactly 10 files
    assert len(files) == 10

    # Every file must contain exactly 24 rows
    for file in files:

        output = pd.read_csv(file)

        assert len(output) == 24

        assert output["ticker"].nunique() == 1


# ============================================================
# OUTPUT COLUMN TEST
# ============================================================

def test_output_contains_required_columns():

    monthly = aggregate_monthly(
        make_daily(["AAPL"])
    )

    output = add_indicators(
        monthly,
        CFG
    )

    required_columns = {
        "ticker",
        "month",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "sma_10",
        "sma_20",
        "ema_10",
        "ema_20",
        "donchian_high_20",
        "donchian_low_20",
        "bb_middle_20",
        "bb_upper_20",
        "bb_lower_20",
        "zscore_20",
    }

    assert required_columns.issubset(
        set(output.columns)
    )


# ============================================================
# NO DUPLICATE MONTHS IN OUTPUT
# ============================================================

def test_output_has_no_duplicate_ticker_month():

    monthly = aggregate_monthly(
        make_daily()
    )

    output = add_indicators(
        monthly,
        CFG
    )

    duplicates = output.duplicated(
        subset=[
            "ticker",
            "month"
        ]
    )

    assert not duplicates.any()


# ============================================================
# EXACT TICKER SET TEST
# ============================================================

def test_output_contains_expected_tickers():

    monthly = aggregate_monthly(
        make_daily()
    )

    output = add_indicators(
        monthly,
        CFG
    )

    assert set(output["ticker"]) == set(
        CFG.tickers
    )