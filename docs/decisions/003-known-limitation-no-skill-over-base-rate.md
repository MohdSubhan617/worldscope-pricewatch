# 003 - v0.1 model is calibrated but shows no skill over the base rate

Status: accepted, known limitation

On the first published run (simulated day 2026-11-02) the held-out Brier score was 0.1199 against
0.1198 for a constant base-rate predictor; ECE was 0.014. Promotions in the simulator start as a
memoryless Bernoulli process with only a seasonal rate boost, so there is little for any model to
learn. We keep the simulator as documented rather than leaking predictability into it to flatter
the model. The test suite asserts calibration and (on one seed) beating the base rate; the
published metrics.json reports the honest numbers. Future work: add predictable structure to the
simulator (for example scheduled model-refresh sales) and document it as an assumption.