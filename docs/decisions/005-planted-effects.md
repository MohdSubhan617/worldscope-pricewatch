# 005 - Plant detectable effects in the simulator; recovery margin stated

Status: accepted (supersedes the "future work" in 003)

Planted, documented assumptions (simulated; not calibrated to any real market):
1. Scheduled sale windows from `configs/sale_calendar.yaml` add `sale_depth` markdown to every
   product in the window.
2. Age-based decay: permanent `cycle_cut` price cuts at ~85% and ~100% of the category refresh
   cycle (+-5 days jitter per product).

Features are leakage-safe: product age and refresh cycle are launch-time metadata, the sale
calendar is public, prices are only used up to day t.

Recovery test: relative Brier reduction vs the oracle constant (test-set base rate, a stricter
baseline than a train-set rate) must be >= 0.25. Measured on seeds 5/6/7: 0.575 / 0.549 / 0.552
against the train-rate baseline (~0.55 relative); a negative control with both effects set to zero
measured -0.005 and -0.214, i.e. does not meet the margin, so the test discriminates.
All "simulated" disclaimers are unchanged; recovering planted effects says nothing about real data.
