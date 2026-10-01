# Monthly Stock Pipeline

Resamples daily prices for 10 tickers into monthly OHLC bars, adds technical
indicators (SMA, EMA, Donchian, Bollinger, Z-score), and writes one CSV per ticker.
Pandas only, no third-party TA libraries.

## Run

```bash
pip install -r requirements.txt
# put the dataset at data/stock_data.csv
python main.py                      # or: python main.py --input X.csv --output out/
python -m pytest                    # run tests
```

Output: `output/result_{SYMBOL}.csv` — 10 files, 24 rows each.

## Structure

| Module | Responsibility |
|---|---|
| `config.py` | Paths, tickers, indicator windows (single `PipelineConfig` dataclass) |
| `loader.py` | Read CSV |
| `cleaner.py` | Types, whitespace, drop bad rows, sort |
| `validator.py` | Input checks (tickers, OHLC sanity, duplicates, 24 months) and output check |
| `transformer.py` | Daily -> monthly OHLCV |
| `indicators.py` | SMA / EMA / Donchian / Bollinger / Z-score (vectorised, per ticker) |
| `writer.py` | Partition by ticker and write CSVs |
| `pipeline.py` | Orchestrates the steps |
| `cli.py` | Argument parsing, logging, exit codes |

Calculation logic (`transformer`, `indicators`) is separate from file I/O (`loader`, `writer`).

## Output columns

`ticker, month, open, high, low, close, volume, sma_10, sma_20, ema_10, ema_20,
donchian_high_20, donchian_low_20, bb_mid_20, bb_upper_20, bb_lower_20, zscore_20`

## Assumptions

1. **Monthly OHLC**: open = first trading day's open, close = last trading day's close,
   high = month max, low = month min, volume = month sum. `close` (not `adjclose`) is used.
2. **Indicators use monthly values**, computed per ticker with no leakage across tickers.
3. **Windows are in months.** SMA/EMA 10 and 20 on 24 monthly rows means
   SMA/EMA 10 start at month 10 and SMA/EMA 20, Donchian, Bollinger and Z-score start at
   month 20. Earlier rows are left empty (NaN) rather than computed on partial windows.
4. **EMA** uses multiplier `2/(n+1)`, seeded with the SMA of the first `n` closes, as in the
   reference formula.
5. **Donchian / Bollinger / Z-score window = 20** and Bollinger `k = 2` (configurable in
   `config.py`). Standard deviation is the sample std (`ddof=1`, pandas default).
6. **Z-score** = `(close - rolling mean) / rolling std` over the same 20-month window.
7. Rows with missing/unparseable date, ticker or OHLC values are dropped and logged;
   the pipeline fails loudly if any ticker doesn't have exactly 24 months.
