#!/usr/bin/env python
"""Analyse sector data and generate HTML reports per sector."""

import argparse
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis-data"
TICKER_LIST = BASE_DIR / "config" / "ticker_list.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "reports" / "sector-overview"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt(val, d=2):
    if val is None:
        return "N/A"
    return f"{float(val):.{d}f}" if isinstance(val, (float, int)) else str(val)


def _price_change_pct(df, close_col="Close", periods=None):
    """Calculate close price change % over the given periods from the last date.

    Returns dict like {"1Y": 12.3, "6M": -3.4, ...} or None for any missing window.
    """
    if periods is None:
        periods = {"1Y": pd.DateOffset(years=1), "6M": pd.DateOffset(months=6),
                    "3M": pd.DateOffset(months=3), "1M": pd.DateOffset(months=1)}
    latest = df[close_col].iloc[-1]
    results = {}
    for label, offset in periods.items():
        cutoff = df["Date"].max() - offset
        subset = df[df["Date"] < cutoff]
        if len(subset) == 0:
            results[label] = None
            continue
        base = subset[close_col].iloc[-1]
        if pd.isna(base) or base == 0:
            results[label] = None
        else:
            results[label] = (latest - base) / base * 100
    return results


def _emoji(ok):
    """Return emoji: green=good, red=bad, yellow=unknown."""
    if ok is None:
        return "\U0001f7e9"
    return "\u2705" if ok else "\U0001f534"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _load_ticker_info():
    """Load ticker list and return dict mapping ticker -> (company, sector)."""
    if not TICKER_LIST.exists():
        return {}
    df = pd.read_csv(TICKER_LIST)
    info = {}
    for _, row in df.iterrows():
        ticker = str(row["Ticker"]).strip()
        company = str(row["Company"]).strip()
        sector = str(row["Major Industry / Sector"]).strip()
        info[ticker] = (company, sector)
    return info


def discover_tickers():
    """Discover ticker CSVs from analysis-data directory."""
    csv_files = sorted(ANALYSIS_DIR.glob("*.csv"))
    return [f.stem for f in csv_files]


def load_ticker(name):
    """Load a ticker's analysis CSV."""
    path = ANALYSIS_DIR / f"{name}.csv"
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ---------------------------------------------------------------------------
# Sector grouping
# ---------------------------------------------------------------------------


def group_by_sector(ticker_info, available_tickers):
    """Group available tickers by sector, excluding Index sector.

    Returns dict: sector -> [(ticker, company), ...]
    """
    sectors = {}
    for ticker in available_tickers:
        if ticker in ticker_info:
            company, sector = ticker_info[ticker]
            # Skip index tickers
            if sector == "Index":
                continue
            sectors.setdefault(sector, []).append((ticker, company))
    # Sort each sector's tickers alphabetically
    for sector in sectors:
        sectors[sector].sort(key=lambda x: x[0])
    return sectors


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------


def _period_cell(val):
    """Format a period return cell with color and emoji."""
    if val is None:
        return '<td style="color:#999;text-align:center">N/A</td>'
    icon = "\u2705" if val > 0 else "\U0001f534" if val < 0 else "\U0001f7e9"
    color = "#26a69a" if val > 0 else "#ef5350" if val < 0 else "#999"
    return f'<td style="text-align:center;color:{color};font-weight:bold">{icon} {val:+.2f}%</td>'


def generate_sector_html(sector_name, tickers_data, rank=1):
    """Generate HTML for a single sector report.

    Args:
        sector_name: Sector name (e.g. "Utilities")
        tickers_data: list of (ticker, company, close, latest_date, periods)
            sorted by 1Y return descending
        rank: 1-based rank for the sector (for display purposes)
    """
    # Build rows
    rows = ""
    for idx, (ticker, company, close, latest_date, periods) in enumerate(tickers_data):
        rank_num = idx + 1
        rows += f"""<tr>
            <td style="text-align:center;font-weight:bold">{rank_num}</td>
            <td style="font-weight:bold">{company} <span style="color:#999;font-size:0.85em">({ticker})</span></td>
            <td style="text-align:center">{_fmt(close)}</td>
            {_period_cell(periods.get("1Y"))}
            {_period_cell(periods.get("6M"))}
            {_period_cell(periods.get("3M"))}
            {_period_cell(periods.get("1M"))}
        </tr>"""

    # Determine overall sector sentiment
    y_returns = [p.get("1Y") for _, _, _, _, p in tickers_data if p.get("1Y") is not None]
    if y_returns:
        avg_1y = sum(y_returns) / len(y_returns)
        avg_icon = "\u2705" if avg_1y > 0 else "\U0001f534"
        avg_color = "#26a69a" if avg_1y > 0 else "#ef5350"
    else:
        avg_1y = None
        avg_icon = "\U0001f7e9"
        avg_color = "#999"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sector Analysis: {sector_name}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
h1 {{ text-align: center; color: #333; }}
h2 {{ color: #555; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
th {{ padding: 10px 12px; background: #2196f3; color: #fff; font-weight: 600; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
tr:last-child td {{ border-bottom: none; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
tr:hover {{ background: #e3f2fd; }}
.stat-card {{ background: #fff; border-radius: 8px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
.stat-value {{ font-size: 1.8em; font-weight: bold; }}
.stat-label {{ color: #666; margin-top: 4px; }}
.subtitle {{ text-align: center; color: #888; margin-bottom: 20px; }}
</style></head><body>
<h1>Sector Analysis: {sector_name}</h1>
<p class="subtitle">Tickers sorted by 1-year return (descending)</p>

<div style="display:flex;gap:12px;justify-content:center;margin:16px 0">
    <div class="stat-card" style="flex:1;max-width:200px">
        <div class="stat-value">{len(tickers_data)}</div>
        <div class="stat-label">Tickers</div>
    </div>
    <div class="stat-card" style="flex:1;max-width:200px">
        <div class="stat-value" style="color:{avg_color}">{avg_icon} {_fmt(avg_1y, 2) if avg_1y is not None else 'N/A'}%</div>
        <div class="stat-label">Avg 1Y Return</div>
    </div>
</div>

<table>
<thead>
<tr>
    <th style="text-align:center;width:60px">Rank</th>
    <th>Company</th>
    <th style="text-align:center">Close</th>
    <th style="text-align:center">1Y</th>
    <th style="text-align:center">6M</th>
    <th style="text-align:center">3M</th>
    <th style="text-align:center">1M</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body></html>"""
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def analyse_sector(sector_name, ticker_info, available_tickers):
    """Analyse a single sector and return sorted ticker data.

    Args:
        sector_name: Name of the sector to analyse.
        ticker_info: Dict mapping ticker -> (company, sector).
        available_tickers: Set of ticker names with available data.

    Returns:
        List of (ticker, company, close, latest_date, periods) sorted by 1Y return desc,
        or None if the sector is not found or has no available tickers.
    """
    # Filter available tickers to this sector (excluding Index)
    sector_tickers = []
    for ticker in available_tickers:
        if ticker in ticker_info:
            company, sector = ticker_info[ticker]
            if sector == sector_name and sector != "Index":
                sector_tickers.append((ticker, company))
    sector_tickers.sort(key=lambda x: x[0])

    if not sector_tickers:
        return None

    # Collect period returns
    tickers_data = []
    for ticker, company in sector_tickers:
        try:
            df = load_ticker(ticker)
            periods = _price_change_pct(df)
            close = float(df["Close"].iloc[-1])
            latest_date = str(df["Date"].iloc[-1])[:10]
            tickers_data.append((ticker, company, close, latest_date, periods))
            print(f"  {ticker}: 1Y={periods.get('1Y')}")
        except Exception as e:
            print(f"  {ticker}: Error - {e}")

    # Sort by 1Y return descending (None values go last)
    tickers_data.sort(key=lambda x: x[4].get("1Y") if x[4].get("1Y") is not None else -999, reverse=True)
    return tickers_data


def generate_sector_report(sector_name, tickers_data, output_dir):
    """Generate HTML report for a single sector and write to file.

    Args:
        sector_name: Sector name (e.g. "Utilities").
        tickers_data: List of (ticker, company, close, latest_date, periods).
        output_dir: Path to output directory.

    Returns:
        Path to the generated HTML file.
    """
    html = generate_sector_html(sector_name, tickers_data)
    filename = f"sector_analysis_{sector_name.replace(' ', '_')}.html"
    output_path = Path(output_dir) / filename
    output_path.write_text(html, encoding="utf-8")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Analyse a single sector and generate HTML report")
    parser.add_argument("sector", help="Sector name to analyse (e.g. Utilities)")
    parser.add_argument("--dry-run", action="store_true", help="Show analysis only, don't generate HTML")
    parser.add_argument("--output", default=None, help="Output directory for HTML report")
    args = parser.parse_args()

    # Load ticker info and discover available data
    ticker_info = _load_ticker_info()
    available = discover_tickers()
    if not available:
        print(f"No CSV files found in {ANALYSIS_DIR}")
        return

    # Analyse the requested sector
    tickers_data = analyse_sector(args.sector, ticker_info, available)
    if tickers_data is None:
        print(f"Sector '{args.sector}' not found or has no available tickers")
        return

    print(f"Sector: {args.sector} ({len(tickers_data)} tickers)")

    if args.dry_run:
        print("\nDry run complete. Analysis shown above.")
        return

    # Generate HTML report
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = generate_sector_report(args.sector, tickers_data, output_dir)
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
