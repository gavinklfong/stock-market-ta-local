"""Shared configuration for all project tests."""

import os
import sys

# Allow tests to import directly from their sibling source directories:
#   `from calculate_trend import ...`
#   `import download_tickers`
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_project_root, "app", "calculate-ta"))
sys.path.insert(0, os.path.join(_project_root, "app", "ticker-retriever"))
