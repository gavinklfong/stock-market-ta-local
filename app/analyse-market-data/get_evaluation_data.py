#!/usr/bin/env python
"""
Quick helper for skills that need ticker evaluation data.

Outputs a compact JSON with all indicator values the review-market-situation
skill needs — no inline Python hacking required.

Usage:
    python app/analyse-market-data/get_evaluation_data.py NG.L                    # latest date
    python app/analyse-market-data/get_evaluation_data.py NG.L 2025-06-15         # specific date
    python app/analyse-market-data/get_evaluation_data.py NG.L --latest-30        # last 30 rows
    python app/analyse-market-data/get_evaluation_data.py NG.L --columns rsi ema  # subset columns
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "analysis-data"
CONFIG_DIR = BASE_DIR / "config"
TICKER_LIST = CONFIG_DIR / "ticker_list.csv"


def load_data(ticker: str, evaluation_date: str | None = None):
    """Load ticker CSV and return a DataFrame."""
    path = DATA_DIR / f"{ticker}.csv"
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path, parse_dates=["Date"])

    if evaluation_date:
        # Find the exact date or the latest date on or before it
        mask = df["Date"] <= pd.Timestamp(evaluation_date)
        if not mask.any():
            print(
                f"WARNING: No data on or before {evaluation_date}. Using latest date.",
                file=sys.stderr,
            )
            evaluation_date = None  # fall back to latest
        else:
            df = df.loc[mask]

    return df


def get_latest_row(df: pd.DataFrame) -> dict:
    """Extract the latest row as a flat dict."""
    row = df.iloc[-1]
    return {
        "date": str(row["Date"].date()),
        "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
        "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
        "high": float(row["High"]) if pd.notna(row["High"]) else None,
        "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
        "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
    }


def get_key_indicators(df: pd.DataFrame) -> dict:
    """Extract key indicator values from the latest row."""
    row = df.iloc[-1]
    indicators = {}

    # Trend
    for col in [
        "ta_ema20", "ta_ema50", "ta_ema200", "ta_supertrend_direction",
        "ta_supertrend", "ta_ma20_slope", "ta_ma50_slope", "ta_ma200_slope",
        "ta_adx14", "ta_plus_di14", "ta_minus_di14",
        "ta_donchian_upper", "ta_donchian_lower",
        "ta_keltner_upper", "ta_keltner_lower",
        "ta_aroon_up", "ta_aroon_down",
        "ta_price_dist_ema20", "ta_price_dist_ema50", "ta_price_dist_ema200",
        "ta_price_ma20_ratio", "ta_trend",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Momentum
    for col in [
        "ta_rsi14", "ta_macd_line", "ta_macd_signal", "ta_macd_histogram",
        "ta_roc20", "ta_williams_r", "ta_cci", "ta_tsi",
        "ta_rsi_zscore", "ta_rsi_percentile", "ta_mfi14",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Return
    for col in [
        "ta_return_5d", "ta_return_10d", "ta_return_20d",
        "ta_performance_1m", "ta_performance_3m", "ta_performance_6m", "ta_performance_1y",
        "ta_alpha20", "ta_beta20", "ta_rs_ftse100",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Structure
    for col in [
        "ta_swing_high", "ta_swing_low", "ta_hh", "ta_hl", "ta_lh", "ta_ll",
        "ta_bos", "ta_choch", "ta_nearest_resistance", "ta_nearest_support",
        "ta_dist_resistance", "ta_dist_support",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            val = row[col]
            indicators[col] = float(val) if pd.notna(val) else val

    # Volatility
    for col in [
        "ta_atr14", "ta_normalized_atr14", "ta_bband_upper", "ta_bband_middle",
        "ta_bband_lower", "ta_bband_width", "ta_bband_pctb",
        "ta_hvol20", "ta_parkinson_vol", "ta_garch_vol", "ta_garch_sq",
        "ta_atr_stop_dist", "ta_atr_percentile",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Volume
    for col in [
        "ta_obv", "ta_cmf", "ta_vwap", "ta_ofi", "ta_adl", "ta_mfi14",
        "ta_emv14", "ta_volume_zscore", "ta_volume_percentile",
        "ta_obv_slope_14", "ta_obv_slope_7",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Regime
    for col in [
        "ta_hmm_regime", "ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1",
        "ta_hmm_regime_prob_2", "ta_regime_label",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            val = row[col]
            indicators[col] = float(val) if isinstance(val, (int, float)) else val

    # Fundamentals
    for col in ["ta_eps_ttm", "ta_pe", "ta_div_ttm", "ta_div_yield"]:
        if col in df.columns:
            val = row.get(col)
            indicators[col] = float(val) if pd.notna(val) else None

    return indicators


def get_52week_range(df: pd.DataFrame) -> dict:
    """Get 52-week high/low."""
    if "High" in df.columns and "Low" in df.columns:
        year_start = df["Date"] >= (df["Date"].max() - pd.DateOffset(years=1))
        year_data = df.loc[year_start]
        return {
            "high_52w": float(year_data["High"].max()),
            "low_52w": float(year_data["Low"].min()),
        }
    return {"high_52w": None, "low_52w": None}


def get_ticker_metadata(ticker: str) -> dict:
    """Look up company name and sector from ticker_list.csv."""
    path = TICKER_LIST
    if not path.exists():
        return {"company_name": None, "sector": None, "metadata_source": None}

    df = pd.read_csv(path)
    # Handle ticker normalization: BRK.B → BRK-B (yfinance style)
    matching = df[df["Ticker"] == ticker]
    if matching.empty:
        # Try matching without suffix (e.g. "NG" matches "NG.L")
        partial = df[df["Ticker"].str.split(".").str[0] == ticker.replace(".L", "").replace(".X", "")]
        if not partial.empty:
            matching = partial.head(1)
        else:
            return {"company_name": None, "sector": None, "metadata_source": str(path)}

    row = matching.iloc[0]
    return {
        "company_name": str(row["Company"]),
        "sector": str(row["Major Industry / Sector"]),
        "metadata_source": str(path),
    }


def get_recent_context(df: pd.DataFrame, n_rows: int = 30) -> list[dict]:
    """Get the last N rows for context (e.g., regime changes)."""
    recent = df.tail(n_rows)
    records = []
    for _, row in recent.iterrows():
        record = {
            "date": str(row["Date"].date()),
            "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
        }
        regime_cols = [
            "ta_regime_label", "ta_hmm_regime", "ta_hmm_regime_prob_0",
            "ta_hmm_regime_prob_1", "ta_hmm_regime_prob_2",
        ]
        for col in regime_cols:
            if col in df.columns and pd.notna(row.get(col)):
                val = row[col]
                record[col] = float(val) if isinstance(val, (int, float)) else val
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description="Get evaluation data for a ticker.")
    parser.add_argument("ticker", help="Ticker symbol (e.g. NG.L)")
    parser.add_argument("date", nargs="?", default=None, help="Evaluation date (YYYY-MM-DD)")
    parser.add_argument("--latest-30", action="store_true", help="Also include last 30 rows context")
    parser.add_argument("--columns", nargs="*", default=None, help="Subset of column prefixes to include")
    parser.add_argument("--full", action="store_true", help="Output full row (all columns)")
    args = parser.parse_args()

    df = load_data(args.ticker, args.date)
    metadata = get_ticker_metadata(args.ticker)

    result = {
        "ticker": args.ticker,
        "company_name": metadata["company_name"],
        "sector": metadata["sector"],
        "data_path": str(DATA_DIR / f"{args.ticker}.csv"),
        "total_rows": len(df),
        "date_range": {
            "start": str(df["Date"].min().date()),
            "end": str(df["Date"].max().date()),
        },
        "latest": get_latest_row(df),
        "indicators": get_key_indicators(df),
        "52week": get_52week_range(df),
    }

    if args.latest_30:
        result["recent_context"] = get_recent_context(df, 30)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
