#!/usr/bin/env python
"""
Quick helper for skills that need ticker evaluation data.

Outputs a compact JSON with all indicator values the investment-strategy
and review-market-situation skills need — no inline Python hacking required.

Default output includes: `latest` (OHLCV row), `indicators` (90+ TA columns
across 8 categories), `52week` range, and optional `recent_context` (30 rows).

Usage:
    # Default: latest snapshot with indicators (investment-strategy skill primary)
    python app/analyse-market-data/get_evaluation_data.py NG.L
    python app/analyse-market-data/get_evaluation_data.py NG.L 2025-06-15         # specific date
    python app/analyse-market-data/get_evaluation_data.py NG.L --cutoff 2016-10-26 # backtest cutoff
    python app/analyse-market-data/get_evaluation_data.py NG.L --latest-30        # last 30 rows context
    python app/analyse-market-data/get_evaluation_data.py NG.L --latest-30 --category trend momentum  # only these categories

    # Full data for backtesting / parameter optimization
    python app/analyse-market-data/get_evaluation_data.py NG.L --full-df          # all columns as JSON rows
    python app/analyse-market-data/get_evaluation_data.py NG.L --ohlcv            # OHLCV rows for VectorBT
    python app/analyse-market-data/get_evaluation_data.py NG.L --cutoff 2016-10-26 --ohlcv

    # Analysis helpers
    python app/analyse-market-data/get_evaluation_data.py NG.L --forward-returns  # forward return statistics
    python app/analyse-market-data/get_evaluation_data.py NG.L --yearly           # year-by-year performance
    python app/analyse-market-data/get_evaluation_data.py NG.L --list-columns     # all columns by category
    python app/analyse-market-data/get_evaluation_data.py NG.L --category trend   # only trend indicators
    python app/analyse-market-data/get_evaluation_data.py NG.L --custom-strategies  # list available custom strategies
"""

import argparse
import json
import re
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
        "ta_supertrend", "ta_supertrend_upper", "ta_supertrend_lower",
        "ta_ma20_slope", "ta_ma50_slope", "ta_ma200_slope",
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
        "ta_stoch_k", "ta_stoch_d",
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
        "ta_swing_high", "ta_swing_low", "ta_swing_high_idx", "ta_swing_low_idx",
        "ta_hh", "ta_hl", "ta_lh", "ta_ll",
        "ta_bos", "ta_choch",
        "ta_nearest_resistance", "ta_nearest_support",
        "ta_dist_resistance", "ta_dist_support",
        "ta_breakout_strength", "ta_support_touches",
        "ta_trend",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            val = row[col]
            indicators[col] = float(val) if pd.notna(val) else val

    # Volatility
    for col in [
        "ta_atr14", "ta_normalized_atr14",
        "ta_bband_upper", "ta_bband_middle", "ta_bband_lower",
        "ta_bband_width", "ta_bband_pctb",
        "ta_hvol20", "ta_parkinson_vol",
        "ta_garch_vol", "ta_garch_sq",
        "ta_atr_stop_dist", "ta_atr_percentile", "ta_atr_position", "ta_rr_ratio",
    ]:
        if col in df.columns and pd.notna(row.get(col)):
            indicators[col] = float(row[col])

    # Volume
    for col in [
        "ta_obv", "ta_cmf", "ta_vwap", "ta_ofi", "ta_adl", "ta_mfi14",
        "ta_emv14", "ta_log_volume", "ta_volume_osc",
        "ta_volume_zscore", "ta_volume_percentile",
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
    """Get the last N rows for context (e.g., regime changes, trend direction).

    Includes regime columns plus key indicators used in multi-row computations:
    OBV, VWAP, CMF, ATR, Bollinger Bands, volume metrics.
    """
    context_cols = [
        # Regime
        "ta_regime_label", "ta_hmm_regime", "ta_hmm_regime_prob_0",
        "ta_hmm_regime_prob_1", "ta_hmm_regime_prob_2",
        # Volume (for OBV trend, CMF, VWAP)
        "ta_obv", "ta_cmf", "ta_vwap", "ta_adl",
        # Volatility (for ATR trend, BB position)
        "ta_atr14", "ta_atr_percentile",
        "ta_bband_upper", "ta_bband_middle", "ta_bband_lower", "ta_bband_pctb",
        # Volume intensity
        "ta_volume_zscore", "ta_volume_percentile",
    ]
    recent = df.tail(n_rows)
    records = []
    for _, row in recent.iterrows():
        record = {
            "date": str(row["Date"].date()),
            "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
        }
        for col in context_cols:
            if col in df.columns and pd.notna(row.get(col)):
                val = row[col]
                record[col] = float(val) if isinstance(val, (int, float)) else val
        records.append(record)
    return records


def get_yearly_performance(df: pd.DataFrame) -> list[dict]:
    """Get year-by-year buy-and-hold performance."""
    if "Date" not in df.columns or "Close" not in df.columns:
        return []
    df = df.copy()
    df["Year"] = df["Date"].dt.year
    yearly = []
    for year in sorted(df["Year"].unique()):
        year_data = df[df["Year"] == year]
        if len(year_data) < 2:
            continue
        start_close = year_data.iloc[0]["Close"]
        end_close = year_data.iloc[-1]["Close"]
        ret = (end_close - start_close) / start_close * 100 if start_close != 0 else None
        yearly.append({
            "year": int(year),
            "start_date": str(year_data.iloc[0]["Date"].date()),
            "end_date": str(year_data.iloc[-1]["Date"].date()),
            "start_close": float(start_close),
            "end_close": float(end_close),
            "return_pct": round(float(ret), 2) if ret is not None else None,
        })
    return yearly


def get_forward_returns_stats(df: pd.DataFrame) -> dict:
    """Get forward returns statistics (ta_return_5d, 10d, 20d)."""
    stats = {}
    for col in ["ta_return_5d", "ta_return_10d", "ta_return_20d"]:
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                stats[col] = {
                    "mean": round(float(vals.mean()), 4),
                    "median": round(float(vals.median()), 4),
                    "std": round(float(vals.std()), 4),
                    "min": round(float(vals.min()), 4),
                    "max": round(float(vals.max()), 4),
                    "pos_pct": round(float((vals > 0).mean() * 100), 1),
                }
    return stats


def get_ohlcv_rows(df: pd.DataFrame) -> list[dict]:
    """Get OHLCV data as list of dicts — useful for VectorBT portfolio creation."""
    records = []
    for _, row in df.iterrows():
        records.append({
            "date": str(row["Date"].date()),
            "open": float(row["Open"]) if pd.notna(row.get("Open")) else None,
            "high": float(row["High"]) if pd.notna(row.get("High")) else None,
            "low": float(row["Low"]) if pd.notna(row.get("Low")) else None,
            "close": float(row["Close"]) if pd.notna(row.get("Close")) else None,
            "volume": int(row["Volume"]) if pd.notna(row.get("Volume")) else None,
        })
    return records


def _matches_any(name, keywords):
    """Check if a column name contains any of the keywords."""
    return any(kw in name for kw in keywords)


def get_all_columns(ticker: str) -> dict:
    """Return all column names available for the ticker, grouped by category."""
    path = DATA_DIR / f"{ticker}.csv"
    if not path.exists():
        return {"error": f"{path} not found", "columns": []}

    df = pd.read_csv(path)
    all_cols = list(df.columns)

    keyword_groups = {
        "OHLCV": ["Date", "Open", "High", "Low", "Close", "Volume", "Adj Close"],
        "Trend": ["ema", "supertrend", "ma", "keltner", "donchian", "adx",
                  "aroon", "trend", "sma", "price_dist", "price_ma20_ratio"],
        "Momentum": ["rsi", "macd", "roc", "williams", "cci", "tsi",
                     "rsi_zscore", "rsi_percentile", "stoch", "mfi"],
        "Volume": ["obv", "cmf", "vwap", "ofi", "adl", "emv", "volume", "log_volume"],
        "Volatility": ["atr", "bband", "hvol", "park", "garch", "vol",
                       "normalized_atr", "atr_stop", "atr_percentile",
                       "atr_position", "rr_ratio"],
        "Regime": ["hmm", "regime"],
        "Structure": ["swing", "hh", "hl", "lh", "ll", "bos", "choch",
                      "resistance", "support", "dist_", "breakout", "touch"],
        "Returns": ["return_", "performance_", "alpha", "beta", "rs_ftse"],
        "Fundamentals": ["eps", "pe", "div"],
        "Time": ["weekday"],
    }

    categories = {}
    for category, keywords in keyword_groups.items():
        if category == "OHLCV":
            categories[category] = [c for c in all_cols if c in keywords]
        elif category == "Time":
            categories[category] = [c for c in all_cols if c in keywords]
        else:
            categories[category] = [
                c for c in all_cols if c.startswith("ta_") and _matches_any(c, keywords)
            ]

    return {"columns": all_cols, "categories": categories}


CATEGORY_COLUMNS = {
    "trend": [
        "ta_ema20", "ta_ema50", "ta_ema200", "ta_supertrend_direction",
        "ta_supertrend", "ta_supertrend_upper", "ta_supertrend_lower",
        "ta_ma20_slope", "ta_ma50_slope", "ta_ma200_slope",
        "ta_adx14", "ta_plus_di14", "ta_minus_di14",
        "ta_donchian_upper", "ta_donchian_lower",
        "ta_keltner_upper", "ta_keltner_lower",
        "ta_aroon_up", "ta_aroon_down",
        "ta_price_dist_ema20", "ta_price_dist_ema50", "ta_price_dist_ema200",
        "ta_price_ma20_ratio", "ta_trend",
    ],
    "momentum": [
        "ta_rsi14", "ta_macd_line", "ta_macd_signal", "ta_macd_histogram",
        "ta_roc20", "ta_williams_r", "ta_cci", "ta_tsi",
        "ta_rsi_zscore", "ta_rsi_percentile", "ta_mfi14",
        "ta_stoch_k", "ta_stoch_d",
    ],
    "return": [
        "ta_return_5d", "ta_return_10d", "ta_return_20d",
        "ta_performance_1m", "ta_performance_3m", "ta_performance_6m", "ta_performance_1y",
        "ta_alpha20", "ta_beta20", "ta_rs_ftse100",
    ],
    "structure": [
        "ta_swing_high", "ta_swing_low", "ta_swing_high_idx", "ta_swing_low_idx",
        "ta_hh", "ta_hl", "ta_lh", "ta_ll",
        "ta_bos", "ta_choch",
        "ta_nearest_resistance", "ta_nearest_support",
        "ta_dist_resistance", "ta_dist_support",
        "ta_breakout_strength", "ta_support_touches",
        "ta_trend",
    ],
    "volatility": [
        "ta_atr14", "ta_normalized_atr14",
        "ta_bband_upper", "ta_bband_middle", "ta_bband_lower",
        "ta_bband_width", "ta_bband_pctb",
        "ta_hvol20", "ta_parkinson_vol",
        "ta_garch_vol", "ta_garch_sq",
        "ta_atr_stop_dist", "ta_atr_percentile", "ta_atr_position", "ta_rr_ratio",
    ],
    "volume": [
        "ta_obv", "ta_cmf", "ta_vwap", "ta_ofi", "ta_adl", "ta_mfi14",
        "ta_emv14", "ta_log_volume", "ta_volume_osc",
        "ta_volume_zscore", "ta_volume_percentile",
        "ta_obv_slope_14", "ta_obv_slope_7",
    ],
    "regime": [
        "ta_hmm_regime", "ta_hmm_regime_prob_0", "ta_hmm_regime_prob_1",
        "ta_hmm_regime_prob_2", "ta_regime_label",
        "ta_garch_vol", "ta_garch_sq",
    ],
    "fundamentals": [
        "ta_eps_ttm", "ta_pe", "ta_div_ttm", "ta_div_yield",
    ],
}


def get_category_indicators(df: pd.DataFrame, categories: list[str] | None = None) -> dict:
    """Extract indicators from specified categories only.

    Args:
        df: DataFrame with TA data.
        categories: List of category names (e.g. ["trend", "momentum"]).
                    Defaults to all categories if None.

    Returns:
        Dict of indicator_name -> value for the latest row.
    """
    if categories is None:
        categories = list(CATEGORY_COLUMNS.keys())

    target_cols = set()
    for cat in categories:
        if cat in CATEGORY_COLUMNS:
            target_cols.update(CATEGORY_COLUMNS[cat])

    row = df.iloc[-1]
    indicators = {}
    for col in sorted(target_cols):
        if col in df.columns and pd.notna(row.get(col)):
            val = row[col]
            if isinstance(val, (int, float)):
                indicators[col] = float(val)
            elif isinstance(val, str):
                indicators[col] = val
            else:
                indicators[col] = val
    return indicators


def main():
    parser = argparse.ArgumentParser(description="Get evaluation data for a ticker.")
    parser.add_argument("ticker", help="Ticker symbol (e.g. NG.L)")
    parser.add_argument("date", nargs="?", default=None, help="Evaluation date (YYYY-MM-DD)")
    parser.add_argument("--cutoff", dest="cutoff_date", default=None,
                        help="Cutoff date (YYYY-MM-DD) — same as backtest --cutoff")
    parser.add_argument("--latest-30", action="store_true", help="Also include last 30 rows context")
    parser.add_argument("--columns", nargs="*", default=None, help="Subset of column prefixes to include")
    parser.add_argument("--full", action="store_true", help="Output full row (all columns)")
    parser.add_argument("--full-df", action="store_true", help="Output full DataFrame as JSON rows")
    parser.add_argument("--ohlcv", action="store_true", help="Output OHLCV rows for VectorBT")
    parser.add_argument("--forward-returns", action="store_true", help="Output forward returns statistics")
    parser.add_argument("--yearly", action="store_true", help="Output year-by-year buy-and-hold performance")
    parser.add_argument("--list-columns", action="store_true", help="List all available columns by category")
    parser.add_argument("--category", nargs="+", choices=list(CATEGORY_COLUMNS.keys()),
                        help="Only include indicators from these categories (e.g. trend momentum)")
    parser.add_argument("--custom-strategies", action="store_true",
                        help="List available custom strategies grouped by ticker")
    # No-op aliases for compatibility with other backtest scripts (AI models commonly add these)
    parser.add_argument("--json", action="store_true", help="Output as JSON (default — this flag is a no-op)")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation (no-op — no HTML generated here)")
    args = parser.parse_args()

    df = load_data(args.ticker, args.date)
    if args.cutoff_date:
        mask = df["Date"] <= pd.Timestamp(args.cutoff_date)
        if not mask.any():
            print(
                f"WARNING: No data on or before {args.cutoff_date}. Using all available data.",
                file=sys.stderr,
            )
        else:
            df = df.loc[mask]

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
    }

    # Explicit output modes (mutually exclusive with defaults)
    if args.list_columns:
        result["columns"] = get_all_columns(args.ticker)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.full_df:
        # Output full DataFrame as list of dicts
        result["data"] = []
        for _, row in df.iterrows():
            record = {"date": str(row["Date"].date())}
            for col in df.columns:
                if col == "Date":
                    continue
                val = row[col]
                if isinstance(val, (int, float)) and pd.notna(val):
                    record[col] = round(float(val), 6)
                elif isinstance(val, str):
                    record[col] = val
                else:
                    record[col] = val
        result["data"] = df.to_dict(orient="records")
        print(json.dumps(result, indent=2, default=str))
        return

    if args.ohlcv:
        result["ohlcv"] = get_ohlcv_rows(df)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.forward_returns:
        result["forward_returns"] = get_forward_returns_stats(df)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.yearly:
        result["yearly_performance"] = get_yearly_performance(df)
        print(json.dumps(result, indent=2, default=str))
        return

    if args.custom_strategies:
        # List all custom strategies across ticker-specific files
        custom_dir = BASE_DIR / "app" / "backtest" / "custom"
        strategies = _list_custom_strategies(custom_dir, args.ticker)
        # Also add relevant built-in strategies for context
        import importlib, sys
        _bt = str(BASE_DIR / "app" / "backtest")
        if _bt not in sys.path:
            sys.path.insert(0, _bt)
        importlib.invalidate_caches()
        from strategies.builtins import STRATEGIES, STRATEGY_LABELS
        result["custom_strategies"] = strategies
        result["built_in_strategies"] = {
            "count": len(STRATEGIES),
            "groups": list(STRATEGY_LABELS.keys()) if hasattr(STRATEGY_LABELS, "keys") else "see STRATEGY_GROUPS in builtins.py",
        }
        print(json.dumps(result, indent=2, default=str))
        return

    # Default: compact evaluation data
    result["latest"] = get_latest_row(df)
    if args.category:
        result["indicators"] = get_category_indicators(df, args.category)
    else:
        result["indicators"] = get_key_indicators(df)
    result["52week"] = get_52week_range(df)

    if args.latest_30:
        result["recent_context"] = get_recent_context(df, 30)

    print(json.dumps(result, indent=2, default=str))


def _list_custom_strategies(custom_dir: Path, ticker: str) -> dict:
    """List all custom strategies grouped by ticker, with their registered names.

    Scans per-ticker subdirectories under *custom_dir* recursively.

    Returns a dict mapping ticker -> list of strategy names found in that ticker's files.
    Only lists strategies relevant to the queried ticker plus a 'generic' group for
    ticker-agnostic strategies.
    """
    result: dict[str, list[str]] = {"generic": [], ticker: []}

    if not custom_dir.exists():
        return result

    ticker_base = ticker.split(".")[0]

    # Recursive glob: walk ticker subdirectories
    for pyfile in sorted(custom_dir.rglob("*.py")):
        if pyfile.name in ("__init__.py", "template_strategy.py"):
            continue

        fname = pyfile.stem  # e.g. "NG.L_custom" or "ba_defense_meanrev"

        # Determine which ticker this file belongs to
        ticker_lower = ticker.lower()
        ticker_base_lower = ticker_base.lower()
        fname_lower = fname.lower()

        file_ticker = "generic"
        if fname_lower.startswith(ticker_lower):
            file_ticker = ticker
        elif fname_lower.startswith(ticker_base_lower + "_"):
            file_ticker = ticker

        # Try to extract @register_custom names from the file
        content = pyfile.read_text()
        for match in re.finditer(r'@register_custom\("([^"]+)"\)', content):
            name = match.group(1)
            if file_ticker == ticker:
                result.setdefault(file_ticker, []).append(name)
            else:
                result.setdefault("generic", []).append(f"{name} (from {pyfile.name})")

    # Clean up: remove empty lists
    result = {k: v for k, v in result.items() if v}
    return result


if __name__ == "__main__":
    main()
