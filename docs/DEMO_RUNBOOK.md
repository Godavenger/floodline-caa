# Demonstration and operations runbook

## Local launch

Double-click start.bat or run the following from the project root:

~~~powershell
.\start.bat
~~~

The launcher opens the dashboard after the server is ready. It normally uses
http://127.0.0.1:8000 and selects the next free port when that default is busy;
the console prints the actual address. An explicit -Port 8001 requests that
port and reports a conflict if it is already occupied.

It uses a project interpreter when available, installs missing pinned Python
dependencies into .venv with network access, uses the bundled interface, backs
up existing SQLite data, migrates, evaluates and starts one FastAPI process.
Python 3.12+ is required; Node and npm are needed only for -Rebuild or an absent
interface build. Use -Install to retry setup, -SkipBuild to require the bundled
interface, -PrepareOnly for setup and -NoBrowser to leave browser opening to
the presenter. start.cmd remains a compatible alias. No global PowerShell
policy is changed.

If startup fails, an interactive batch window waits for Enter and shows the
error and its log path. Logs are under .runtime/launcher-logs/. Check the error
before retrying; Python installation, dependency-download and port conflicts
include specific next steps. The launcher does not delete existing demo data.

For a new, separate rehearsal without deleting any existing reports:

~~~powershell
$env:FLOODLINE_RUNTIME = '.runtime/rehearsal'
.\start.bat
~~~

A new runtime starts at 14:02 IST on 11 November 2026. Initially it has nine
cells, three warning cells, one unknown cell and one active verified hazard.
An already-used runtime retains its own history and elapsed demo clock. It may
therefore open with stale observations; use the replay controls deliberately.

Sign in as moderator / floodline-demo. Change the default by editing .env from
.env.example before hosting beyond the local demonstration.

## Ten-minute CAA demonstration

| Time | Speaker | Action and explanation |
| --- | --- | --- |
| 0:00–1:15 | M1 | Declare the synthetic pilot and sparse-data fallback. Show the source register, raw archive, checksums and the 866 accepted / 1 duplicate / 2 quarantined initial outcome. |
| 1:15–2:30 | M2 | Show the three wards, approximately 1 km cells and directed graph. Calculate Library → Station and inspect the excluded segment. |
| 2:30–4:00 | M3 | Open Data & model, expand the evaluation gate and show the frozen split. Explain that synthetic scores cannot establish historical prediction accuracy. |
| 4:00–5:30 | M4 | Submit an observation with an image near a route segment. Verify pending privacy, moderator access, time/location matching and the audit record. |
| 5:30–7:00 | M5 | Verify a corroborated road restriction, recalculate and inspect the changed route. Show the map/evidence and report form at phone width. |
| 7:00–10:00 | M6 | Return to resident access, opt in to a ward and inspect delivery. Repeat processing, simulate a failed send, apply heavy rain, outage and recovery, and show expiry/unknown states. |

At Station, the north approach is road-n4-1-n4-2; select it only when the report
pin supports that match. This segment is on the default Library → Station
route. The alternative uses different edges with the same distance because the
synthetic graph has tied paths. The browser script chooses an actual segment
from the baseline route to make the comparison deterministic.

Observed report time should come from the displayed demo clock. No participant
needs to visit a flooded road or take measurements.

## Replay controls and delivery

Light rain, Heavy rain and Recover feed each advance demo time by 15 minutes
and add clearly synthetic observations received at the new issue time.
Recovery reconstructs a synthetic history; it does not pretend a real outage's
missing observations were recovered. Feed outage advances time by 105 minutes
without inserting rain. The map retains original issue times and shows unknown.

Process again recomputes eligible decisions without inventing new evidence.
Alert idempotency prevents repeats of the same trigger. A 30-minute cooldown
applies to unchanged warning reminders; severity increases can bypass it.

Fail next delivery configures one simulated failure. The first retry is due
after 30 seconds, the second after 60; at most three attempts are made.
Withdrawn subscriptions, stale/superseded evidence, resolved hazards and expiry
cancel further delivery. No real provider is contacted.

## Verification

~~~powershell
.\.venv\Scripts\python.exe scripts/verify_backend.py
.\.venv\Scripts\python.exe scripts/verify_launcher.py
node scripts/verify-ui.mjs
~~~

The backend suite covers ingestion, receipt-time availability, access, private
uploads, moderation, road matching, directed routing, consent, cooldown,
retry/expiry, outage/recovery and backup/rollback. The browser run creates an
isolated SQLite runtime and captures actual interactions and failure states.
The Windows launcher suite uses separate folders with spaces and temporary
databases. It serves the real bundled interface with Node blocked, verifies
backup/data preservation, tests port conflicts and checks visible error/log
messages, including a first dependency setup with network access disabled.
Successful startup checks reuse installed Python dependencies.

Use GET /api/health and the moderator Pipeline health panel for operating
checks. The offline /docs page lists endpoint actions; /openapi.json supplies
schemas. A 30-second worker checks current evidence; it is not an upstream
weather feed.

## Backup, restore and retention

~~~powershell
.\.venv\Scripts\python.exe -m backend.floodline backup .runtime/backups/manual.db
~~~

This backs up SQLite only. For a full local archive, stop the app and copy the
runtime's images and evaluation files along with the database to a private
location. To restore, stop the app, retain the current database as a separate
backup and replace the database from the known-good copy. The acceptance suite
tests restore/integrity against temporary databases without replacing user
data.

Original uploads and EXIF are not retained. Processed images are removed on the
next processing cycle after the report is 30 demo days old; the cleanup is
audited, and retained report text is unaffected. No cleanup runs while the app
is stopped. Report withdrawal removes its text and image immediately; audit
references and separately reviewed restriction validity remain. A human-data
pilot must establish its own consented retention period and cleanup policy.

## Optional PostgreSQL/PostGIS and containers

This path is prepared but **untested locally**; Docker and PostgreSQL are not
installed on the verification machine.

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-postgres.txt
$env:DATABASE_URL = 'postgresql://floodline:YOUR_PASSWORD@localhost:5432/floodline'
.\start.bat
~~~

Use a database role permitted to install PostGIS during initial migration.
The shared schema gains geometry columns, validation triggers and spatial
indexes. Health reports postgresql-postgis. Run the full acceptance suite
against that adapter before claiming deployment readiness.

The optional compose file uses local demo credentials and binds the web port
to localhost:

~~~powershell
docker compose up --build
docker compose exec app python -m backend.floodline evaluate
~~~

PostgreSQL backups use pg_dump rather than the SQLite helper. Store a custom
format dump inside the database container, then copy it out:

~~~powershell
docker compose exec db pg_dump -U floodline -d floodline -Fc -f /tmp/floodline.dump
docker compose cp db:/tmp/floodline.dump outputs/floodline.dump
~~~

Hosted TLS, credentials, migrations, provider delivery, PostGIS acceptance,
monitoring and multi-worker coordination remain later deployment work.
