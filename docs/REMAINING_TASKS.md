# Completion checklist

Reviewed against the supplied assignment, item 3, and the P1–P8 pipeline on
11 November 2026. The working scope is an explicitly synthetic prototype.
The source is published at https://github.com/Godavenger/floodline-caa.

The map, observation pipeline, threshold baseline, separate model experiment,
private image reports, authenticated review, route exclusions and consent-based
in-app alerts are implemented. Light, Dark and System appearance are implemented.
Submission still needs the human evidence below. Historical forecasting accuracy
is not established by the synthetic tests.

## Required before team submission

| ID | Task | Owner | Evidence that closes it | Status |
| --- | --- | --- | --- | --- |
| S1 | Confirm the course deadline and acceptance of the synthetic fallback | M1 + all | Record the actual deadline and the instructor/team scope decision; retain the data limitation in the report | Pending team input |
| S2 | Assign the six roles and complete contribution records | All six | Names, actual hours, inspectable work, six peer reviews with dates, and individual reflections in TEAM_CONTRIBUTIONS.md | Pending team input |
| S3 | Run human usability and accessibility checks | M5 + M6 | Five consenting testers complete reporting, interpreting an alert and finding map evidence; record actual success, errors and fixes. The proposed 4/5 target is a target. Include keyboard use and a real phone in both themes | Pending human testing |
| S4 | Review one relevant local-language alert | M1 + M5 + M6 | Select the language, draft the alert with uncertainty and expiry, obtain a fluent reader's review and record the approved wording | Pending language and reviewer |
| S5 | Reproduce and rehearse the demo as a team | M4 + M6 + all | Another member follows the README on a clean setup, reproduces the evaluation and completes the ten-minute runbook; every member explains their handoff and a failure case | Pending team rehearsal |
| S6 | Finalize the submission report and release | All six | Add team evidence, actual results, limitations and any course-specific requirements; sign off one release and its checksum. The published synthetic demo is a technical checkpoint | Pending team sign-off |

The supplied brief asks for a prototype map and risk-analysis platform, with
predictions validated against available historical data. The supplied pipeline
permits a documented susceptibility/threshold fallback when trustworthy history
is absent. S1 confirms that this fallback meets the team's assessment requirements.

## Required to claim a real pilot or validated forecasting

| ID | Task | Owner | Evidence that closes it |
| --- | --- | --- | --- |
| R1 | Select a real catchment and obtain usable, licensed inputs | M1 + M2 | Real ward boundaries, rainfall and gauge coverage, units, observation/receipt times, access terms, licences and a versioned raw archive |
| R2 | Validate the real GIS and road network | M2 | Check projections, terrain/drainage resolution, joins, one-way roads, locations and hazard-to-edge matches against local evidence |
| R3 | Build a trustworthy historical event ledger | M1 + M3 | Independently reviewed positive and supported negative events, uncertainty states and evidence references; unknown conditions remain unknown |
| R4 | Run historical evaluation and a model promotion decision | M3 | Event/time-separated holdout, leakage checks, baseline comparison, false/missed alarms and lead time. Establish calibration before displaying probabilities; promote a candidate only with supporting evidence |
| R5 | Validate communication and routes in the actual locality | M2 + M5 + M6 | Local reviewer/tester evidence for alert interpretation, freshness, routing limits and real place names |

The present logistic candidate remains unpromoted. At its selected threshold it
flags all 138 held-out synthetic rows, including 40 false positives. These rows
are software experiment results and do not establish real flood prediction.

## Environment gates and optional extensions

- PostgreSQL/PostGIS migrations and container configuration are supplied but
  untested on this machine, where Docker and psql are unavailable. Run their
  migration, API, spatial and restart checks before choosing that deployment.
- A hosted application needs its own configuration, credentials, backups,
  service monitoring and multi-worker coordination tests. GitHub publication
  provides source and a downloadable demo; it does not host the FastAPI app.
- SMS/email delivery needs a real provider, recipient consent and delivery,
  retry and expiry evidence. The current adapter is simulated and sends in-app
  demo records.
- IoT sensors, native mobile apps and city-wide expansion are optional in the
  supplied MVP. They do not block the approved local synthetic prototype.

## Working order

Complete S1 and S2 first, then schedule S3–S5 and close S6 after fixing the issues
they expose. Start R1–R5 only when moving beyond the synthetic scope. Record
results in [acceptance evidence](ACCEPTANCE.md) and the
[contribution record](TEAM_CONTRIBUTIONS.md); use the [runbook](DEMO_RUNBOOK.md)
for the reproducibility and rehearsal steps.
