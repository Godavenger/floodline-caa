# Data dictionary and feature rules

## Observations

| Field | Meaning / validation |
| --- | --- |
| source_record_key | Stable upstream key; combined with source_id for uniqueness |
| source_id, area_id | Must exist in the source register and spatial fixture |
| observed_at | Time of measurement; ISO 8601 with a timezone, stored UTC |
| received_at | Time the application could first use the record; cannot precede observation |
| variable | rainfall or water_level |
| value, unit | Rainfall interval amount in mm; gauge height in m |
| interval_minutes | Must equal the source's registered 15-minute interval |
| quality | good, suspect or missing; null requires missing and never becomes zero |
| longitude, latitude | WGS84 coordinate covered by the declared cell |
| raw_fingerprint | SHA-256 of the received record for conflict detection |

Rainfall accepts mm, cm and inches; water levels accept m, cm and mm.
Conversions produce canonical mm/m. Demonstration plausibility limits are
0–500 mm per rainfall interval and 0–30 m for a gauge. They are engineering
fixtures, not approved local hydrological bounds. Incompatible units, negative
values, invalid geometry and conflicting reused keys are quarantined.

For an issue at time t, a record is available only if both observed_at and
received_at are at or before t. A later correction to the same interval is used
only after its receipt. Duplicate records do not create new observations.

## GIS

| Field | Meaning |
| --- | --- |
| area id / ward_id | Stable cell IDs A1–C3 and ward IDs A–C |
| geometry_version | synthetic-pilot-v1 |
| source_resolution_m | Approximately 1000 m; no 250 m accuracy claim |
| relative_elevation_m | Synthetic relative terrain height |
| impervious_fraction | Synthetic 0–1 surface proxy |
| drainage_constraint | Synthetic 0–1 constraint proxy; larger is less favourable |
| distance_to_water_m | Synthetic proximity feature, not proof of flood cause |
| road segment / edge | One physical segment can contain two directed edges |

Map export is WGS84 (EPSG:4326). Distance, snapping and geometry matching use
UTM zone 45N (EPSG:32645). The graph has 21 nodes and 61 directed edges,
including one-way and disconnected cases. Start/end snapping is bounded;
moderator-selected hazard segments must lie within 150 m of the report pin.

## Issue-time features and risk

| Feature / output | Definition |
| --- | --- |
| rainfall_1h_mm, rainfall_3h_mm, rainfall_6h_mm, rainfall_24h_mm | Sum of known interval amounts in the look-back window; null when none are known |
| coverage_1h / coverage_3h | Known interval count divided by expected interval count |
| rainfall_observed_at / rainfall_age_minutes | Newest contributing rainfall observation and current age |
| water_level_m, level_observed_at | Latest available valid gauge value and its observation time |
| available_at | Receipt time of newest contributing evidence |
| fingerprint | Accepted-record references plus geometry/rule version |
| issued_at | When newest contributing evidence became available |
| valid_until | Three-hour maximum record validity; earlier staleness still applies |
| index | Relative warning index 0–100; null for unknown |
| susceptibility_index | Static synthetic terrain/drainage index, distinct from probability |
| risk_level | low/Monitor, elevated, high or unknown |
| data_support | adequate, limited or insufficient; evidence quality, not a confidence interval |

Rainfall older than 90 minutes or less than 75% three-hour coverage produces
unknown. Incomplete coverage, rainfall older than 30 minutes or a gauge older
than 60 minutes produces limited support. Missing/stale gauges are excluded
from interpretation. The retained record keeps its original issue time.

## Reports, hazards, consent and delivery

Reports move from pending to verified, rejected or duplicate. A verified report
may be resolved; time-limited evidence expires. Only active verified hazards
exclude road-edge IDs. Withdrawal removes owned evidence without claiming that
an independently reviewed restriction has cleared.

Image input is JPEG/PNG/WebP, up to 5 MB and 12 megapixels. Re-encoded images
are at most 2048 px on the long side. Publication requires privacy review.

Subscriptions store the resident, ward, in-app channel, consent time and active
state. Alerts store kind, severity, trigger, idempotency key, message version,
issue/expiry time, attempts, retry time and queued/sent/failed/expired/cancelled
state. Delivery retries stop on withdrawn consent, expiry, stale evidence,
resolved hazards or newer evidence that no longer supports the warning.

## Historical labels

The evaluation CSV records event/area/row IDs, issue time, feature availability,
three-hour target-window end, label state, evidence reference and negative
support. Unknown, unverified, unsupported-negative and late-feature rows are
excluded. Positive onset timestamps, when supplied, must fall after issue time
and inside the target window. Real and synthetic datasets cannot be mixed.
