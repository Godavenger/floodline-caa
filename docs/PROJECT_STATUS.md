# Pipeline implementation status

This file tracks the delivered application against the supplied eight-week
blueprint. The user approved a synthetic pilot and a map/evidence-first
dashboard on 11 November 2026. Original planning documents remain in `outputs/`.

| Package | Owner | Work | Status |
| --- | --- | --- | --- |
| P1 | M1 + all | Scope, pilot, source inventory and contracts | Implemented for the approved synthetic scope; see PRODUCT.md, source register and API contracts |
| P2 | M1 | Raw archive, clean observations and event ledger | Implemented; checksummed raw fixture, deduplication, quarantine, receipt-time features and synthetic event ledger |
| P3 | M2 | Versioned GeoJSON, spatial features and directed graph | Implemented; nine cells, three wards, projected distances and 61 directed edges with tested exclusions |
| P4 | M3 | Baseline, temporal evaluation and model card | Implemented fallback; frozen synthetic event split and an explicitly unpromoted logistic candidate |
| P5 | M4 | Database, access, uploads and APIs | Implemented and tested in SQLite mode; PostgreSQL/PostGIS preparation remains untested |
| P6 | M5 | Resident map, reporting and administrator flows | Implemented; map/evidence, reports, routes, alerts and moderation pass browser acceptance at four widths |
| P7 | M6 + M2 | Alerts and verified hazard routing | Implemented; consent, deduplication, retries, expiry, unknown states and verified road exclusions tested |
| P8 | All | Acceptance evidence, runbook and demo package | Local synthetic demo ready: 44 backend tests, 13 browser checks, 7 Windows launcher checks, both review fixes resolved; report, design record and checksum package supplied |

The Week 2 data-feasibility gate is **fallback**: no real historical labels are
available. A synthetic software evaluation must remain separate from historical
predictive accuracy. The real-pilot gate stays open for later evidence.

## Release records

- [Acceptance evidence](ACCEPTANCE.md) records actual checks and their scope.
- [Project report](PROJECT_REPORT.md) and `outputs/Floodline_Project_Report.pdf`
  explain the implementation, synthetic results and limits.
- [Runbook](DEMO_RUNBOOK.md) gives local setup, replay, rollback and the six-speaker demo.
- `scripts/package_release.py --verify` freezes the source/demo ZIP, checksums
  every entry and starts the extracted application with a separate database.

## Gates requiring real evidence or team work

The synthetic implementation is available for demonstration. It does not close
historical forecasting validation, real pilot/source licensing, field GIS
review, five-person human usability testing or local-language review. M1–M6
names, peer sign-offs, actual hours, individual reflections and the course
deadline remain for the team in [the contribution record](TEAM_CONTRIBUTIONS.md).
An actual Git release tag, PostgreSQL acceptance, hosted deployment and real
notification providers require their own setup and evidence.
