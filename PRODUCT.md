# Smart City Flood Prediction and Community Alert Platform

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

The supplied implementation pipeline specifies Python/FastAPI, React/Leaflet,
GeoPandas/scikit-learn and PostgreSQL/PostGIS. Follow that stack. A documented
SQLite mode is permitted as a local demonstration fallback where PostgreSQL
is unavailable; it must use the same service contracts and expose its mode.

## Users

Residents inspect area risk, submit waterlogging evidence, subscribe to in-app
alerts and request routes that avoid verified hazards. Administrators review
reports and inspect feed freshness, alert failures and the audit trail. The
six-person CAA team demonstrates and explains the complete pipeline.

## Product Purpose

Connect environmental observations, geographic context and reviewed community
evidence to an understandable prototype map and useful local actions. Preserve
the distinction between future risk, observed conditions and data support.

## Operating Context

The user asked to continue the project using
`outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md` and explicitly selected
"Use a synthetic pilot for now" on 11 November 2026. The workspace initially
contained the project description and an 18-page pipeline, with no application
source, real pilot data, event labels or credentials.

## Capabilities and Constraints

- One bounded synthetic catchment, three demo wards and a small directed road
  graph; names and geometry are development fixtures.
- Timestamped, deduplicated observations with provenance and quarantine.
- An interpretable susceptibility/threshold baseline; numerical probabilities
  and real-world forecasting accuracy require independent historical evidence.
- Pending, verified, rejected, duplicate, resolved and expired report states.
- Consent-based in-app subscriptions, bounded delivery retries and expiry.
- Route exclusions use active verified road-edge hazards only.
- Reproducible local setup, database migrations, evaluation evidence and demo.
- Pilot city, actual data access, course deadline and M1-M6 names are undecided.
- Real notifications, hosted deployment and IoT hardware are optional and are
  not enabled by default.

## Evidence on Hand

`project description.docx`, item 3, supplies the assignment requirements.
`outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md` supplies work packages,
interfaces, scope gates and acceptance checks. The user approved synthetic data;
it can establish software behavior, not real-world predictive validity.

## Product Principles

1. Unknown observations remain unknown; missing rainfall never becomes zero.
2. Issue-time features use only observations received by that time.
3. Evidence and actions carry their source, validity and limitations.
4. A report cannot block a road before authenticated review.
5. Every displayed total is computed from the underlying records.

## Accessibility & Inclusion

The pipeline requires keyboard operation, visible focus, non-color risk words,
text alternatives for map-only information, responsive resident flows and
understandable uncertainty messages. A local-language alert remains a future
human-reviewed deliverable after the real pilot is selected.
