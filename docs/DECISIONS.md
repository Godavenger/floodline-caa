# Decision log

| Date | Decision | Reason and evidence |
| --- | --- | --- |
| 2026-11-11 | Start application work at P1/P2 rather than regenerate the blueprint. | The workspace has the completed pipeline but no application code. |
| 2026-11-11 | Use an explicitly synthetic pilot. | The user selected this option. Real city, observations and historical labels have not been supplied. |
| 2026-11-11 | Apply the Week 2 sparse-data gate immediately. | No trustworthy event ledger is present. Ship a susceptibility/threshold prototype, record historical accuracy as not established. |
| 2026-11-11 | Keep the specified FastAPI and React/Leaflet stack. | The pipeline defines this implementation contract. |
| 2026-11-11 | Support SQLite for the default local run and PostgreSQL/PostGIS for deployment. | Python dependencies are available locally; Docker/PostgreSQL are not available on this machine. Both adapters share migrations and service behavior; record PostgreSQL validation separately. |
| 2026-11-11 | Deliver alerts in-app through a simulated adapter. | Demonstrates consent, decision logging, idempotency, retries and expiry without contacting real recipients. |
| 2026-11-11 | Lead with the map and ward evidence. | The user selected this task priority; Reports, Routes, Alerts and Evidence review have separate screens. |
| 2026-11-11 | Keep the logistic candidate unpromoted. | The synthetic held-out comparison exposes a higher false-positive burden; no independent historical labels support promotion. |
| 2026-11-11 | Separate evaluated and unknown cells in summaries. | The final review found that an all-unknown feed must lead with unavailable-data wording rather than a zero-warning count. |
| 2026-11-11 | Validate the local release from an isolated extraction. | Checksums and a new database verify the shipped files without copying resident sessions, private uploads or installed dependencies. |

Numerical thresholds in the synthetic fixture are demonstration configuration,
not local meteorological guidance. Team assignments remain M1-M6 until names
are provided.
