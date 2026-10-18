import os
import math
import pandas as pd

from common import main, read_yfinance_csv


def compute_ema(values, period):
    """Incremental EMA: returns a list where each element is the EMA up to that index."""
    k = 2.0 / (period + 1)
    result = [None] * len(values)
    if len(values) < period:
        return result
    # Seed with SMA of first `period` values
    ema = sum(float(v) for v in values[:period]) / period
    for i in range(period - 1, len(values)):
        result[i] = ema
        if i < len(values) - 1:
            ema = float(values[i + 1]) * k + ema * (1 - k)
    return result


def compute_atr(highs, lows, closes, period=14):
    """Compute Wilder's ATR. Returns list aligned with input."""
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
    # Seed ATR at index `period` using first `period` true ranges (indices 0..period-1)
    initial_atr = sum(true_ranges[i] for i in range(period)) / period
    atr_values[period] = initial_atr

    k = 2.0 / (period + 1)
    for i in range(period + 1, len(highs)):
        if true_ranges[i] is not None:
            prev_atr = atr_values[i - 1]
            if prev_atr is not None:
                atr_values[i] = true_ranges[i] * k + prev_atr * (1 - k)

    return atr_values


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


def compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0):
    """Compute SuperTrend indicator.
    
    Returns dict with:
      - supertrend: list of SuperTrend line values
      - direction: +1 for uptrend (price above ST), -1 for downtrend (price below ST)
      - upper_band: the upper band line (used when in downtrend)
      - lower_band: the lower band line (used when in uptrend)
    """
    atr = compute_atr(highs, lows, closes, atr_period)
    n = len(highs)
    
    # Mid point
    mid = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    
    # Raw bands
    upper_band_raw = [None] * n
    lower_band_raw = [None] * n
    for i in range(n):
        if atr[i] is not None:
            upper_band_raw[i] = mid[i] + multiplier * atr[i]
            lower_band_raw[i] = mid[i] - multiplier * atr[i]
    
    # Smooth bands: upper band only goes up, lower band only goes down
    upper_band = [None] * n
    lower_band = [None] * n
    
    for i in range(n):
        if upper_band_raw[i] is None or lower_band_raw[i] is None:
            continue
        if i == 0:
            upper_band[i] = upper_band_raw[i]
            lower_band[i] = lower_band_raw[i]
        else:
            # Upper band: only decrease if current raw < previous, else keep previous
            if upper_band[i - 1] is not None:
                upper_band[i] = min(upper_band_raw[i], upper_band[i - 1])
            else:
                upper_band[i] = upper_band_raw[i]
            # Lower band: only increase if current raw > previous, else keep previous
            if lower_band[i - 1] is not None:
                lower_band[i] = max(lower_band_raw[i], lower_band[i - 1])
            else:
                lower_band[i] = lower_band_raw[i]
    
    # Direction: +1 = uptrend, -1 = downtrend
    direction = [0] * n
    supertrend = [None] * n
    
    for i in range(n):
        if upper_band[i] is None or lower_band[i] is None:
            continue
        
        if i == 0:
            if closes[i] > lower_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            continue
        
        if direction[i - 1] == 1:
            # Was in uptrend: stay up if close > lower_band, flip to down if close < lower_band
            if closes[i] <= lower_band[i]:
                direction[i] = -1
                supertrend[i] = upper_band[i]
            else:
                direction[i] = 1
                supertrend[i] = lower_band[i]
        else:
            # Was in downtrend: stay down if close < upper_band, flip to up if close > upper_band
            if closes[i] >= upper_band[i]:
                direction[i] = 1
                supertrend[i] = lower_band[i]
            else:
                direction[i] = -1
                supertrend[i] = upper_band[i]
    
    return {
        "supertrend": supertrend,
        "direction": direction,
        "upper_band": upper_band,
        "lower_band": lower_band,
    }


def compute_aroon(highs, lows, period=25):
    """Compute Aroon Up and Aroon Down indicators.

    Aroon Up    = ((Period - Days Since Highest High) / Period) * 100
    Aroon Down  = ((Period - Days Since Lowest Low)  / Period) * 100

    Returns dict with:
      - aroon_up:    list of Aroon Up values (100 = strong uptrend)
      - aroon_down:  list of Aroon Down values (100 = strong downtrend)
    """
    n = len(highs)
    aroon_up = [None] * n
    aroon_down = [None] * n

    for i in range(n):
        # We need at least `period` data points for the first valid value
        if i < period - 1:
            continue
        # Look back over the window of `period` bars ending at i
        window_start = i - period + 1
        # Highest high in the window
        highest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if highs[j] > highs[highest_idx]:
                highest_idx = j
        # Lowest low in the window
        lowest_idx = window_start
        for j in range(window_start + 1, i + 1):
            if lows[j] < lows[lowest_idx]:
                lowest_idx = j

        days_since_high = i - highest_idx
        days_since_low = i - lowest_idx
        aroon_up[i] = ((period - days_since_high) / period) * 100
        aroon_down[i] = ((period - days_since_low) / period) * 100

    return {
        "aroon_up": aroon_up,
        "aroon_down": aroon_down,
    }


def compute_donchian(highs, lows, period=20):
    """Compute Donchian Upper and Lower channels.

    Donchian Upper = Highest High over the last `period` bars
    Donchian Lower = Lowest Low over the last `period` bars

    Returns dict with:
      - donchian_upper: list of upper channel values (resistance level)
      - donchian_lower: list of lower channel values (support level)

    First valid value at index ``period - 1`` (19 for period=20).
    """
    n = len(highs)
    donchian_upper = [None] * n
    donchian_lower = [None] * n

    for i in range(n):
        if i < period - 1:
            continue
        window_start = i - period + 1
        window_highs = highs[window_start: i + 1]
        window_lows = lows[window_start: i + 1]
        donchian_upper[i] = max(window_highs)
        donchian_lower[i] = min(window_lows)

    return {
        "donchian_upper": donchian_upper,
        "donchian_lower": donchian_lower,
    }


def compute_keltner(highs, lows, closes, ema_period=20, atr_period=10, multiplier=2.0):
    """Compute Keltner Upper and Lower channels.

    Keltner Channels use ATR-based bands around an EMA of the typical price.
      - Typical Price (TP) = (High + Low + Close) / 3
      - Middle Line = EMA(TP, ema_period)
      - Upper Band = Middle + (multiplier × ATR)
      - Lower Band = Middle - (multiplier × ATR)

    Returns dict with:
      - keltner_upper: list of upper channel values (resistance)
      - keltner_lower: list of lower channel values (support)

    First valid value at index ``max(ema_period - 1, atr_period)``.
      For default params: max(19, 10) = 19.
    """
    n = len(highs)
    keltner_upper = [None] * n
    keltner_lower = [None] * n

    # Compute Typical Price
    tp = [(float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0 for i in range(n)]

    # Compute EMA of Typical Price
    ema_tp = compute_ema(tp, ema_period)

    # Compute ATR (using existing compute_atr with atr_period)
    atr_values = compute_atr(highs, lows, closes, atr_period)

    for i in range(n):
        if ema_tp[i] is not None and atr_values[i] is not None:
            keltner_upper[i] = ema_tp[i] + multiplier * atr_values[i]
            keltner_lower[i] = ema_tp[i] - multiplier * atr_values[i]

    return {
        "keltner_upper": keltner_upper,
        "keltner_lower": keltner_lower,
    }


def compute_adx_di(highs, lows, closes, period=14):
    """Compute ADX, +DI, and -DI using Wilder's smoothing.

    Returns dict with:
      - adx:       list of ADX values (trend strength 0-100)
      - plus_di:   list of +DI values (bullish directional movement)
      - minus_di:  list of -DI values (bearish directional movement)

    Index validity (period=14):
      +DI/-DI : first valid at index ``period`` (14)
      DX      : first valid at index ``period + 1`` (15)
      ADX     : initial at index ``period + 14`` (28), then smoothed
    """
    n = len(highs)
    adx = [None] * n
    plus_di = [None] * n
    minus_di = [None] * n

    if n < period + 1:
        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    # --- Step 0: Directional movement ---
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    for i in range(1, n):
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    # --- Step 1: True Range ---
    true_range = [0.0] * n
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_range[i] = tr

    # --- Step 2: Wilder's smoothing (initial sum → recursive) ---
    k = 1.0 / period

    def _wilder_sum(values, start, end, period):
        """Initial sum of ``values[start:end]``, then recursive smoothing."""
        s = sum(values[i] for i in range(start, end))
        out = [0.0] * len(values)
        out[end - 1] = s
        for i in range(end, len(values)):
            out[i] = out[i - 1] - out[i - 1] * k + values[i]
        return out

    smoothed_tr = _wilder_sum(true_range, 1, period + 1, period)
    smoothed_plus_dm = _wilder_sum(plus_dm, 1, period + 1, period)
    smoothed_minus_dm = _wilder_sum(minus_dm, 1, period + 1, period)

    # --- Step 3: +DI / -DI (first valid at index ``period``) ---
    for i in range(period, n):
        st = smoothed_tr[i]
        if st == 0:
            continue
        plus_di[i] = (smoothed_plus_dm[i] / st) * 100
        minus_di[i] = (smoothed_minus_dm[i] / st) * 100

    # --- Step 4: DX (first valid at index ``period + 1``) ---
    # We store DX values in a separate dict so they are available for ADX
    # initialisation (which needs 14 consecutive DX values).
    dx_values = {}
    for i in range(period + 1, n):
        pdi = plus_di[i]
        mdi = minus_di[i]
        if pdi is None or mdi is None:
            continue
        di_sum = pdi + mdi
        if di_sum == 0:
            continue
        dx_values[i] = (abs(pdi - mdi) / di_sum) * 100

    # --- Step 5: ADX ---
    # Initial ADX = average of first 14 DX values.
    # Smoothed ADX[i] = ADX[i-1] * (1 - k) + DX[i] * k   (for i > first)
    init_dx_start = period + 1
    init_dx_end = period + 15  # 14 values: period+1 .. period+14
    init_idx = init_dx_end - 1  # index where initial ADX lands

    for i in range(period + 1, n):
        if i not in dx_values:
            continue
        dx = dx_values[i]

        if i == init_idx:
            # Average the first 14 DX values
            sum_dx = sum(dx_values[j] for j in range(init_dx_start, init_dx_end) if j in dx_values)
            count = sum(1 for j in range(init_dx_start, init_dx_end) if j in dx_values)
            if count > 0:
                adx[i] = sum_dx / count
        else:
            if adx[i - 1] is not None:
                adx[i] = adx[i - 1] * (1 - k) + dx * k

    return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}


def compute_trend_columns(highs, lows, closes, n):
    """Compute all trend indicator columns for a single ticker's data."""
    ta_ema20 = compute_ema(closes, 20) if n >= 20 else [None] * n
    ta_ema50 = compute_ema(closes, 50) if n >= 50 else [None] * n
    ta_ema200 = compute_ema(closes, 200) if n >= 200 else [None] * n
    st = compute_supertrend(highs, lows, closes, atr_period=14, multiplier=3.0)
    ta_ma20 = compute_ma(closes, 20)
    ta_ma50 = compute_ma(closes, 50)
    ta_sma10 = compute_ma(closes, 10)
    ta_ma20_slope = compute_ma_slope(closes, 20, lookback=10)
    ta_ma50_slope = compute_ma_slope(closes, 50, lookback=10)
    ta_price_ma20_ratio = [None] * n
    for i in range(n):
        if ta_ma20[i] is not None and ta_ma20[i] != 0:
            ta_price_ma20_ratio[i] = closes[i] / ta_ma20[i]

    aroon = compute_aroon(highs, lows, period=25)
    adx_di = compute_adx_di(highs, lows, closes, period=14)
    donchian = compute_donchian(highs, lows, period=20)
    keltner = compute_keltner(highs, lows, closes)

    return {
        "ta_ema20": ta_ema20,
        "ta_ema50": ta_ema50,
        "ta_ema200": ta_ema200,
        "ta_supertrend": st["supertrend"],
        "ta_supertrend_direction": st["direction"],
        "ta_supertrend_upper": st["upper_band"],
        "ta_supertrend_lower": st["lower_band"],
        "ta_ma20": ta_ma20,
        "ta_ma50": ta_ma50,
        "ta_sma10": ta_sma10,
        "ta_ma20_slope": ta_ma20_slope,
        "ta_ma50_slope": ta_ma50_slope,
        "ta_price_ma20_ratio": ta_price_ma20_ratio,
        "ta_aroon_up": aroon["aroon_up"],
        "ta_aroon_down": aroon["aroon_down"],
        "ta_adx14": adx_di["adx"],
        "ta_plus_di14": adx_di["plus_di"],
        "ta_minus_di14": adx_di["minus_di"],
        "ta_donchian_upper": donchian["donchian_upper"],
        "ta_donchian_lower": donchian["donchian_lower"],
        "ta_keltner_upper": keltner["keltner_upper"],
        "ta_keltner_lower": keltner["keltner_lower"],
    }


def process_csv(input_path, output_path, total_files, current_file, _lock=None):
    raw_df = read_yfinance_csv(input_path)
    raw_df["Date"] = pd.to_datetime(raw_df["Date"])
    raw_df = raw_df.sort_values("Date").reset_index(drop=True)
    file_total = len(raw_df)

    closes = raw_df["Close"].tolist()
    highs = raw_df["High"].tolist()
    lows = raw_df["Low"].tolist()

    # Compute this module's TA columns only
    trend_cols = compute_trend_columns(highs, lows, closes, file_total)

    # Build output: Date + own ta_ columns (no OHLCV, no other modules' columns)
    df = pd.DataFrame({"Date": raw_df["Date"]})
    for col, values in trend_cols.items():
        df[col] = values

    df = df.sort_values("Date").reset_index(drop=True)

    df.to_csv(output_path, index=False)
    return len(df)


main(
    module_name="calculate_trend",
    description="trend indicators: EMA20/50/200, SuperTrend, SMA10/20/50, MA slopes, price/MA ratio, Aroon, ADX/DI, Donchian, Keltner",
    process_csv_fn=process_csv,
)
