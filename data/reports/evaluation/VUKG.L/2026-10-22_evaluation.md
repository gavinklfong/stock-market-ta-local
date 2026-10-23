# Market Situation Evaluation: VUKG.L

**Date:** 2026-10-22
**Ticker:** VUKG.L (Vanguard FTSE 100 UCITS ETF)
**Price:** 57.82
**Data Range:** 2019-05-14 to 2026-10-22 (1,881 rows)
**Strategy Reference:** `data/strategy/VUKG.L/20261021.md`

---

## Executive Summary

**Signal:** HOLD
**Confidence:** Medium

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Trend | 4 | Bullish |
| Momentum | 3 | Neutral |
| Return | 4 | Bullish |
| Structure | 2 | Bearish-leaning |
| Volatility | 3 | Normal |
| Volume | 3 | Neutral |
| Regime | 3 | Sideways |

**Summary:** VUKG.L is in a structurally bullish long-term trend with EMA alignment and SuperTrend support, but momentum is weakening and the HMM regime has been in a neutral/sideways state for 60+ days. The ETF is trading near its 20-day Bollinger Band upper (67.5% %B), suggesting limited short-term upside. The recommended strategy from the backtest (Score 3+ entry / RSI > 75 exit) has no active signals — RSI is at 56, far from the 75 exit threshold, and the entry score conditions are only partially met. This is a HOLD with a bias toward buying on dips, but caution on chasing above current levels.

---

## 1. Trend Analysis

### Current Indicators
| Indicator | Value | Signal |
|-----------|-------|--------|
| EMA20 | 57.59 | |
| EMA50 | 57.47 | |
| EMA200 | 55.52 | |
| SuperTrend Direction | 1 | Bullish |
| MA20 Slope | 0.0087 | Bullish |
| MA50 Slope | -0.0074 | Bearish |
| ADX | 16.01 | Weak trend |
| DI+ / DI- | (near-equal) | No clear bias |
| Price vs EMA20 | +0.39% | Slightly above |

### Trend Assessment
- **Alignment:** EMA20 (57.59) > EMA50 (57.47) > EMA200 (55.52) — classic bullish alignment. All three EMAs are ordered correctly and price is above all three.
- **SuperTrend:** Currently +1 (bullish), stable for 10+ consecutive days (last flip confirmed). The SuperTrend lower band at 57.18 acts as near-term support.
- **Momentum of MAs:** Mixed — MA20 slope is positive (+0.0087, short-term uptrend) but MA50 slope is negative (-0.0074, medium-term declining). This suggests the recent rally is a correction within a broader sideways-to-downtrend context.
- **Trend Strength:** ADX at 16.01 is well below 20, indicating a weak trend. DI+ and DI- are near-equal, confirming no strong directional conviction.
- **Donchian Position:** Price (57.82) is near the Donchian upper (58.73) and Keltner upper (58.81), suggesting the price is at the top of its recent range — potential resistance zone.

### Strategy Alignment
The strategy report recommends "Score 3+" entry (≥3 of 6: EMA20>50, RSI>50, MACD bullish, CMF>0, OFI>0, ADX>20). Current conditions:
- EMA20>50: ✓ Yes (57.59 > 57.47)
- RSI>50: ✓ Yes (56.3)
- MACD bullish: ✓ Yes (MACD line > signal)
- CMF>0: ✗ No (-0.114, selling pressure)
- OFI>0: ✓ Yes (0.069, order flow favoring buyers)
- ADX>20: ✗ No (16.0, weak trend)

**Score: 3/6** — This hits the minimum entry threshold of 3, but the borderline nature (MA50 slope negative, low ADX, negative CMF) means it is a weak entry signal. The recommended RSI > 75 exit is not triggered (RSI at 56).

---

## 2. Momentum Analysis

### Current Indicators
| Indicator | Value | Signal |
|-----------|-------|--------|
| RSI(14) | 56.29 | Neutral |
| MACD Line | 0.34 | |
| MACD Signal | 0.22 | |
| MACD Histogram | 0.12 | Declining |
| ROC(20) | 1.18% | Mildly positive |
| Williams %R | -29.20 | Overbought zone |
| CCI | 119.82 | Overbought (>100) |
| MFI(14) | 135.56 | Extremely overbought |

### Momentum Assessment
- **RSI Context:** RSI at 56.3 is in neutral territory (50–70). The RSI z-score (1.33) and percentile (84.7%) indicate RSI is well above its 20-day average — the short-term RSI has been elevated relative to recent history.
- **MACD State:** MACD line (0.34) is above signal (0.22), which is technically bullish. However, the MACD histogram has been declining for 5 consecutive days (0.22 → 0.20 → 0.17 → 0.15 → 0.12), signaling momentum is fading. A bearish cross is possible if the decline continues.
- **Momentum Strength:** Williams %R at -29.2 and CCI at 119.8 both indicate overbought conditions. MFI at 135.6 is extremely elevated (normal range is 20–80), suggesting heavy buying pressure that may be exhausted.
- **Divergence Check:** Price is near recent highs while MACD histogram is declining — this is a mild bearish divergence warning. If price continues higher but MACD histogram keeps falling, a reversal could be imminent.

### Strategy Alignment
The strategy uses RSI > 75 as the primary exit and various RSI thresholds for entry scoring. Current RSI at 56 is well below both entry preference (RSI > 50 for Score, RSI > 40 for SuperTrend+EMA) and the exit threshold (RSI > 75). The elevated RSI percentile (84.7%) suggests momentum is relatively high, but not extreme enough for the strategy's exit trigger.

---

## 3. Return Analysis

### Performance Metrics
| Period | Return | Assessment |
|--------|--------|------------|
| 1 Month | See CSV | — |
| 3 Months | See CSV | — |
| 6 Months | See CSV | — |
| 1 Year | See CSV | — |

### Risk-Adjusted Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| Alpha(20) | See CSV | Positive = outperforming |
| Beta(20) | See CSV | >1 = more volatile |
| RS vs FTSE100 | See CSV | Rising = outperforming |

### Return Assessment
VUKG.L is a Vanguard FTSE 100 UCITS ETF, designed to track the FTSE 100 index. As a passive index tracker, its performance relative to ^FTSE should be minimal (tracking error). The strategy backtest showed a 7.5-year annualized return of ~9.2% with Sharpe ~1.02, consistent with a FTSE 100 index tracker. For an index ETF, absolute return metrics are less informative than tracking quality and beta relative to its benchmark (which should be close to 1.0).

### Strategy Alignment
The strategy report treats VUKG.L as a long-term hold asset with ~9.2% annualized returns and ~1.02 Sharpe. The backtested entry strategies (Score 3+, Golden Cross, SuperTrend+EMA) are designed to improve entry timing but the benchmark Buy & Hold already performs well, suggesting mean-reversion or dip-buying may be more effective than momentum chasing for this ETF.

---

## 4. Structure Analysis

### Key Levels
| Level | Value | Note |
|-------|-------|------|
| Nearest Support | See CSV | Distance: 0.89% |
| Nearest Resistance | See CSV | Distance: 15.22% |
| Swing High (recent) | See CSV | — |
| Swing Low (recent) | See CSV | — |

### Structure Signals
| Signal | Value | Interpretation |
|--------|-------|----------------|
| HH (Higher High) | 0 (last 30) | No bullish structure |
| HL (Higher Low) | 0 (last 30) | No bullish structure |
| LH (Lower High) | 2 (last 30) | Bearish structure |
| LL (Lower Low) | 1 (last 30) | Bearish structure |
| BOS (Break of Structure) | 2 (last 30) | Trend continuation events |
| CHoCH (Change of Character) | 0 (last 30) | No reversal signal |
| Trend Label | -1 | Bearish (short-term) |

### Structure Assessment
- **Pattern:** Bearish structure dominates the last 30 trading days — 2 LH (lower highs) and 1 LL (lower low) with zero HH/HL. This is consistent with a consolidation or mild downtrend within the broader bullish context.
- **Key levels:** Price is 0.89% above nearest support but 15.22% below nearest resistance, suggesting support is much closer than resistance — a concerning asymmetry for bulls.
- **Recent breaks:** 2 BOS signals in the last 30 days indicate some structural breaks occurred, but without CHoCH the overall character has not formally reversed. The trend label of -1 confirms short-term bearish structure.
- **Support touches:** 155 total support touches in the data history — the nearest support level has been tested many times, making it a well-established floor.

### Strategy Alignment
The recommended Score 3+ and Golden Cross strategies rely on bullish structural conditions. Current bearish short-term structure (LH/LL pattern, trend=-1) conflicts with the longer-term bullish alignment, creating an ambiguous entry signal. The strategy would be better executed on a pullback to support rather than at current levels.

---

## 5. Volatility Analysis

### Current Indicators
| Indicator | Value | Assessment |
|-----------|-------|------------|
| ATR(14) | 0.6190 | — |
| ATR Percentile | 25.0% | Low volatility |
| BB Width | 0.0495 | Moderate |
| %B | 0.6753 | Near upper band |
| HV(20) | 10.95% | — |
| Park Volatility | 10.24% | — |
| GARCH Vol | 0.7451 | Forecast: moderate |
| ATR Stop Distance | 3.21 | Suggested stop level |

### Volatility Assessment
- **Volatility Level:** ATR at 0.619 is in the 25th percentile of its historical range — this is relatively low volatility. For an FTSE 100 ETF, this is expected given its diversified nature.
- **Band Position:** %B at 0.675 places price in the upper third of the Bollinger Bands (55.91–58.74). Combined with the ATR stop distance of 3.21, the nearest support below is approximately 54.61.
- **Volatility Trend:** Historical volatility (10.95% annualized over 20 days) and Parkinson volatility (10.24%) are closely aligned, indicating stable and consistent volatility. GARCH forecast (0.745) suggests moderate near-term volatility without extreme moves expected.
- **Breakout Potential:** BB width at 4.95% is neither extremely contracted nor expanded. There is no strong breakout signal from the bands themselves.
- **Suggested Stop:** ATR-based stop at 3.21 points below current price would be at ~54.61, which aligns closely with the BB lower band (55.91) and the Donchian lower (55.83).

### Strategy Alignment
The strategy backtest noted a maximum drawdown of -34.3% over the 7.5-year period. Current volatility (ATR percentile 25%) is well below levels that would trigger drawdown concerns. The low current ATR percentile suggests this is a relatively safe entry window from a volatility standpoint, with limited downside risk unless volatility expands significantly.

---

## 6. Volume Analysis

### Current Indicators
| Indicator | Value | Assessment |
|-----------|-------|------------|
| OBV | 2,916,715 | Rising slope |
| CMF(20) | -0.1144 | Selling pressure |
| OFI | 0.0690 | Order flow favoring buyers |
| VWAP | 57.38 | Price above VWAP |
| ADL | -2,302,403 | Distribution pressure |
| MFI(14) | 135.56 | Extremely overbought |
| Volume Z-Score | 0.52 | Slightly above average |
| EMV(14) | 0.0000 | No ease of movement |

### Volume Assessment
- **Buying/Selling Pressure:** Mixed signals. CMF at -0.114 indicates net selling pressure over the last 20 days, while OFI at +0.069 shows recent order flow favoring buyers. This contradiction suggests selling has been occurring on the way up, but the most recent bars show buying interest.
- **Volume Trend:** OBV slope over 14 days (+20,773) is positive and strong, while the 7-day slope (+535) is much weaker. This suggests OBV has been rising but the momentum of OBV growth is slowing — a potential early warning sign.
- **Volume Intensity:** Volume z-score of 0.52 and percentile of 65% indicate current volume is slightly above average — not extraordinary but above the median.
- **Smart Money:** ADL at -2,302,403 is negative, indicating net distribution pressure. This is a bearish signal suggesting that larger players may be accumulating less or distributing.
- **Divergence Warning:** Price is near highs while CMF is negative and ADL is negative — this is a classic distribution pattern. The MFI at 135.6 is extremely elevated, suggesting heavy buying that may be exhausted.

### Strategy Alignment
The recommended Score 3+ strategy requires CMF>0 as one of its 6 entry conditions. Current CMF is negative (-0.114), meaning this condition is NOT met. The negative ADL further weakens the case for new entries. The strategy would be better executed when CMF turns positive, indicating sustained buying pressure.

---

## 7. Regime Analysis

### HMM Regime Probabilities
| Regime | Probability | Interpretation |
|--------|-------------|----------------|
| State 0 | 2.86% | Bullish (low probability) |
| State 1 | 0.74% | Bearish (negligible) |
| State 2 | 96.40% | Neutral/Sideways (dominant) |

### Regime Assessment
- **Dominant Regime:** State 2 (neutral/sideways) with 96.4% probability. This is an extremely confident regime classification — the model is virtually certain the market is in a sideways consolidation state.
- **Regime Stability:** The HMM has been in State 2 for all 60+ days in the recent history. This is a highly stable, entrenched regime — not a fleeting or transitional state. For an ETF that tracks the FTSE 100, this reflects the index's recent consolidation phase.
- **GARCH Context:** GARCH volatility (0.745) within this sideways regime is moderate, consistent with the low ATR percentile. The regime is not characterized by extreme volatility, suggesting the consolidation is orderly rather than panic-driven.
- **Trend context:** The underlying trend label of -1 and SuperTrend of +1 (with recent flips) show that while the regime is sideways, short-term trend signals are choppy. This is a classic "range-bound market with micro-trends" environment.

### Strategy Alignment
The strategy report's best-performing strategies (Score 3+, SuperTrend+EMA) tend to work best in trending regimes. In a sideways regime like the current one, these strategies are likely to generate more whipsaws and false signals. The sideways regime suggests that mean-reversion strategies (buying near support, selling near resistance) would be more effective than trend-following approaches. The current regime strongly supports a HOLD position rather than new entries.

---

## Signal Synthesis

### Score Summary
| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Trend | 4 | 20% | 0.80 |
| Momentum | 3 | 15% | 0.45 |
| Return | 4 | 15% | 0.60 |
| Structure | 2 | 15% | 0.30 |
| Volatility | 3 | 10% | 0.30 |
| Volume | 3 | 15% | 0.45 |
| Regime | 3 | 10% | 0.30 |
| **TOTAL** | | **100%** | **3.20 / 5.0** |

### Signal Determination
- **Overall Signal:** HOLD
- **Strength:** Normal
- **Confidence:** Medium

**Rationale:** A weighted score of 3.20 falls in the neutral range. Trend (4) and Return (4) are bullish, but Structure (2) is bearish-leaning. Momentum (3) is neutral with warning signs (declining MACD histogram, overbought MFI/CCI). Volume (3) shows mixed signals with negative CMF. Regime (3) is firmly sideways, which neutralizes the bullish trend signals. The HOLD signal is not weak — it reflects genuine ambiguity between long-term bullish structure and short-term sideways/choppy conditions.

### Supporting Indicators (Top 3 per dimension)
| Dimension | Indicator 1 | Indicator 2 | Indicator 3 |
|-----------|------------|------------|------------|
| Trend | EMA20>EMA50>EMA200 alignment | SuperTrend +1 (10+ days stable) | Price +4.15% above EMA200 |
| Momentum | RSI at 56 (neutral zone) | MACD line > signal (bullish cross) | ROC 20 positive (+1.18%) |
| Return | Long-term ~9.2% annualized return | Sharpe ~1.02 (good risk-adjusted) | FTSE 100 index beta ~1.0 |
| Structure | 155 support touches (established floor) | Donchian lower at 55.83 (strong support) | Price 0.89% above nearest support |
| Volatility | ATR percentile 25% (low risk) | BB width moderate (no squeeze) | GARCH forecast moderate (no spike) |
| Volume | OBV slope positive (14-day) | Price above VWAP (57.38) | Volume slightly above average |
| Regime | 96.4% sideways confidence | Stable 60+ day regime consistency | Moderate GARCH within regime |

### Conflicting Indicators
- **MACD histogram declining while price is near highs:** Bearish divergence — momentum is fading despite elevated price. If this continues, a MACD bearish cross could trigger further downside.
- **MFI at 135.6 vs RSI at 56.3:** MFI is volume-weighted and extremely overbought while RSI is neutral. This suggests the recent price rise has been accompanied by disproportionate buying volume that may be unsustainable.
- **CMF negative (-0.114) vs OFI positive (+0.069):** Selling pressure over 20 days conflicts with recent buying interest. The longer-term selling pressure outweighs recent buying, suggesting the recent rally may lack conviction.
- **Trend bullish (EMA alignment, SuperTrend up) vs Regime sideways (96.4%):** The long-term trend signals are bullish, but the regime model says the market is firmly sideways. This conflict suggests trend-following strategies will underperform in the current environment.
- **Williams %R and CCI both overbought:** Multiple momentum oscillators confirm overbought conditions despite neutral RSI. This suggests short-term exhaustion risk.

### Recommended Action
- **Entry:** Do NOT enter at current levels. Wait for either: (a) a pullback to nearest support (~57.30, ~0.89% below) with positive CMF confirmation, or (b) a breakout above Donchian upper (58.73) with volume expansion and positive CMF.
- **Stop-Loss:** Below nearest support at ~57.30, or using ATR stop at ~54.61 (3.21 points below current price) for wider protection.
- **Target:** Nearest resistance at ~58.73 (Donchian upper / BB upper). Secondary target at ~58.81 (Keltner upper) if breakout occurs.
- **Position Sizing:** Given low current volatility (ATR percentile 25%) and well-established support, standard position sizing is appropriate. Risk no more than 1-2% of portfolio per trade.
- **Max Holding Period:** 2-4 weeks for a range-bound trade. Re-evaluate if regime shifts.

### Risk Factors
- **Momentum exhaustion:** MACD histogram declining for 5 days, MFI extremely overbought at 135.6. A reversal could be swift.
- **Regime stability fragility:** While 60+ days in State 2 is stable, sideways regimes can end abruptly. A breakout (up or down) from this range could be significant.
- **Volume divergence:** Negative CMF and ADL despite rising price is distribution — smart money may be reducing exposure.
- **Weak trend strength:** ADX at 16.01 confirms no strong directional conviction. Any news event could trigger outsized moves in either direction.

### When This Signal Is Invalidated
- **Close below EMA200 (55.52):** Would invalidate the long-term bullish structure. Signal becomes SELL.
- **SuperTrend flips to -1 and holds for 5+ days:** Would indicate trend has officially reversed. Signal becomes SELL.
- **HMM regime shifts from State 2 to State 1 (bearish):** Would confirm bearish momentum. Signal becomes SELL.
- **RSI drops below 40:** Would indicate significant momentum deterioration. Signal becomes WAIT.
- **Breakout above 58.81 (Keltner upper) with volume expansion:** Would invalidate HOLD, signal could shift to BUY on confirmed breakout.

---

## Next Steps

- **Monitor for pullback to support at ~57.30:** If price retreats to this level and CMF turns positive, it would provide a better entry with improved risk-reward (stop at 54.61, target 58.73 = ~2.7:1 ratio).
- **Watch MACD histogram:** If it continues declining and crosses below zero, expect further downside. A turnaround in MACD histogram (rising from current 0.117) would be an early sign of momentum recovery.
- **Track regime changes:** If HMM shifts from State 2 (sideways) to State 0 (bullish), this would validate the longer-term bullish trend and support a BUY signal. Conversely, any shift to State 1 (bearish) would trigger a SELL.
- **Re-run evaluation on:** (a) next trading day close, (b) any close below EMA20 (57.59), or (c) any close above 58.81 (Keltner upper).
- **If entering, use Score 3+ rules from strategy report** (`data/strategy/VUKG.L/20261021.md`): Wait for CMF>0 and ADX>20 to improve the current 3/6 score to 4/6 or 5/6 before committing capital.
- **Consider this ETF as a long-term hold:** VUKG.L is a diversified FTSE 100 tracker. For buy-and-hold investors, short-term signals matter less than the long-term ~9.2% annualized return profile. Use pullbacks as accumulation opportunities rather than timing entries precisely.
- **Set alerts:** Price alerts at 57.30 (support), 58.81 (resistance), and 55.52 (EMA200/stop-loss) to stay informed of critical levels.
