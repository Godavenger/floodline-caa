# Model card — synthetic fallback

## Intended use and current status

The active version is demo-threshold-v1, a relative susceptibility and rainfall
warning rule for nine synthetic cells. It supports software demonstration and
evidence interpretation. It has **no established historical forecasting
accuracy**, calibrated flood probability or authority to issue emergency orders.
The three-hour validity limit is a maximum record lifetime, not a validated
forecast horizon.

The user-approved sparse-data gate is active. A logistic-regression candidate
exists only as an unpromoted experiment artifact. The running app never loads it
for live decisions.

## Active rule

Static susceptibility S, rounded to an integer, is:

~~~text
100 × (
  0.35 × impervious_fraction +
  0.35 × drainage_constraint +
  0.20 × max(0, 1 - relative_elevation_m / 10) +
  0.10 × max(0, 1 - distance_to_water_m / 1500)
)
~~~

The current warning index is round(0.35 × S + 0.65 × R), with
R = min(100, rainfall_3h_mm / 75 × 100). Index ≥75 is high; ≥55 is elevated;
otherwise it is Monitor. Alert hysteresis resets below 45. All weights,
thresholds and dimensions are demo configuration, not local guidance.

Rainfall missing, older than 90 minutes or with under 75% of expected
three-hour intervals produces unknown and a null current index. Limited
support identifies incomplete rainfall, older recent rain or a stale/missing
gauge. Gauge values are displayed as context and affect the data-support flag;
they do not enter this numerical warning index.

## Software experiment

Run:

~~~powershell
python -m backend.floodline evaluate
~~~

The frozen synthetic dataset uses seed 20261111, 18 storm groups separated by
three days, nine areas and four issue times per storm. Unknown labels are
excluded, leaving 624 usable rows. Positive onset timestamps lie in each
three-hour future target window. No row substitutes for an independent storm.

Chronological event groups are split into 10 training, 4 validation and 4
test events. Events with target/look-back overlap are purged as whole groups.
Imputation, missing indicators, scaling and class weighting are fitted on
training only. A threshold from 0.2–0.7 is selected by validation F2 score,
then frozen before final-test prediction.

The candidate uses rainfall over one/three hours, relative elevation,
impervious fraction, drainage constraint and water level. It is compared with
a separate 75 mm rainfall-only baseline and a training-prevalence baseline.
The rainfall-only comparator is not the composite map index.

Evaluation records recall, precision, average precision, confusion counts,
errors by event/area and simulated lead time. Brier score is a software
diagnostic for candidate/prevalence scores; it is omitted for the uncalibrated
rainfall index. False-positive rows per event count repeated decision
opportunities, **not distinct delivered alerts**. Actual notification
deduplication/retries are tested separately.

The exact results, dataset hash, split IDs and candidate artifact are in the
release evidence. Four synthetic held-out storms are too few for stable
calibration or claimed metric intervals. Synthetic labels establish pipeline
behaviour only.

## Promotion and limitations

Real-world promotion requires a chosen pilot, licensed observations,
independent credible event labels, supported negatives, a receipt-time leakage
audit, adequate separated events and a frozen held-out comparison supporting
improvement at an acceptable alert burden. Calibration and geographical
transfer require their own evidence. The candidate remains unpromoted even
when a real CSV is supplied until that evidence is reviewed.

Synthetic terrain omits drains, kerbs, culverts, maintenance and local
exposure. Approximately 1 km support cannot determine road-water depth.
Observed, moderator-verified road hazards are a separate action stream;
community reports never automatically retrain the model.
