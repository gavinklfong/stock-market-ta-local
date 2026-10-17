"""Run all unit tests for modules under app/.

Usage:
    python run_test.py            # all tests
    python run_test.py calculate-ta  # only TA module tests
    python run_test.py ticker-retriever  # only download script tests
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"

MODULE_DIRS = {
    "all": [str(APP_DIR / "calculate-ta" / "tests"), str(APP_DIR / "ticker-retriever" / "tests")],
    "calculate-ta": [str(APP_DIR / "calculate-ta" / "tests")],
    "ticker-retriever": [str(APP_DIR / "ticker-retriever" / "tests")],
}


def main():
    parser = argparse.ArgumentParser(description="Run unit tests for app/ modules")
    parser.add_argument(
        "module",
        nargs="?",
        default="all",
        choices=["all", "calculate-ta", "ticker-retriever"],
        help="Which module's tests to run (default: all)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_dirs = MODULE_DIRS[args.module]
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short"]
    if args.verbose:
        cmd.insert(-1, "-v")
    cmd.extend(test_dirs)

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
