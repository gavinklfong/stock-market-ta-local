# Market Situation Review — Executive Summary (Simplified)

## Objective

Assess the market situation for `{ticker}` as of `{evaluation_date}` and output a concise Executive Summary report with a BUY / SELL / HOLD signal. Evaluate across 7 dimensions (trend, momentum, return, structure, volatility, volume, regime) and cross-reference with the most recent backtested strategy results from `data/reports/strategies/{ticker}/`. Output to `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md`

## Parameters

- `{ticker}` — Ticker symbol (e.g. `NG.L`, `BP.L`, `HSBA.L`)
- `{evaluation_date}` — Evaluation date (format: `YYYY-MM-DD`). Defaults to latest CSV date.
- `{strategy_name}` — (Optional) Specific strategy name to evaluate against (e.g. `MA_Crossover_Bullish`). If not specified, use the **recommended strategy** from the latest strategy file.
- Data source: `data/analysis-data/{ticker}.csv`
- Strategy reference: `data/reports/strategies/{ticker}/` — most recent `.md` file (must exist before running)
- Output: `data/reports/evaluation/{ticker}/{evaluation_date}_evaluation.md`.  where {evaluation_date} of the file name shuold be YYYYMMDD format such as 20261027_evaluation.md

## Data Loading

**Use the companion script** (one call, all data):

```bash
python app/analyse-market-data/get_evaluation_data.py {ticker} {evaluation_date} --latest-30
```

This outputs a single JSON with: `latest` row, all `indicators` (100+ TA columns), `52week` range, and `recent_context` (last 30 rows).

**Date resolution:** If the specified date does not exist (weekend/holiday), the script falls back to the latest available date on or before the specified date. Use `{actual_date}` = `date_range.end` as the effective evaluation date.

**Fallback:** If you need a column not in the companion output, read the raw CSV:
```bash
tail -30 data/analysis-data/{ticker}.csv
```

**Use `read` for:** Strategy reports and config files (text files, not CSVs).

## Pre-flight: Resolve Ticker Identity

1. Read `config/ticker_list.csv` and look up `{ticker}`
2. Record `Company` and `Sector` — these are the **authoritative** identifiers
3. **NEVER guess** what a ticker represents (e.g. `NG.L` = **National Grid**, not "Natural Gas"; `BP.L` = **BP**, not "Bond Pricing")

If the ticker is not found, proceed with the ticker symbol only — do not fabricate a company name.

## Prerequisites Check

Verify that the most recent strategy file exists in `data/reports/strategies/{ticker}/`.

- List all `.md` files, select the most recent one.
- If the directory is empty or does NOT exist, advise the user to run the investment strategy skill first and **exit** until the strategy report is available.
- Record the strategy file path for use in the report.
- **Resolve the strategy name:**
  - If `{strategy_name}` is **provided**: Read the strategy file and search for this exact strategy name. If it does **not** exist in the file, tell the user: `"Strategy '{strategy_name}' not found in the latest strategy report for {ticker}. Available strategies: {list available strategies}. Aborting."` and **stop**.
  - If `{strategy_name}` is **not provided** (empty or omitted): Extract the **recommended strategy** name from the latest strategy file (usually listed as the top-performing or recommended strategy). Use this as the target strategy.
- Record the resolved strategy name as `{target_strategy}` — use this throughout the report.

## Scoring Scale — -3.0 to +3.0

Each of the 7 dimensions is scored from **-3.0 (strong bearish)** to **+3.0 (strong bullish)**:

| Score | Signal |
|-------|--------|
| +2.0 to +3.0 | Strong Bullish |
| +0.5 to +1.9 | Mildly Bullish |
| -0.4 to +0.4 | Neutral |
| -1.9 to -0.5 | Mildly Bearish |
| -3.0 to -2.0 | Strong Bearish |

**Per-dimension confidence:** High (4+ indicators agree), Medium (2–3 agree or 1–2 null), Low (conflicting or >3 null).

## Evaluation Steps

### Step 1: Load Data & Resolve Strategy

Run the companion script and extract from the JSON:
- `{actual_date}` = `date_range.end`
- `{price}` = `latest.close`
- `{indicators}` = all TA column values
- `{recent_context}` = last 30 rows
- `{high_52w}`, `{low_52w}` = 52-week range

**Strategy resolution (add to Step 1):**
- If `{strategy_name}` was provided → search the strategy file for this exact name. Record `{target_strategy}` = the matching strategy.
- If `{strategy_name}` was **not provided** → extract the **recommended strategy** name from the file. Record `{target_strategy}` = recommended strategy name.
- Read the strategy file (using `read`) and extract the entry conditions and exit conditions **for `{target_strategy}` specifically**:

```
Target Strategy Data ({target_strategy}):
- Entry conditions:
  a) {condition 1 from {target_strategy}}
  b) {condition 2 from {target_strategy}}
  c) {condition 3 from {target_strategy}}
- Exit conditions:
  a) {exit condition 1 from {target_strategy}}
  b) {exit condition 2 from {target_strategy}}
  c) {exit condition 3 from {target_strategy}}
- Preferred regime: {bull/bear/neutral/all}
- Preferred volatility: {low/medium/high}
```

- **Use this Target Strategy Data throughout the report.** Do NOT re-read the strategy file. For each dimension, check whether the current state matches the conditions from `{target_strategy}`.

Handle missing data: skip null indicators; if >3 indicators in a dimension are null, mark that dimension's confidence as **Low**.

### Step 2: Evaluate Each Dimension (7 total)

Score each dimension from -3.0 to +3.0 using its key indicators:

| Dimension | Key Indicators |
|-----------|---------------|
| **Trend** | EMA20/50/200 alignment, SuperTrend direction, MA slopes, ADX, Donchian, Keltner, price/EMA20 ratio |
| **Momentum** | RSI(14), MACD (line/signal/histogram), ROC(20), Williams %R, CCI, TSI, MFI(14) |
| **Return** | Performance 1m/3m/6m/1y, Alpha(20), Beta(20), RS vs FTSE 100, forward returns (5d/10d/20d) |
| **Structure** | Swing highs/lows, HH/HL vs LH/LL, BOS, CHoCH, nearest support/resistance, trend label |
| **Volatility** | ATR(14), ATR percentile, BB width/position, HV(20), Parkinson vol, GARCH vol, ATR stop distance |
| **Volume** | OBV, CMF, VWAP, OFI, ADL, MFI(14), volume z-score/percentile, EMV(14) |
| **Regime** | HMM regime probabilities (state 0/1/2), regime label, GARCH vol trend, regime stability |

**Strategy Alignment per dimension:** Check if current conditions match the strategy's entry/regime/volatility requirements. Format: "Strategy Data → {condition}: Current {value} → Match ✅/❌"

### Step 3: Signal Synthesis

Aggregate all 7 dimension scores:

| Signal | Criteria |
|--------|----------|
| **STRONG BUY** | All 7 Bullish, regime is Bull |
| **BUY** | 5–6 Bullish, none strongly Bearish, regime not Bear |
| **HOLD** | Mixed (3–4 Bullish, 3–4 Bearish), or regime is Neutral |
| **WAIT** | High uncertainty — low volume, extreme volatility, regime shift imminent |
| **SELL** | 5–6 Bearish, none strongly Bullish, regime not Bull |
| **STRONG SELL** | All 7 Bearish, regime is Bear |

**Final signal must include:** Signal, score breakdown, key supporting/conflicting indicators, strategy alignment, confidence level, risk factors, and recommended action.

## Standardized Executive Summary Report Template

Write the report using this template:

```markdown
# Market Situation Evaluation: {company_name} ({Ticker})

**Evaluation Date:** {evaluation_date}
**Actual Date Used:** {actual_date}
**Ticker:** {Ticker} ({company_name})
**Price:** {close_price}
**Data Range:** {first_date} to {last_date} ({total_rows} rows)
**Sector:** {sector}
**Strategy Reference:** `data/reports/strategies/{ticker}/{latest_strategy_date}.md`
**Target Strategy:** `{target_strategy}`

---

## Executive Summary

**Signal:** STRONG BUY / BUY / HOLD / WAIT / SELL / STRONG SELL
**Confidence:** High / Medium / Low

### Dimension Overview

| Dimension | Signal | Confidence | Key Driver |
|-----------|--------|------------|------------|
| **Trend** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Momentum** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Return** | 🟢 POSITIVE / 🟡 MIXED / 🔴 NEGATIVE | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Structure** | 🟢 BULLISH / 🟡 CAUTIOUS / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Volatility** | 🟢 LOW / 🟡 NORMAL / 🔴 HIGH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Volume** | 🟢 BULLISH / 🟡 MIXED / 🔴 BEARISH | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Regime** | 🟢 BULL / 🟡 NEUTRAL / 🔴 BEAR | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |
| **Overall** | 🟢 STRONG BUY / 🟢 BUY / 🟡 HOLD / 🟠 WAIT / 🟠 SELL / 🔴 STRONG SELL | 🟢 High / 🟡 Medium / 🔴 Low | {1-line key driver} |

### Current Market Snapshot

| Metric | Value | Assessment |
|--------|-------|------------|
| Close | {price} | {context} |
| 52-Week Range | {low} – {high} | {position} |
| P/E (TTM) | {pe_ttm} | {comparison} |
| Dividend Yield | {yield}% | {assessment} |
| Beta (20d) | {beta} | {vs FTSE 100} |
| RS vs FTSE 100 | {rs} | {outperforming/underperforming} |

### Strategy Alignment Summary — `{target_strategy}`

#### Entry conditions (from `{target_strategy}`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| {Strategy entry condition 1 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy entry condition 2 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy entry condition 3 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Key strategy observation from `{target_strategy}`} | {context} | ✅ CONFIRMED / ⚠️ CAUTION / ❌ NOT MET |

**Strategy Entry Verdict:** {1–2 sentences on whether current conditions match `{target_strategy}` entry criteria}

#### Exit conditions (from `{target_strategy}`)
| Strategy Element | Current State | Alignment |
|-----------------|---------------|-----------|
| {Strategy exit condition 1 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy exit condition 2 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Strategy exit condition 3 — from `{target_strategy}`} | {current value} | ✅ MET / ❌ NOT MET |
| {Key strategy observation from `{target_strategy}`} | {context} | ✅ CONFIRMED / ⚠️ CAUTION / ❌ NOT MET |

**Strategy Exit Verdict:** {1–2 sentences on whether current conditions match `{target_strategy}` exit criteria}

### Signal Summary

**Current Signal: {SIGNAL} / {STRENGTH}**

{2–3 sentence narrative explaining the overall signal, who should act, and for whom}

---

### Aggregate Score

| # | Dimension | Signal | Score (-3.0 to +3.0) | Weight | Weighted |
|---|-----------|--------|-------------|--------|----------|
| 1 | **Trend** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 2 | **Momentum** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 3 | **Return** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 4 | **Structure** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 5 | **Volatility** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 6 | **Volume** | {Signal} | {+/−val} | {n}% | {+/−val} |
| 7 | **Regime** | {Signal} | {+/−val} | {n}% | {+/−val} |
| | **AGGREGATE** | | | **100%** | **+/−{total}** |

**Aggregate Score: {+/−val} — {SIGNAL}**

### Recommended Action

| Stakeholder | Action | Rationale |
|-------------|--------|-----------|
| **Non-holders** | {e.g., DO NOT ENTER} | {reason} |
| **Current holders** | {e.g., HOLD / REDUCE} | {reason} |
| **Traders** | {e.g., AVOID} | {reason} |

- **Entry:** {Specific conditions}
- **Stop-Loss:** {Level}
- **Target:** {Level}

### Risk Factors
- **{Risk 1}:** {description}
- **{Risk 2}:** {description}
- **{Risk 3}:** {description}

### When This Signal Is Invalidated
- **{Condition 1}:** → Signal becomes {NEW_SIGNAL}
- **{Condition 2}:** → Signal becomes {NEW_SIGNAL}
- **{Condition 3}:** → Signal becomes {NEW_SIGNAL}

---

*Report generated: {actual_date} | Data point: {evaluation_date} → `{actual_date}` | Data: `data/analysis-data/{ticker}.csv` ({total_rows} rows) | Strategy: `data/reports/strategies/{ticker}/{latest_strategy_date}.md` → Target: `{target_strategy}`*
```

## Constraints & Gotchas

- **Activate venv** before running any Python scripts
- **Never write inline Python** to read CSVs — use the companion script
- **TA column names** all use `ta_` prefix — verify names in the TA Column Quick Reference table in the full skill
- **NaN/null handling** — skip null indicators; mark confidence as Low if >3 null in a dimension
- **Ticker identity:** Always resolve from `config/ticker_list.csv`. Never guess company names.
- **Report file path:** Use YYYYMMDD format, e.g. `data/reports/evaluation/NG.L/20261231_evaluation.md`
- **MFI and GARCH appear in multiple dimensions** — score each dimension independently
- **Strategy report must exist** before running — exit with a helpful message if missing
- **Strategy name validation:** If `{strategy_name}` is provided, it **must** exist in the latest strategy file. If not, abort immediately with the list of available strategies. If not provided, auto-select the recommended strategy.
- **Always use `{target_strategy}`'s conditions** in the Strategy Alignment Summary — never mix conditions from different strategies
