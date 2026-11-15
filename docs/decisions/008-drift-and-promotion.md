# 008 - Drift detector and promotion policy

Status: accepted

Drift (`pricewatch.drift`): PSI (reference-quantile bins, threshold 0.25) and two-sample KS.
A column is flagged if PSI >= 0.25, or KS p < 0.01 AND statistic >= 0.10 (the extra effect-size
floor avoids flagging trivial shifts on large samples). Tests: 20 same-distribution seeds raise no
alarm; a planted mean shift and a planted variance shift are detected, and only on the shifted
column. Retrain reports drift on price-behaviour features only; on the simulated data several
of them are flagged between windows because the sale calendar makes the windows seasonally
different, so drift is INFORMATIONAL in v0.1.1 and does not block promotion.

Promotion (`pricewatch.promotion`): promote only if the lower bound of a 95% day-clustered
bootstrap CI on (champion Brier - challenger Brier) is >= margin (default 0.002 absolute).
Same-data retrains are not promoted (tested). The first model is promoted unconditionally.

Weekly retrain (`weekly-retrain.yml`) fits a challenger on data ending holdout+purge+embargo before
the last 60 labelled days, scores both models on that holdout, persists the champion
(`state/models/champion.joblib`, trusted pickle from our own branch) and a JSON report.
Known gap: the daily export (`pricewatch run`) still refits its own model each day and does not
yet load the champion; the registry is exercised only by the weekly job. Listed in the release
checklist.
