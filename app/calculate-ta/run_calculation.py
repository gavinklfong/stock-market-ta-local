#!/usr/bin/env python
"""Orchestrator for all calculate_*.py TA modules.

Runs the full technical-analysis pipeline in the recommended dependency order:

    1. calculate_trend.py       – EMA, SuperTrend, MA, slopes, price/MA ratio
    2. calculate_momentum.py    – RSI, MACD, ROC
    3. calculate_volume.py      – OBV, CMF, VWAP, OFI, log volume
    4. calculate_volatility.py  – ATR, Bollinger Bands
    5. calculate_regime.py      – GARCH, HMM regime, log return
    6. calculate_structure.py   – Swing points, HH/HL/LH/LL, BOS, CHoCH, S/R
    7. calculate_return.py      – Forward 5d/10d/20d returns

All modules read from data/market-data/*.csv and write (merge-add) to
data/ta-data/*.csv.

Usage:
    python run_calculation.py                          # run all, in order
    python run_calculation.py trend momentum           # run specific modules
    python run_calculation.py --help                   # show usage
"""

import argparse
import subprocess
import sys
from pathlib import Path

MODULES = {
    "trend":       "calculate_trend.py",
    "momentum":    "calculate_momentum.py",
    "volume":      "calculate_volume.py",
    "volatility":  "calculate_volatility.py",
    "regime":      "calculate_regime.py",
    "structure":   "calculate_structure.py",
    "return":      "calculate_return.py",
}

ALL_ORDER = [
    "trend",
    "momentum",
    "volume",
    "volatility",
    "regime",
    "structure",
    "return",
]

DESCRIPTIONS = {
    "trend":       "trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio",
    "momentum":    "momentum indicators: RSI(14), MACD, ROC(20)",
    "volume":      "volume indicators: OBV, CMF(20), VWAP, OFI, log volume",
    "volatility":  "volatility indicators: ATR(14), Bollinger Bands(20,2)",
    "regime":      "regime detection: GARCH volatility + 3-state HMM, log return",
    "structure":   "structure indicators: HH/HL/LH/LL, BOS, CHoCH, Support/Resistance",
    "return":      "future returns: 5d/10d/20d",
}


def find_script_dir() -> Path:
    """Return the directory containing calculate_*.py scripts."""
    return Path(__file__).resolve().parent


def run_module(module_name: str, script_dir: Path, *, dry_run: bool = False) -> bool:
    """Run a single calculate_*.py module.

    Returns True on success, False on failure.
    """
    script = script_dir / MODULES[module_name]
    desc = DESCRIPTIONS[module_name]
    print(f"\n{'='*60}")
    print(f"  [{module_name.upper()}] {desc}")
    print(f"{'='*60}")

    if dry_run:
        print(f"  (dry-run) Would run: python {script}")
        return True

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script_dir),
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\n[ERROR] {module_name} failed with exit code {result.returncode}", file=sys.stderr)
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run all TA indicator modules in dependency order.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"\nAvailable modules:\n"
               + "\n".join(f"  {name:12s}  {DESCRIPTIONS[name]}" for name in ALL_ORDER),
    )
    parser.add_argument(
        "modules",
        nargs="*",
        choices=list(MODULES.keys()),
        help=(
            "Modules to run (default: all). "
            f"Available: {', '.join(MODULES.keys())}. "
            f"Order is always enforced as: {' → '.join(ALL_ORDER)}."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be run without executing.",
    )
    args = parser.parse_args()

    script_dir = find_script_dir()

    # Resolve requested modules → ordered list
    if args.modules:
        order = [m for m in ALL_ORDER if m in args.modules]
    else:
        order = list(ALL_ORDER)

    print(f"\nTA Pipeline Runner")
    print(f"{'='*60}")
    print(f"  Scripts directory : {script_dir}")
    print(f"  Modules to run    : {' → '.join(order)}")
    print(f"{'='*60}")

    failed = []
    for name in order:
        if not run_module(name, script_dir, dry_run=args.dry_run):
            failed.append(name)

    print(f"\n{'='*60}")
    print(f"  Pipeline {'complete' if not failed else 'FAILED'}")
    if failed:
        print(f"  Failed modules    : {', '.join(failed)}")
    else:
        print(f"  All modules passed.")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
