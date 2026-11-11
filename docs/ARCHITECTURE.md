# Architecture and integration

The local application follows the supplied P1–P8 pipeline. It uses FastAPI,
SQLite, React/TypeScript and Leaflet. Shapely and PyProj validate and project GIS
geometry, NetworkX calculates directed routes, and scikit-learn runs the separate
evaluation. PostgreSQL/PostGIS has an optional adapter and migrations.

~~~mermaid
flowchart LR
  Raw[Synthetic raw observations] --> Check[Validate, convert and deduplicate]
  Check -->|invalid| Quarantine[Quarantine with reasons]
  Check --> Features[Issue-time feature snapshot]
  GIS[Versioned cells, terrain and roads] --> Features
  Features --> Rule[Relative index and threshold rule]
  Rule --> Map[Map and area evidence]
  Rule --> Alerts[Consent, cooldown and delivery state]
  Resident[Resident observation and image] --> Review[Private moderation queue]
  Review -->|verified| Hazard[Bounded road-edge hazard]
  Hazard --> Map
  Hazard --> Route[Directed route with exclusions]
  Hazard --> Alerts
  Labels[Separate reviewed event dataset] --> Evaluate[Temporal evaluation]
  Evaluate --> Candidate[Unpromoted candidate artifact]
~~~

## Processing and storage

The startup lifecycle applies numbered migrations, verifies fixture SHA-256
checksums, seeds a new database once and processes one cycle. A 30-second worker
checks expiry, computes a new risk record only when contributing evidence
changes, decides alerts and processes due retries. Synthetic feed scenarios are
deliberately invoked through authenticated controls.

Every cycle is a database transaction. Related risk, hazard and alert writes
either commit together or roll back. A local lock serializes database work; the
prototype is intended for one application process, not a fleet of workers.

The tables are:

- areas, sources, road_nodes and road_edges for versioned spatial/source data;
- observations and quarantine for accepted and rejected evidence;
- risk_runs and events for issue-time decisions and separate event references;
- reports and hazards for private evidence and verified restrictions;
- users and sessions for resident ownership and moderator authentication;
- subscriptions, alert_state and alerts for consent and delivery;
- jobs, audit and settings for replay, operations and decision history.

UTC ISO timestamps include a timezone. The UI shows IST, while the report
datetime input is interpreted in the device's local timezone. Demo time advances
with wall-clock elapsed time and with replay controls; session expiry uses wall
time. Repeated polling never refreshes an old observation's issue time.

## Access and images

An anonymous visitor can read public map/evidence and request a route. A resident
session owns its reports, images, subscriptions and alert history. Moderators
authenticate separately and can review reports and inspect operations. Ending
moderator access restores the existing resident cookie.

Writes require the client marker and an allowed/same origin. Session cookies
are HttpOnly and SameSite=Strict, and use Secure under HTTPS. Login/report request
limits, per-session report limits, content security headers and ownership checks
are enforced. These are prototype controls; no public hosting claim is made.

Images are decoded, oriented according to EXIF, converted to clean RGB pixels,
resized and re-encoded. Originals and metadata are not stored. Private image
URLs check access; publication requires a verified report and explicit image
privacy review. Report withdrawal deletes its text/image evidence. A separately
reviewed hazard keeps its own expiry and audit reference.

## Deployment choices

SQLite is the tested local mode. PostGIS adds validated geometry columns,
triggers and spatial indexes to the shared schema; distance and routing still
use the same projected Python calculations. Docker/PostgreSQL are unavailable
on the verification machine. Their preparation files are supplied as an
untested optional deployment path.

Real feeds, calibrated forecasting, external notifications, multi-worker
coordination, field validation and human-data retention policies require later
work after a real pilot and its evidence are selected.
