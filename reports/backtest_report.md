# Backtest report

Chronological, leakage-free evaluation of the weekly demand estimate used by the rules. Each forecast uses only weeks up to its origin; horizon 1 week.

Methods:

- `baseline_12w`: 12-week moving average (baseline)
- `rules_engine`: 12-week average + festival uplift (rules engine)
- `recent_4w`: 4-week moving average (reference)

## Summary

| method | observations | MAE | WAPE | description |
|---|---|---|---|---|
| baseline_12w | 60.0 | 8.07 | 8.7% | 12-week moving average (baseline) |
| recent_4w | 60.0 | 6.13 | 6.6% | 4-week moving average (reference) |
| rules_engine | 60.0 | 14.86 | 16.0% | 12-week average + festival uplift (rules engine) |

The rules-engine estimate **does not beat** the 12-week baseline (16.0% vs 8.7% WAPE). In this sample, October weeks did not rise 25% for most SKUs, so the festival uplift overstates demand. Rule A should be reassessed with Raghav before a pilot. 

## By target week

| target | target_festival | method | observations | MAE | WAPE |
|---|---|---|---|---|---|
| 2026-W39 | False | baseline_12w | 15.0 | 9.13 | 9.9% |
| 2026-W39 | False | recent_4w | 15.0 | 9.05 | 9.8% |
| 2026-W39 | False | rules_engine | 15.0 | 9.13 | 9.9% |
| 2026-W40 | True | baseline_12w | 15.0 | 8.51 | 9.2% |
| 2026-W40 | True | recent_4w | 15.0 | 7.1 | 7.6% |
| 2026-W40 | True | rules_engine | 15.0 | 17.81 | 19.2% |
| 2026-W41 | True | baseline_12w | 15.0 | 7.78 | 8.4% |
| 2026-W41 | True | recent_4w | 15.0 | 4.83 | 5.2% |
| 2026-W41 | True | rules_engine | 15.0 | 16.56 | 17.9% |
| 2026-W42 | True | baseline_12w | 15.0 | 6.88 | 7.4% |
| 2026-W42 | True | recent_4w | 15.0 | 3.53 | 3.8% |
| 2026-W42 | True | rules_engine | 15.0 | 15.94 | 17.1% |

Evaluated SKU-week forecasts per method: 60. Excluded origins: 165 (fewer than 12 weeks of history).

## Limits

- Chronological, expanding origin: each forecast uses only weeks up to its origin.
- Horizon: 1 week(s) ahead. Origins need 12 prior weeks.
- Festival status of the target week comes from calendar.csv (week assigned to the month of its Thursday).
- Stockout/overstock outcomes are not simulated: no historical inventory snapshots, lead times or prices exist in the data.
- 15 SKUs x 16 weeks is a small sample; results are indicative only.
- Forecast accuracy is not a business outcome. No savings are claimed.
