# Backtest report

Chronological, leakage-free evaluation of the weekly demand estimate used by the rules. Each forecast uses only weeks up to its origin; horizon 1 week.

Methods:

- `baseline_12w`: 12-week moving average (baseline)
- `rules_engine`: 12-week average + festival uplift (rules engine)
- `recent_4w`: 4-week moving average (reference)

## Summary

| method | observations | MAE | WAPE | description |
|---|---|---|---|---|
| baseline_12w | 64.0 | 7.8 | 8.6% | 12-week moving average (baseline) |
| recent_4w | 64.0 | 5.87 | 6.5% | 4-week moving average (reference) |
| rules_engine | 64.0 | 14.54 | 16.0% | 12-week average + festival uplift (rules engine) |

The rules-engine estimate **does not beat** the 12-week baseline (16.0% vs 8.6% WAPE). In this sample, October weeks did not rise 25% for most SKUs, so the festival uplift overstates demand. Rule A should be reassessed with Raghav before a pilot. 

## By target week

| target | target_festival | method | observations | MAE | WAPE |
|---|---|---|---|---|---|
| 2026-W39 | False | baseline_12w | 16.0 | 8.81 | 9.7% |
| 2026-W39 | False | recent_4w | 16.0 | 8.64 | 9.6% |
| 2026-W39 | False | rules_engine | 16.0 | 8.81 | 9.7% |
| 2026-W40 | True | baseline_12w | 16.0 | 8.25 | 9.0% |
| 2026-W40 | True | recent_4w | 16.0 | 6.83 | 7.5% |
| 2026-W40 | True | rules_engine | 16.0 | 17.37 | 19.0% |
| 2026-W41 | True | baseline_12w | 16.0 | 7.42 | 8.2% |
| 2026-W41 | True | recent_4w | 16.0 | 4.55 | 5.0% |
| 2026-W41 | True | rules_engine | 16.0 | 16.35 | 18.0% |
| 2026-W42 | True | baseline_12w | 16.0 | 6.73 | 7.3% |
| 2026-W42 | True | recent_4w | 16.0 | 3.47 | 3.8% |
| 2026-W42 | True | rules_engine | 16.0 | 15.62 | 17.0% |

Evaluated SKU-week forecasts per method: 64. Excluded origins: 176 (fewer than 12 weeks of history).

## Limits

- Chronological, expanding origin: each forecast uses only weeks up to its origin.
- Horizon: 1 week(s) ahead. Origins need 12 prior weeks.
- Festival status of the target week comes from calendar.csv (week assigned to the month of its Thursday).
- Stockout/overstock outcomes are not simulated: no historical inventory snapshots, lead times or prices exist in the data.
- 16 SKUs x 16 weeks is a small sample; results are indicative only.
- Forecast accuracy is not a business outcome. No savings are claimed.
