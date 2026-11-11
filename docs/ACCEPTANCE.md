# Recorded acceptance evidence

Release v0.1.1 · synthetic pilot · 11 November 2026

The delivered scope is three invented wards, nine analysis cells and one small
directed road graph. These records establish software behavior. Historical
prediction accuracy and human usability outcomes are not established.

## Automated results

The latest backend run passes **44 tests**, with no failures, errors or skips.
The production frontend build and browser acceptance pass **14 workflow
checks**, recording **62 screenshots** in Light and Dark at 1440, 1024, 390 and 320 px widths.
The browser run records no uncaught JavaScript errors or horizontal overflow.

| Pipeline check | Recorded behavior | Evidence |
| --- | --- | --- |
| P1/P2 scope and integrity | Initial ingestion accepts 866 records, ignores one duplicate and quarantines two invalid records; nulls and delayed receipts remain explicit | `backend-acceptance.json`, `backend-tests.txt`, `data/manifest.json` |
| P3 geography and routing | WGS84 display, EPSG:32645 distances, bounded snapping, one-way graph and unreachable destinations | Backend spatial/routing tests; route screenshots |
| P4 evaluation | 18 synthetic storm groups; chronological 10/4/4 event split; preprocessing and threshold selection precede the frozen test | `evaluation.json`, `split-manifest.json`, synthetic event ledger, model card |
| P5 access and uploads | Private pending reports and images, authenticated moderation, ownership checks, content/size validation, EXIF removal and audited 30-demo-day processed-image cleanup | Backend API/privacy/retention tests |
| P6 resident and moderator tasks | Map and evidence, reporting, correction, publication, consent, withdrawal and keyboard navigation work across the recorded viewport sizes | `browser-acceptance.json` and `.impeccable/review/` |
| P6 appearance | System/Light/Dark preferences, device changes, manual overrides, invalid/cleared storage, disabled storage, cross-tab changes, persistence before React loads, map continuity and AA text/control contrast pass | `browser-acceptance.json` theme acceptance and 31 pairs of workflow captures |
| P7 alert lifecycle | Repeated decisions deduplicate; severity escalation, cooldown, failed delivery, bounded retries, withdrawal and expiry are tested | Backend alert tests and alert screenshots |
| P7 road restrictions | Only active verified hazards exclude edges; a newly verified report changes the route; blocked connections return an explicit unavailable result | Route comparison in `browser-acceptance.json`; backend exclusion tests |
| P8 recovery | Outage retains issue times and makes all nine cells unknown; recovery is explicitly synthetic; an injected inference failure is logged by class and the worker resumes without duplicate risk/alert records | Backend worker/outage tests and browser outage/recovery captures |
| P8 database integrity | Idempotent migrations, SQLite backup/restore, integrity check and transactional rollback pass | Backend database tests |

Machine-readable records and report figures are in `outputs/evidence/`.
The backend record includes interpreter, platform, package versions and run
times. The browser record includes the built entry-page hash, the early
appearance script hash and all capture hashes. The early script is an external
same-origin asset compatible with the backend's Content Security Policy.

## Final interface corrections

The original v0.1.0 review at `.impeccable/review/finish-review.md` required two fixes:
the outage summary and the resident form's error/save-state wording. The updated
browser acceptance checks verify that:

- All-unknown conditions lead with unavailable-data wording above the map,
  including on a phone. Partial coverage uses the evaluated denominator and
  explicitly counts unknown cells; the initial state is three warnings among
  eight evaluated cells, with one unknown.
- Landmark, coordinate and map-pin corrections clear location errors while
  preserving unrelated request errors. Before submission the form says it
  will be saved as pending; confirmation follows API success.

The original reviewer continuation failed with a tool resource error. A fresh
verdict pass scores these two fixes at `.impeccable/review/finish-verdict.md`.
That baseline reviewer scored both fixes **resolved**, with **disposition: ship**.
This historical verdict covers those two fixes. The v0.1.1 browser checks repeat
their assertions in both themes, and `.impeccable/review/dark-mode-review.md`
records the appearance inspection. The packaged extraction has a separate
verification record next to the ZIP.

The recorded light and dark taste inspections have no FAILs and one WARN each
for five detected hues.
Those hues encode environmental data, risk categories and a verified road
restriction on a geographic map; they preserve distinct meanings rather than
adding unrelated chart series. The remote design catalog/QUALITY BAR board was
unavailable, so no comparison to its visual ceiling is claimed.

## Performance and reproducible release

`outputs/evidence/performance.json` records 20 local dashboard requests from ten
concurrent clients against SQLite. Its measured p95 is below the proposed
3,000 ms target. This excludes upstream feed/provider latency and city-scale
load. Alert decisions run in the same completed local processing cycle; real
provider delivery and receipt by a person are not measured.

The launcher, built interface, fixture, pinned dependency records and offline
API reference are included. `scripts/package_release.py --verify` validates
all packaged checksums and runs the extracted source against a new SQLite
database, using the existing interpreter's installed dependencies. Its result
and archive SHA-256 are supplied next to the release ZIP in `outputs/releases/`.
This is separate from a fresh online dependency installation.

The recorded [GitHub Actions run](https://github.com/Godavenger/floodline-caa/actions/runs/42984005876)
passes backend dependency installation, all 44 backend tests, npm ci, the
production build and both-theme browser acceptance on a fresh Ubuntu runner
with Python 3.12 and Node 24. `outputs/evidence/github-actions.json` records its
commit, result and scope. Windows launcher checks remain a separate local
record; another member's clean setup and team rehearsal still need completion.

## Windows startup acceptance

Startup errors previously let the batch window close before the user could
read them. The start.bat wrapper now retains an interactive failure window,
reports the error and writes a transcript under .runtime/launcher-logs/.
The start.cmd alias shares this behavior. The bundled interface is used by
default, missing Python dependencies trigger setup, and an occupied default
port selects the next free port. Browser opening waits for API readiness.

Seven isolated launcher checks pass, covering real HTTP/asset startup from
another folder with spaces and Node blocked, the start.cmd alias, SQLite
backup/data preservation, automatic/default and explicit port conflicts,
missing interface guidance, invalid settings and first-install failure with
pip network access disabled. A separate v0.1.0 real interactive console check confirms
that the failure prompt waits for Enter and then exits with code 1.

The v0.1.1 launcher checks for a missing bundled interface with -SkipBuild before
probing or installing Python dependencies. This keeps rebuild guidance available
even when dependency imports are slow; the full seven-check suite passes after
the change.

Evidence: `outputs/evidence/launcher-acceptance.json`, `launcher-tests.txt` and
the dated baseline `launcher-interactive-check.json`. The refreshed archive verification also runs
its extracted start.bat from an unrelated folder. Successful dependency checks
reuse installed packages; a successful fresh online installation remains open.

## Remaining evidence gates

No real historical labels, city coverage, calibration, field validation or
human usability results are claimed. The candidate is unpromoted: at its
chosen threshold it flags all 138 held-out synthetic rows, including 40 false
positives. The rainfall-only comparison misses 12 positive rows and produces
eight false-positive rows. These are correlated synthetic decision rows,
not independent events or distinct delivered alerts.

PostgreSQL/PostGIS and container configuration are supplied but untested on
this machine. Real feeds, hosted deployment, multi-worker coordination and
external notifications remain later work. Team names, peer review, reflections,
deadline, consenting usability testers and a fluent local-language reviewer
must be recorded by the team; automated browser checks do not replace them.
The [completion checklist](REMAINING_TASKS.md) records each submission task,
owner and evidence needed to close it. The public GitHub release remains a
synthetic demo prerelease until the team completes its submission sign-off.
