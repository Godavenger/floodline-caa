# API contracts

All application endpoints use the /api prefix. The offline /docs reference and
generated /openapi.json are the schema authority. JSON requests use
Content-Type: application/json. Every write requires X-Floodline-Client: web
and an allowed/same origin. Browser cookies carry authorization.

## Read and action endpoints

| Endpoint | Access | Response / behaviour |
| --- | --- | --- |
| GET /api/health | Public | Version, synthetic mode, storage adapter, worker state |
| GET /api/clock | Public | Demo time, scenario and display timezone |
| GET /api/dashboard | Public | GeoJSON, cells, wards, risks, roads, public reports and active hazards |
| GET /api/areas, /api/network | Public | Versioned WGS84 geometry and directed edge references |
| GET /api/risk?area_id=C2 | Public | Issue/expiry, relative index, evidence support and reasons |
| GET /api/sources | Public | Source provenance, units and latest available observation time |
| GET /api/observations?area_id=C2 | Public | Only records observed and received by current demo time |
| GET /api/reports | Public / authorized | Public verified evidence; moderators see the review queue |
| GET /api/reports?mine=true | Resident | Owned pending/reviewed evidence |
| POST /api/reports | Resident | Validated, private pending report; HTTP 201 |
| PATCH /api/reports/{id} | Owner | Correct a pending description |
| DELETE /api/reports/{id} | Owner | Withdraw owned text/image evidence |
| POST /api/reports/{id}/image | Owner, pending | Multipart field image; clean private image |
| GET /api/reports/{id}/image | Owner / moderator / explicitly published | Controlled image response; private outsiders receive 404 |
| POST /api/reports/{id}/moderate | Moderator | Audited verification/rejection/duplicate/resolution |
| POST /api/routes | Public | Directed geometry, cost, current exclusions or explicit unavailable status |
| GET/POST /api/subscriptions | Resident | Owned active subscriptions / explicit consent |
| DELETE /api/subscriptions/{id} | Owner | Withdraw consent and cancel queued delivery |
| GET /api/alerts | Resident | Owned delivery history and evidence_current indicator |
| GET /api/evaluation | Public | Separate software experiment; candidate_promoted=false |

## Sessions and operations

| Endpoint | Purpose |
| --- | --- |
| GET /api/auth/session | Current resident/moderator role |
| POST /api/auth/guest | Start or retain an anonymous resident session |
| POST /api/auth/login | Moderator username/password; separate admin cookie |
| POST /api/auth/logout | End moderator access, preserving resident ownership |
| GET /api/admin/operations | Counts, quarantine, jobs, failed sends and audit |
| POST /api/admin/ingest | Validate and transactionally process observation records |
| POST /api/admin/cycle | Process current evidence without fabricating freshness |
| POST /api/admin/scenarios/{name} | normal, storm, outage or recovery |
| POST /api/admin/delivery-fault | Set a bounded simulated failure count |

Operations endpoints require moderator authorization.

## Request examples

Submit an observation after starting a resident session:

~~~json
{
  "description": "Synthetic demo: standing water affects this mapped junction.",
  "severity": "water_on_road",
  "observed_at": "2026-11-11T08:32:00Z",
  "longitude": 88.3475,
  "latitude": 22.571
}
~~~

Use GET /api/clock for the current demo timestamp; observations are accepted
from the last 24 demo hours, with a five-minute future tolerance.

Moderate a corroborated observation:

~~~json
{
  "status": "verified",
  "reason": "Reviewed the synthetic location, time and mapped road impact.",
  "road_edge_ids": ["road-n3-1-n4-1"],
  "ttl_minutes": 120,
  "privacy_reviewed": false,
  "publish_image": false
}
~~~

Subscribe:

~~~json
{"ward_id": "C", "channel": "in_app", "consented": true}
~~~

Route:

~~~json
{
  "start": {"longitude": 88.328, "latitude": 22.571},
  "end": {"longitude": 88.354, "latitude": 22.571}
}
~~~

## Errors and result meanings

Validation failures return a detail field with HTTP 422; invalid/missing
sessions return 401, forbidden moderator access 403, unavailable private/owned
records 404, incompatible report transitions 409, oversized uploads 413 and
request limits 429. Missing frontend builds return a helpful HTTP 503.

Routes use an ordinary result with status available, unavailable,
outside_pilot or unsnappable; a no-route result never restores excluded edges.
Null risk indices mean unknown. No endpoint returns a validated flood
probability. A sent alert records simulated adapter acceptance, not human
receipt or reading. Old alert records can remain visible while their evidence
is explicitly no longer current.
