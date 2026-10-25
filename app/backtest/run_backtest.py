"""CLI entry point — run backtests for a single ticker with YAML config."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Ensure the backtest package is importable
BACKTEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKTEST_DIR))

from framework.engine import BacktestEngine, DEFAULT_CUTOFF
from framework.extensions import load_custom_strategies, validate_custom_strategies
from framework.metrics import summarize_table
from framework.report import generate_report
from strategies.builtins import STRATEGIES, STRATEGY_LABELS


def load_config(config_path: str | Path) -> dict:
    """Load YAML config (requires PyYAML; falls back to minimal parser if absent)."""
    try:
        import yaml
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except ImportError:
        return _parse_minimal_config(config_path)


def _parse_minimal_config(config_path: str | Path) -> dict:
    """Minimal YAML-like parser for simple config files (no PyYAML dependency)."""
    config = {"strategies": [], "custom_dir": None, "trailing_pct": None}
    strategies = []
    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("custom_dir:"):
                config["custom_dir"] = line.split(":", 1)[1].strip().strip('"\'')
            elif line.startswith("trailing_pct:"):
                config["trailing_pct"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("module:") or line.startswith("type:"):
                name = line.split(":", 1)[1].strip().strip('"\'')
                strategies.append({"module": name})
            elif line.startswith("custom_indicators:"):
                # Inline indicator list — skip (logged as warning later)
                pass
    config["strategies"] = strategies
    return config


def resolve_strategies(
    strategy_specs: list[dict],
    custom_dir: str | Path | None = None,
) -> tuple[dict[str, object], dict[str, str]]:
    """Resolve strategy names to callables + labels."""
    strategies: dict[str, object] = {}
    labels: dict[str, str] = {}

    for spec in strategy_specs:
        name = spec.get("module") or spec.get("type") or ""
        if not name:
            continue

        # Check custom registry first
        if name in _custom_cache:
            strategies[name] = _custom_cache[name]
            labels[name] = spec.get("label", name)
            continue

        # Check builtins
        if name in STRATEGIES:
            strategies[name] = STRATEGIES[name]
            labels[name] = spec.get("label", STRATEGY_LABELS.get(name, name))
            continue

        # Try loading custom strategies
        if custom_dir:
            _load_custom(custom_dir)
            if name in _custom_cache:
                strategies[name] = _custom_cache[name]
                labels[name] = spec.get("label", name)
                continue

        print(f"WARNING: Strategy '{name}' not found — skipping")

    return strategies, labels


# Module-level cache for custom strategies
_custom_cache: dict[str, object] = {}


def _load_custom(custom_dir: str | Path) -> None:
    """Load custom strategies once and cache them."""
    if not custom_dir or custom_dir in _custom_cache:
        return
    loaded = load_custom_strategies(custom_dir)
    _custom_cache.update(loaded)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run backtests for a ticker using the reusable framework.",
    )
    parser.add_argument("ticker", help="Ticker symbol (e.g. NG.L, HSBA.L)")
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Path to YAML config (default: configs/default.yaml)",
    )
    parser.add_argument(
        "-d", "--data-dir",
        default=None,
        help="Path to analysis-data directory (default: data/analysis-data)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory for reports (default: data/reports/backtest)",
    )
    parser.add_argument(
        "--cutoff",
        default=None,
        help="Cutoff date YYYY-MM-DD (default: ~10 years from now)",
    )
    parser.add_argument(
        "--trailing-pct",
        type=float,
        default=None,
        help="Trailing stop percentage (overrides config)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip HTML report generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show strategy list and data summary only",
    )
    parser.add_argument(
        "--custom-dir",
        default=None,
        help="Directory for custom strategy Python files",
    )

    args = parser.parse_args()

    # Resolve paths
    root = Path(__file__).resolve().parent.parent.parent  # stock-market-ta-local
    if args.data_dir is None:
        data_dir = root / "data" / "analysis-data"
    else:
        data_dir = Path(args.data_dir)
    if args.output_dir is None:
        output_dir = root / "data" / "reports" / "backtest"
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data_path = data_dir / f"{args.ticker}.csv"
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows for {args.ticker} from {data_path.name}")

    # Parse cutoff date
    cutoff = None
    if args.cutoff:
        cutoff = pd.Timestamp(args.cutoff)

    # Load config
    config_path = args.config
    if config_path is None:
        default_config = BACKTEST_DIR / "configs" / "default.yaml"
        if default_config.exists():
            config_path = default_config

    strategy_specs = []
    custom_dir = args.custom_dir
    if config_path and Path(config_path).exists():
        config = load_config(config_path)
        strategy_specs = config.get("strategies", [])
        if not custom_dir and config.get("custom_dir"):
            custom_dir = Path(config_path).parent / config["custom_dir"]
    else:
        strategy_specs = [{"module": name} for name in STRATEGIES]

    # Resolve strategies
    strategies, labels = resolve_strategies(strategy_specs, custom_dir)
    if not strategies:
        print("ERROR: No strategies loaded — check config and strategy names")
        sys.exit(1)

    print(f"Loaded {len(strategies)} strategies: {list(strategies.keys())}")

    # Dry run: show data summary and exit
    if args.dry_run:
        print(f"\nData summary:")
        print(f"  Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        print(f"\nStrategies to run:")
        for name in strategies:
            print(f"  - {labels.get(name, name)}")
        return

    # Run backtests
    engine = BacktestEngine(
        data_path=str(data_path),
        cutoff_date=cutoff,
        trailing_pct=args.trailing_pct,
    )
    results = engine.run_batch(strategies)

    # Print summary
    summary = pd.DataFrame(results).sort_values("Total Return (%)", ascending=False)
    summary.set_index("Strategy", inplace=True)
    print(f"\n{'='*70}")
    print(f"  Backtest Results — {args.ticker}  ({len(results)} strategies)")
    print(f"{'='*70}")
    for i, row in summary.iterrows():
        label = labels.get(i, i)
        print(f"\n  {label}")
        print(f"  {'─'*40}")
        for col in ["Total Return (%)", "Sharpe Ratio", "Max Drawdown (%)",
                     "Total Trades", "Win Rate (%)", "Profit Factor"]:
            if col in row:
                print(f"    {col:20s}: {row[col]:.2f}")

    # Generate report
    if not args.no_report:
        report_path = generate_report(
            results=results,
            df=df,
            ticker=args.ticker,
            output_dir=output_dir,
            top_n=15,
        )
        print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
