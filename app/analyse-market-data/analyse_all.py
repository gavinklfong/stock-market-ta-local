#!/usr/bin/env python
"""Generate an all-tickers overview report with period returns, sorted by 1Y return."""

import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis-data"
TICKER_LIST = BASE_DIR / "config" / "ticker_list.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "reports"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(val, d=2):
    if val is None:
        return "N/A"
    return f"{float(val):.{d}f}" if isinstance(val, (float, int)) else str(val)


def _price_icon(val):
    if val is None:
        return "\U0001f7e9"
    return "\u2705" if val > 0 else "\U0001f534" if val < 0 else "\U0001f7e9"


def _period_cell(val):
    """Format a period return cell with color and emoji."""
    if val is None:
        return '<td style="text-align:center">N/A</td>'
    icon = _price_icon(val)
    color = "#26a69a" if val > 0 else "#ef5350" if val < 0 else "#94a3b8"
    return f'<td style="text-align:center;color:{color};font-weight:bold">{icon} {val:+.2f}%</td>'


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_ticker_info():
    """Load ticker list and return dict mapping ticker -> company."""
    if not TICKER_LIST.exists():
        return {}
    df = pd.read_csv(TICKER_LIST)
    info = {}
    for _, row in df.iterrows():
        ticker = str(row["Ticker"]).strip()
        company = str(row["Company"]).strip()
        info[ticker] = company
    return info


def discover_tickers():
    """Discover ticker CSVs from analysis-data directory."""
    csv_files = sorted(ANALYSIS_DIR.glob("*.csv"))
    return [f.stem for f in csv_files]


def load_ticker_latest(name):
    """Load a ticker's analysis CSV and return the latest row."""
    path = ANALYSIS_DIR / f"{name}.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    latest = df.iloc[-1]
    return latest


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------


def generate_all_tickers_html(tickers_data, latest_date):
    """Generate HTML report for all tickers.

    Args:
        tickers_data: list of dicts with keys:
            ticker, company, close, period_1y, period_6m, period_1m
            already sorted by 1Y return descending
        latest_date: string date of latest data
    """
    # Build rows
    rows = ""
    for idx, t in enumerate(tickers_data):
        rows += f"""<tr>
            <td style="text-align:center">{idx + 1}</td>
            <td style="font-weight:bold">{t['company']} <span style="color:#999;font-size:0.85em">({t['ticker']})</span></td>
            <td style="text-align:center">{_fmt(t['close'])}</td>
            {_period_cell(t['period_1y'])}
            {_period_cell(t['period_6m'])}
            {_period_cell(t['period_1m'])}
        </tr>"""

    # Summary stats
    y_returns = [t["period_1y"] for t in tickers_data if t["period_1y"] is not None]
    if y_returns:
        avg_1y = sum(y_returns) / len(y_returns)
        best_1y = max(y_returns)
        worst_1y = min(y_returns)
        up_count = sum(1 for r in y_returns if r > 0)
        down_count = len(y_returns) - up_count
    else:
        avg_1y = best_1y = worst_1y = None
        up_count = down_count = 0

    avg_color = "#26a69a" if avg_1y and avg_1y > 0 else "#ef5350" if avg_1y and avg_1y < 0 else "#94a3b8"
    best_color = "#26a69a" if best_1y else "#94a3b8"
    worst_color = "#ef5350" if worst_1y else "#94a3b8"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>All Tickers Overview</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
h1 {{ text-align: center; color: #333; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
th {{ padding: 10px 12px; background: #2196f3; color: #fff; font-weight: 600; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
tr:last-child td {{ border-bottom: none; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
tr:hover {{ background: #e3f2fd; }}
.stat-cards {{ display: flex; gap: 12px; justify-content: center; margin: 16px 0; flex-wrap: wrap; }}
.stat-card {{ background: #fff; border-radius: 8px; padding: 16px; min-width: 180px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.stat-value {{ font-size: 1.6em; font-weight: bold; }}
.stat-label {{ color: #666; margin-top: 4px; font-size: 0.9em; }}
.subtitle {{ text-align: center; color: #888; margin-bottom: 20px; }}
.legend {{ text-align: center; margin: 16px 0; font-size: 0.85em; color: #666; }}
</style></head><body>
<h1>All Tickers Overview</h1>
<p class="subtitle">Sorted by 1-year return (descending) · Data as of {latest_date}</p>

<div class="stat-cards">
    <div class="stat-card">
        <div class="stat-value">{len(tickers_data)}</div>
        <div class="stat-label">Total Tickers</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:{avg_color}">{avg_icon(avg_1y)} {_fmt(avg_1y, 2) if avg_1y is not None else 'N/A'}%</div>
        <div class="stat-label">Avg 1Y Return</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:{best_color}">{_fmt(best_1y, 2) if best_1y is not None else 'N/A'}%</div>
        <div class="stat-label">Best 1Y</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:{worst_color}">{_fmt(worst_1y, 2) if worst_1y is not None else 'N/A'}%</div>
        <div class="stat-label">Worst 1Y</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:#26a69a">{up_count}</div>
        <div class="stat-label">Positive</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="color:#ef5350">{down_count}</div>
        <div class="stat-label">Negative</div>
    </div>
</div>

<p class="legend">
    <span style="color:#26a69a">&#9650;</span> Positive return &nbsp;&nbsp;
    <span style="color:#ef5350">&#9660;</span> Negative return
</p>

<table>
<thead>
<tr>
    <th style="text-align:center;width:50px">Rank</th>
    <th>Company</th>
    <th style="text-align:center">Close</th>
    <th style="text-align:center">1Y</th>
    <th style="text-align:center">6M</th>
    <th style="text-align:center">1M</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body></html>"""
    return html


def avg_icon(val):
    """Return emoji for average return."""
    if val is None:
        return "\U0001f7e9"
    return "\u2705" if val > 0 else "\U0001f534" if val < 0 else "\U0001f7e9"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Generate all-tickers overview report")
    parser.add_argument("--dry-run", action="store_true", help="Show analysis only, don't generate HTML")
    parser.add_argument("--output", default=None, help="Output directory for HTML report")
    args = parser.parse_args()

    # Load ticker info and discover available data
    ticker_info = _load_ticker_info()
    available = discover_tickers()
    if not available:
        print(f"No CSV files found in {ANALYSIS_DIR}")
        return

    print(f"Found {len(available)} tickers in {ANALYSIS_DIR}")

    # Collect period returns per ticker
    tickers_data = []
    for ticker in available:
        try:
            latest = load_ticker_latest(ticker)
            close = float(latest.get("Close", 0)) or float(latest.get("Adj Close", 0))
            period_1y = latest.get("ta_performance_1y")
            period_6m = latest.get("ta_performance_6m")
            period_1m = latest.get("ta_performance_1m")
            company = ticker_info.get(ticker, ticker)
            tickers_data.append({
                "ticker": ticker,
                "company": company,
                "close": close,
                "period_1y": float(period_1y) if period_1y is not None else None,
                "period_6m": float(period_6m) if period_6m is not None else None,
                "period_1m": float(period_1m) if period_1m is not None else None,
            })
            y_str = _fmt(period_1y, 2) if period_1y is not None else "N/A"
            print(f"  {ticker}: 1Y={y_str}%")
        except Exception as e:
            print(f"  {ticker}: Error - {e}")

    # Sort by 1Y return descending (None values go last)
    tickers_data.sort(key=lambda x: x["period_1y"] if x["period_1y"] is not None else -999, reverse=True)

    if args.dry_run:
        print("\nDry run complete. Analysis shown above.")
        return

    # Get latest date from first valid ticker
    latest_date = None
    for t in tickers_data:
        try:
            latest = load_ticker_latest(t["ticker"])
            latest_date = str(latest["Date"])[:10]
            break
        except Exception:
            continue
    latest_date = latest_date or "N/A"

    # Generate HTML report
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    html = generate_all_tickers_html(tickers_data, latest_date)
    output_path = output_dir / "all_tickers.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport written to {output_path}")


if __name__ == "__main__":
    main()
