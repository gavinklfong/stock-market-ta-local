# Technical Analysis (TA) Indicator Modules

Modular, parallel pipeline that computes technical analysis indicators from daily OHLCV data. Each module reads raw market data, computes its own set of indicators, and writes an independent CSV. An orchestrator then merges all per-module outputs into a unified analysis file per ticker.

## Quick Start

```bash
# Run all modules in parallel
python app/calculate-ta/run_calculation.py

# Run a subset (e.g. trend + momentum only)
python app/calculate-ta/run_calculation.py trend momentum
```

## Output File Structure

| File Pattern | Contents |
|---|---|
| `data/ta-data/{ticker}_ta_{type}.csv` | Per-module output: `Date` + only this module's `ta_` columns |
| `data/ta-data/{ticker}.csv` | Merged file: `Date` + all `ta_` columns from all 8 modules |

Each per-module CSV contains **only** `Date` and the indicators that module produces — no OHLCV columns, no columns from other modules.

---

## Indicator Summary

All technical indicators are grouped by analysis category below. Each module produces independent `ta_`-prefixed columns that are later merged into a unified CSV per ticker.

| Category | Column | Description |
|---|---|---|
| **Trend** | `ta_ema20`, `ta_ema50`, `ta_ema200` | Exponential Moving Averages (20, 50, 200 periods) |
| | `ta_ma20`, `ta_ma50`, `ta_sma10` | Simple Moving Averages (20, 50, 10 periods) |
| | `ta_price_ma20_ratio` | Close / MA20 — price relative to 20-day MA |
| | `ta_ma20_slope`, `ta_ma50_slope` | Rate of change of MA20/MA50 over 10-bar lookback |
| | `ta_supertrend` | SuperTrend indicator line value |
| | `ta_supertrend_direction` | +1 = uptrend, −1 = downtrend |
| | `ta_supertrend_upper`, `ta_supertrend_lower` | Active SuperTrend band (upper in downtrend, lower in uptrend) |
| | `ta_donchian_upper`, `ta_donchian_lower` | Donchian Channel upper (resistance) and lower (support) |
| | `ta_keltner_upper`, `ta_keltner_lower` | Keltner Channel upper and lower (ATR-based bands around EMA of typical price) |
| **Momentum** | `ta_rsi14` | Relative Strength Index (14-period, Wilder's smoothing) |
| | `ta_macd_line` | MACD line (EMA12 − EMA26) |
| | `ta_macd_signal` | Signal line (EMA9 of MACD line) |
| | `ta_macd_histogram` | MACD − Signal (divergence/convergence) |
| | `ta_roc20` | Rate of Change (20-period, in percent) |
| | `ta_williams_r` | Williams %R (14-period, oscillator from 0 to −100) |
| **Volume** | `ta_obv` | On-Balance Volume (cumulative) |
| | `ta_adl` | Accumulation Distribution Line (cumulative CLV × Volume) |
| | `ta_cmf` | Chaikin Money Flow (20-period) |
| | `ta_vwap` | Volume-Weighted Average Price (20-period rolling) |
| | `ta_ofi` | Order Flow Imbalance, normalized to [−1, 1] |
| | `ta_log_volume` | Natural log of volume |
| **Volatility** | `ta_atr14` | Average True Range (14-period, Wilder's smoothing) |
| | `ta_normalized_atr14` | ATR / Close — volatility as a percentage of price |
| | `ta_bband_upper`, `ta_bband_lower` | Bollinger Bands upper/lower (20-period, 2σ) |
| | `ta_bband_middle` | Bollinger middle = SMA(20) |
| | `ta_hvol20` | Historical Volatility (20-period log-return std dev, annualized) |
| | `ta_parkinson_vol` | Parkinson Volatility (20-period high-low range, annualized) |
| **Regime** | `ta_hmm_regime` | HMM regime state: 0 = Bull, 1 = Bear, 2 = Volatile |
| | `ta_hmm_regime_prob_0/1/2` | Posterior probability for Bull, Bear, Volatile |
| | `ta_garch_vol`, `ta_garch_sq` | GARCH(1,1) conditional volatility and variance |
| | `ta_log_return` | Log return: `ln(close[t] / close[t−1])` |
| **Structure** | `ta_swing_high`, `ta_swing_low` | Price at most recent swing high / low |
| | `ta_swing_high_idx`, `ta_swing_low_idx` | Index of most recent swing high / low |
| | `ta_hh`, `ta_hl`, `ta_lh`, `ta_ll` | Higher High, Higher Low, Lower High, Lower Low flags |
| | `ta_trend` | Net trend: 1 = bullish, −1 = bearish, 0 = undetermined |
| | `ta_bos`, `ta_choch` | Break of Structure (continuation) / Change of Character (reversal) |
| | `ta_nearest_resistance`, `ta_nearest_support` | Clusters of swing highs/lows within 100-bar lookback |
| **Return** | `ta_return_5d`, `ta_return_10d`, `ta_return_20d` | Forward return over 5, 10, 20 trading days |

---

## Modules

### 1. Trend (`calculate_trend.py`)

**Dependencies:** `pandas` (stdlib: `math`, `os`)

**Input columns:** `Close`, `High`, `Low`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_ema20` | float | Exponential Moving Average (20-period) |
| `ta_ema50` | float | EMA (50-period) |
| `ta_ema200` | float | EMA (200-period) |
| `ta_supertrend` | float | SuperTrend line value |
| `ta_supertrend_direction` | int | +1 = uptrend, -1 = downtrend |
| `ta_supertrend_upper` | float | Upper band (active in downtrend) |
| `ta_supertrend_lower` | float | Lower band (active in uptrend) |
| `ta_ma20` | float | Simple Moving Average (20-period) |
| `ta_ma50` | float | SMA (50-period) |
| `ta_sma10` | float | SMA (10-period) |
| `ta_ma20_slope` | float | Change in MA20 over 10-bar lookback |
| `ta_ma50_slope` | float | Change in MA50 over 10-bar lookback |
| `ta_price_ma20_ratio` | float | Close / MA20 (price relative to MA20) |
| `ta_donchian_upper` | float | Donchian Upper channel (highest high over 20-period window) |
| `ta_donchian_lower` | float | Donchian Lower channel (lowest low over 20-period window) |
| `ta_keltner_upper` | float | Keltner Upper channel (EMA of typical price + 2×ATR) |
| `ta_keltner_lower` | float | Keltner Lower channel (EMA of typical price − 2×ATR) |

**Calculation logic:**

- **EMA** — Incremental EMA seeded with SMA of the first `period` values. Applies smoothing factor `k = 2/(period+1)` iteratively.
- **SuperTrend** — Uses Wilder's ATR(14) internally. Mid-point = `(High + Low) / 2`. Raw bands = mid ± 3×ATR. Bands are smoothed (upper only decreases, lower only increases). Direction flips when price crosses the opposite band.
- **SMA** — Standard rolling mean over the specified window.
- **MA Slope** — `(MA_current - MA_lookback_back) / lookback` where lookback = 10.
- **Price/MA20 Ratio** — `Close / MA20`, `None` when MA20 is null or zero.
- **Donchian Channels(20)** — Upper channel = highest high over the last 20 bars. Lower channel = lowest low over the last 20 bars. Defines a price envelope; price at the upper band suggests a breakout to new highs, price at the lower suggests a breakdown to new lows. Channel width = upper − lower (volatility measure).
- **Keltner Channels** — Typical Price (TP) = (High + Low + Close) / 3. Middle line = EMA(TP, 20). Upper band = Middle + 2 × ATR(10). Lower band = Middle − 2 × ATR(10). Similar to Bollinger Bands but uses ATR instead of standard deviation for the bands. Channel width = 4 × ATR.

**Minimum data:** 200 bars for EMA200; 50 for EMA50; 20 for EMA20/SMA20/SMA10/Donchian/Keltner.

---

### 2. Momentum (`calculate_momentum.py`)

**Dependencies:** `pandas` (stdlib: `os`, `sys`, `threading`)

**Input columns:** `High`, `Low`, `Close`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_rsi14` | float | Relative Strength Index (14-period) |
| `ta_macd_line` | float | MACD line (EMA12 − EMA26) |
| `ta_macd_signal` | float | Signal line (EMA9 of MACD line) |
| `ta_macd_histogram` | float | MACD − Signal |
| `ta_roc20` | float | Rate of Change (20-period), in percent |
| `ta_williams_r` | float | Williams %R (14-period), range 0 to −100 |
| `ta_cci` | float | Commodity Channel Index (20-period), no bounds |
| `ta_tsi` | float | True Strength Index (25, 13), ranges ~−100 to +100 |

**Calculation logic:**

- **RSI(14)** — Wilder's smoothed RSI. Initial average gain/loss = SMA of first 14 price changes. Subsequent averages use smoothing: `(prev_avg × (period−1) + current_change) / period`. If avg_loss = 0, RSI = 100 (if avg_gain > 0) or 50 (if both zero).
- **MACD** — Fast EMA(12) − Slow EMA(26) gives the MACD line. Signal line = EMA(9) of the MACD line values. Histogram = MACD − Signal.
- **ROC(20)** — `(close[t] − close[t−20]) / close[t−20] × 100`.
- **Williams %R(14)** — `(Highest High(14) − Close) / (Highest High(14) − Lowest Low(14)) × −100`. Oscillator ranging from 0 to −100. Overbought above −20, oversold below −80.
- **CCI(20)** — Commodity Channel Index. Typical Price = `(High + Low + Close) / 3`. CCI = `(TP − SMA(TP)) / (0.015 × Mean Deviation)` where Mean Deviation = mean of `|TP − SMA(TP)|` over 20 bars. No upper/lower bounds — values above +100 suggest overbought, below −100 suggest oversold.
- **TSI(25, 13)** — True Strength Index. Price changes: `d = close[t] − close[t−1]`. Double EMA of `d` using fast (25) then slow (13) periods. Double EMA of `|d|` the same way. TSI = `100 × double_ema(d) / double_ema(|d|)`. Oscillator roughly in −100 to +100 range. Positive in uptrends, negative in downtrends.

**Minimum data:** 15 bars for RSI; 21 bars for ROC; ~26+ bars for MACD; 14 bars for Williams %R; 20 bars for CCI; 38 bars for TSI.

---

### 3. Volume (`calculate_volume.py`)

**Dependencies:** `pandas`, `math` (stdlib: `os`)

**Input columns:** `High`, `Low`, `Close`, `Volume`, `Open`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_obv` | float | On-Balance Volume (cumulative) |
| `ta_adl` | float | Accumulation Distribution Line (cumulative CLV × Volume) |
| `ta_cmf` | float | Chaikin Money Flow (20-period) |
| `ta_vwap` | float | Rolling Volume-Weighted Average Price (20-period) |
| `ta_ofi` | float | Order Flow Imbalance (normalized) |
| `ta_log_volume` | float | Natural log of volume |

**Calculation logic:**

- **OBV** — Cumulative volume: +volume if close > previous close, −volume if close < previous close, unchanged if equal. Starts at first bar's volume.
- **ADL** — Accumulation Distribution Line. Closing Location Value (CLV) = `((Close − Low) − (High − Close)) / (High − Low)`. CLV = 0 when High = Low. ADL = cumulative sum of CLV × Volume, starting at bar 0.
- **CMF(20)** — Chaikin Money Flow. Money Flow Volume = `((Close − Low) − (High − Close)) / (High − Low) × Volume`. Rolling 20-period sum of MFV / sum of volume. Uses a rolling 20-element buffer with modulo indexing.
- **VWAP(20)** — Rolling Volume-Weighted Average Price. Typical price = `(High + Low + Close) / 3`. Sliding window of 20 bars; incrementally removes oldest and adds newest element.
- **OFI** — Order Flow Imbalance = `(Close − Open) / (High − Low)`, normalized to [−1, 1]. Returns 0 when High = Low.
- **Log Volume** — `ln(Volume)` for `Volume > 0`, else `None`.

**Minimum data:** 20 bars for CMF and VWAP. OBV and OFI work from bar 1+.

---

### 4. Volatility (`calculate_volatility.py`)

**Dependencies:** `pandas`, `math` (stdlib: `os`)

**Input columns:** `High`, `Low`, `Close`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_atr14` | float | Average True Range (14-period, Wilder's smoothing) |
| `ta_normalized_atr14` | float | ATR / Close (ATR as % of price) |
| `ta_bband_upper` | float | Bollinger Bands upper (20, 2σ) |
| `ta_bband_middle` | float | Bollinger Bands middle = SMA(20) |
| `ta_bband_lower` | float | Bollinger Bands lower (20, 2σ) |
| `ta_hvol20` | float | Historical Volatility (20-period, annualized) |
| `ta_parkinson_vol` | float | Parkinson Volatility (20-period, annualized) |

**Calculation logic:**

- **ATR(14)** — Wilder's ATR. True Range = `max(High − Low, |High − prev_close|, |Low − prev_close|)`. First TR = High − Low (no prior close). Seed ATR = SMA of first 14 TRs. Subsequent: `TR × k + prev_ATR × (1−k)` where `k = 2/(14+1)`.
- **Normalized ATR** — `ATR / Close`, giving ATR as a fraction of price.
- **Bollinger Bands(20, 2)** — Middle = SMA(20). Upper/Lower = Middle ± 2 × population standard deviation of the 20-bar window.
- **Historical Volatility(20)** — Standard deviation of 20-period log returns, annualized by multiplying by √252. Log return = `ln(close[t] / close[t−1])`. Population std dev (not sample). Returns `None` for the first 20 bars.
- **Parkinson Volatility(20)** — Uses the intra-bar high-low range to estimate volatility, which is more statistically efficient than close-to-close returns. Formula: `sqrt( (1 / (4 × ln(2) × n)) × Σ ln(high_i / low_i)² )`. Annualized by multiplying by √252. Returns `None` for the first 19 bars (needs 20 bars for the first complete window).

**Minimum data:** 15 bars for ATR; 20 bars for Bollinger Bands; 21 bars for Historical Volatility; 20 bars for Parkinson Volatility.

---

### 5. Regime (`calculate_regime.py`)

**Dependencies:** `pandas`, `numpy`, `arch`, `hmmlearn` (stdlib: `os`, `sys`, `math`, `warnings`)

**Input columns:** `Close`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_garch_vol` | float | GARCH(1,1) conditional volatility (σₜ) |
| `ta_garch_sq` | float | GARCH(1,1) conditional variance (σ²ₜ) |
| `ta_log_return` | float | Log return: `ln(close[t] / close[t−1])` |
| `ta_hmm_regime` | int | HMM regime: 0 = Bull, 1 = Bear, 2 = Volatile |
| `ta_hmm_regime_prob_0` | float | P(Bull) — posterior probability |
| `ta_hmm_regime_prob_1` | float | P(Bear) — posterior probability |
| `ta_hmm_regime_prob_2` | float | P(Volatile) — posterior probability |

**Calculation logic:**

- **GARCH(1,1)** — Fits a GARCH(1,1) model via MLE on log returns (mean = zero, normal distribution). Extracts conditional volatility for each bar. Fails gracefully (returns all `None`) if fitting fails.
- **Log Return** — `ln(close[t] / close[t−1])` for t > 0. First bar is `None`. Returns 0.0 if either price ≤ 0.
- **HMM(3-state)** — Fits a Gaussian HMM on standardized log returns with 3 components. Viterbi decoding gives the most likely state per bar. States are labeled post-hoc by emission means: highest mean = Bull (0), lowest = Bear (1), middle = Volatile (2). Posterior probabilities are remapped to match.

**Dependencies:** Requires `arch` (for GARCH fitting) and `hmmlearn` (for HMM fitting) — both are heavy ML packages.

**Minimum data:** 30 log returns for GARCH; 30 observations for HMM (3 states × 10).

---

### 6. Structure (`calculate_structure.py`)

**Dependencies:** `pandas` (stdlib: `os`, `sys`)

**Input columns:** `High`, `Low`, `Close`

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_swing_high` | float | Price at the most recent swing high, or `None` |
| `ta_swing_low` | float | Price at the most recent swing low, or `None` |
| `ta_swing_high_idx` | int | Index of the most recent swing high (−1 if none) |
| `ta_swing_low_idx` | int | Index of the most recent swing low (−1 if none) |
| `ta_hh` | int | 1 if this bar is a Higher High, else 0 |
| `ta_hl` | int | 1 if this bar is a Higher Low, else 0 |
| `ta_lh` | int | 1 if this bar is a Lower High, else 0 |
| `ta_ll` | int | 1 if this bar is a Lower Low, else 0 |
| `ta_trend` | int | 1 = bullish, −1 = bearish, 0 = undetermined |
| `ta_bos` | int | 1 = Break of Structure (trend continuation) |
| `ta_choch` | int | 1 = Change of Character (trend reversal) |
| `ta_nearest_resistance` | float | Nearest resistance level (clustered swing high) |
| `ta_nearest_support` | float | Nearest support level (clustered swing low) |

**Calculation logic:**

- **Swing Detection** — Pivot-point approach with `lookback=5`. A swing high at index `i` requires `high[i] >= max(high[i−lookback:i])` AND `high[i] >= max(high[i+1:i+lookback+1])`. Same logic for swing lows.
- **HH/HL/LH/LL** — Compares current swing high/low to the previous swing of the same type. HH = current HH > previous HH; LH = current HH < previous HH. HL = current HL > previous HL; LL = current LL < previous LL.
- **Trend** — Driven by BOS/CHoCH signals. BOS confirms trend continuation; CHoCH flips the trend state (reversal).
- **BOS (Break of Structure)** — New swing high exceeds prior swing high in an uptrend, or new swing low breaks below prior swing low in a downtrend.
- **CHoCH (Change of Character)** — First BOS against the prevailing trend, signaling a potential reversal.
- **Support/Resistance** — Identifies swing highs/lows within a 100-bar lookback. Clusters nearby levels within 2% tolerance. Finds the nearest resistance (swing high) above and support (swing low) below the midpoint price.

**Minimum data:** `lookback × 2 + 1 = 11` bars for any structure detection.

---

### 7. Return (`calculate_return.py`)

**Dependencies:** `pandas` (stdlib: `os`, `sys`)

**Input columns:** `Close` (Open, High, Low, Volume are accepted but unused)

**Output columns:**

| Column | Type | Description |
|---|---|---|
| `ta_return_5d` | float | Forward return over 5 trading days |
| `ta_return_10d` | float | Forward return over 10 trading days |
| `ta_return_20d` | float | Forward return over 20 trading days |

**Calculation logic:**

- **Forward Return** — For each horizon H: `return_H[t] = (close[t+H] − close[t]) / close[t]`. Returns `None` for the last H bars where future data is unavailable.

**Minimum data:** 20 bars for the 20-day horizon.

---

## Module Dependency Graph

All 7 modules are **independent** — each reads only from raw OHLCV data in `data/market-data/`. There are no inter-module dependencies:

```
                    ┌─────────────────────────────────┐
                    │    data/market-data/*.csv       │
                    │       (raw OHLCV from yfinance) │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │   trend      │  │  momentum    │  │   volume     │
     └──────────────┘  └──────────────┘  └──────────────┘
              │                │                │
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ volatility   │  │   regime     │  │  structure   │
     └──────────────┘  └──────────────┘  └──────────────┘
              │                │                │
     ┌────────────────────────────────────────────────┐
     │              return                             │
     └────────────────────────────────────────────────┘
                               │
                      ┌────────▼────────┐
                      │   MERGE          │
                      │ {ticker}.csv     │
                      └─────────────────┘
```

---

## Execution

### Orchestrator (`run_calculation.py`)

Runs all modules in parallel via `concurrent.futures.ThreadPoolExecutor`, then merges per-module outputs into `{ticker}.csv`.

```bash
# All modules (parallel)
python app/calculate-ta/run_calculation.py

# Subset
python app/calculate-ta/run_calculation.py trend momentum

# Dry-run (print only)
python app/calculate-ta/run_calculation.py --dry-run
```

### Individual Modules

Each module can be run independently:

```bash
python app/calculate-ta/calculate_trend.py
python app/calculate-ta/calculate_momentum.py
# ... etc.
```

### Adding a New Module

1. Create `app/calculate-ta/calculate_<name>.py` with:
   - `compute_<name>_columns(highs, lows, closes, volumes, n, ...)` → dict of `col_name → list`
   - `process_csv(input_path, output_path, total_files, current_file)` → row count
   - Call `main()` at the bottom
2. Register in `run_calculation.py` `MODULES` and `ALL_ORDER` dicts.

---

## Shared Infrastructure (`common.py`)

### `read_yfinance_csv(input_path)`

Reads yfinance CSVs with multi-row header support. Handles:
- **2-row headers:** `Price,Open,High,...` → `Date,,,,,`
- **3-row headers:** `Ticker,NG.L,...` → `Price,Open,High,...` → `Date,,,,,`
- **Single-row headers:** standard CSV (fallback)

### `main(module_name, description, process_csv_fn, ...)`

Thread-pool pipeline runner. Each module calls this to:
1. Discover CSV files in `data/market-data/`
2. Submit processing tasks to a `ThreadPoolExecutor` (max_workers=10)
3. Write output to `data/ta-data/{ticker}_ta_{suffix}.csv`
4. Display file-level progress bars

### Progress Helpers

| Function | Purpose |
|---|---|
| `progress_bar(current, total, prefix)` | Single-line bar with percentage |
| `file_progress_bar(filename, current, total)` | One bar per CSV file |
| `row_progress_bar(filename, total_rows, current_row)` | Per-file row progress |

---

## Dependencies (`requirements.txt`)

### Core
- `pandas >= 2.0.0`
- `numpy >= 1.24.0`

### Regime Module (heavy ML)
- `arch >= 7.0.0` — GARCH model fitting
- `hmmlearn >= 0.3.0` — Hidden Markov Model

### Transitive Dependencies
- `scipy >= 1.10.0` — required by `arch`
- `statsmodels >= 0.14.0` — required by `arch`
- `scikit-learn >= 1.3.0` — required by `hmmlearn`
- `patsy >= 0.5.0` — required by `statsmodels`
- `formulaic >= 1.0.0` — required by `statsmodels`
- `packaging >= 22.0` — required by `arch`
- `joblib >= 1.2.0` — required by `scikit-learn`
- `threadpoolctl >= 3.1.0` — required by `scikit-learn`
- `typing_extensions >= 4.0.0` — required by `formulaic`
- `wrapt >= 1.14.0` — required by `formulaic`
- `interface_meta >= 2.0.0` — required by `formulaic`
- `narwhals >= 1.0.0` — required by `formulaic`

Install with:
```bash
pip install -r app/calculate-ta/requirements.txt
```

---

## Notes

- **Column naming convention:** All output columns use the `ta_` prefix (e.g. `ta_rsi14`, `ta_ema20`).
- **Missing data:** Indicators that require more data than available return `None` (not 0) for those positions.
- **Date format:** Output CSVs use `YYYY-MM-DD` string format.
- **Thread safety:** Progress bar state is protected by a threading lock to prevent garbled output from concurrent workers.
- **Error handling:** If a module fails on one ticker, it logs the error to stderr and continues with remaining tickers.
