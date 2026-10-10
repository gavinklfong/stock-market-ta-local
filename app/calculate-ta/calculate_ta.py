import math
import os
import pandas as pd

from common import main, row_progress_bar


def compute_ema(values, period):
    k = 2.0 / (period + 1)
    ema = float(values[0])
    for v in values[1:]:
        ema = float(v) * k + ema * (1 - k)
    return ema


def compute_rsi(values, period=14):
    if len(values) < period + 1:
        return None

    window = list(values[-(period + 1):])
    gains, losses = [], []

    for i in range(1, len(window)):
        diff = window[i] - window[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(values, fast=12, slow=26, signal=9):
    if len(values) < slow:
        return None, None, None

    k_fast = 2.0 / (fast + 1)
    k_slow = 2.0 / (slow + 1)

    ef = float(values[0])
    es = float(values[0])
    macd_all = [None] * len(values)

    for i, v in enumerate(values):
        vf = float(v)
        ef = vf * k_fast + ef * (1 - k_fast)
        es = vf * k_slow + es * (1 - k_slow)
        if i >= slow - 1:
            macd_all[i] = ef - es

    current_idx = len(values) - 1
    macd_line = macd_all[current_idx]

    if macd_all[current_idx] is None:
        return None, None, None

    recent_macd_start = current_idx - signal + 1
    if recent_macd_start < slow - 1:
        return macd_line, None, None

    recent_macd = [macd_all[i] for i in range(recent_macd_start, current_idx + 1)]

    if len(recent_macd) < signal:
        return macd_line, None, None

    signal_line = compute_ema(recent_macd, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def compute_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1:
        return [None] * len(highs)

    true_ranges = [None] * len(highs)
    for i in range(len(highs)):
        if i == 0:
            true_ranges[i] = highs[i] - lows[i]
        else:
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges[i] = tr

    atr_values = [None] * len(highs)
    first_atr_idx = None
    for i in range(period, len(true_ranges)):
        if true_ranges[i] is not None:
            first_atr_idx = i
            break

    if first_atr_idx is None:
        return atr_values

    initial_atr = sum(true_ranges[first_atr_idx:first_atr_idx + period]) / period
    atr_values[first_atr_idx] = initial_atr

    k = 2.0 / (period + 1)
    for i in range(first_atr_idx + 1, len(highs)):
        if true_ranges[i] is not None:
            prev_atr = atr_values[i - 1]
            if prev_atr is not None:
                atr_values[i] = true_ranges[i] * k + prev_atr * (1 - k)

    return atr_values


def compute_ofi(open_prices, highs, lows, closes):
    if len(open_prices) < 2:
        return [None] * len(open_prices)

    ofi_values = [None] * len(open_prices)
    for i in range(len(open_prices)):
        high_low_range = highs[i] - lows[i]
        if high_low_range == 0:
            ofi_values[i] = 0.0
        else:
            ofi_values[i] = (closes[i] - open_prices[i]) / high_low_range

    return ofi_values


def compute_ma(closes, period):
    """Compute Simple Moving Average (SMA) for each candle."""
    ma_values = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1: i + 1]
        ma_values[i] = sum(window) / period
    return ma_values


def compute_ma_slope(closes, period, lookback=10):
    """Compute slope of MA over `lookback` periods.
    
    slope = (MA_at_current - MA_at_current_lookback) / lookback
    """
    ma_values = compute_ma(closes, period)
    slope_values = [None] * len(closes)
    for i in range(period - 1 + lookback, len(closes)):
        if ma_values[i] is not None and ma_values[i - lookback] is not None:
            slope_values[i] = (ma_values[i] - ma_values[i - lookback]) / lookback
    return slope_values


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    df = pd.read_csv(input_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    file_total = len(df)

    closes = df["Close"].tolist()
    highs = df["High"].tolist()
    lows = df["Low"].tolist()
    opens = df["Open"].tolist()
    volumes = df["Volume"].tolist()

    ta_log_volume = [math.log(v) if v > 0 else None for v in volumes]

    ta_rsi14 = [None] * file_total
    ta_macd_line = [None] * file_total
    ta_macd_signal = [None] * file_total
    ta_macd_histogram = [None] * file_total
    ta_ema20 = [None] * file_total
    ta_log_return = [None] * file_total
    ta_atr14 = compute_atr(highs, lows, closes)
    ta_ofi = compute_ofi(opens, highs, lows, closes)

    ta_normalized_atr14 = [
        ta_atr14[i] / closes[i] if ta_atr14[i] is not None and closes[i] != 0 else None
        for i in range(file_total)
    ]

    ta_ma20 = compute_ma(closes, 20)
    ta_ma50 = compute_ma(closes, 50)
    ta_sma10 = compute_ma(closes, 10)
    ta_sma50 = compute_ma(closes, 50)
    ta_ma20_slope = compute_ma_slope(closes, 20, lookback=10)
    ta_ma50_slope = compute_ma_slope(closes, 50, lookback=10)
    ta_price_ma20_ratio = [None] * file_total
    for i in range(file_total):
        if ta_ma20[i] is not None and ta_ma20[i] != 0:
            ta_price_ma20_ratio[i] = closes[i] / ta_ma20[i]

    for i in range(file_total):
        if i > 0 and closes[i - 1] > 0 and closes[i] > 0:
            ta_log_return[i] = math.log(closes[i] / closes[i - 1])

        row_closes = closes[: i + 1]
        ta_rsi14[i] = compute_rsi(row_closes) if len(row_closes) >= 15 else None
        macd_line, macd_signal, macd_hist = compute_macd(row_closes)
        ta_macd_line[i] = macd_line
        ta_macd_signal[i] = macd_signal
        ta_macd_histogram[i] = macd_hist
        ta_ema20[i] = compute_ema(row_closes, 20) if len(row_closes) >= 20 else None

        if (i + 1) % max(1, file_total // 50) == 0 or i == file_total - 1:
            row_progress_bar(os.path.basename(input_path), file_total, i + 1)

    df["ta_rsi14"] = ta_rsi14
    df["ta_macd_line"] = ta_macd_line
    df["ta_macd_signal"] = ta_macd_signal
    df["ta_macd_histogram"] = ta_macd_histogram
    df["ta_ema20"] = ta_ema20
    df["ta_log_return"] = ta_log_return
    df["ta_atr14"] = ta_atr14
    df["ta_ofi"] = ta_ofi
    df["ta_ma20"] = ta_ma20
    df["ta_ma50"] = ta_ma50
    df["ta_sma10"] = ta_sma10
    df["ta_sma50"] = ta_sma50
    df["ta_ma20_slope"] = ta_ma20_slope
    df["ta_ma50_slope"] = ta_ma50_slope
    df["ta_price_ma20_ratio"] = ta_price_ma20_ratio
    df["ta_log_volume"] = ta_log_volume
    df["ta_normalized_atr14"] = ta_normalized_atr14

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_ta",
    description="core indicators: RSI, MACD, ATR, OFI, MAs, log return/vol, normalized ATR",
    process_csv_fn=process_csv,
)
