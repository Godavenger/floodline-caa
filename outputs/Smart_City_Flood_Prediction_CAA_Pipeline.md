# Smart City Flood Prediction and Community Alert Platform

Detailed implementation pipeline for a six-person CAA project team.

Based on `project description.docx`, item 3. Proposed duration: eight weeks. Team members are labelled M1–M6 until names are assigned. The pilot city, data access and course deadline remain to be selected. All numerical thresholds, budgets and performance gates are proposed planning targets, not measured results.

<!-- PAGE -->
# Project brief and scope

## What the supplied description asks for
Build a platform that analyses environmental and geographical information to identify areas vulnerable to urban flooding. The expected outcome is a **prototype map and risk-analysis platform**, with predictions validated against available historical data and alerts that clearly communicate uncertainty.

<!-- widths: 0.26, 0.46, 0.28 -->
| Brief requirement | Planned implementation | Evidence for assessment |
| --- | --- | --- |
| Rainfall and water levels | Timestamped weather adapters plus a historical replay or optional sensor feed. | Source register, sample data and ingestion logs. |
| GIS flood-risk visualisation | Interactive map combining risk cells, ward boundaries, roads and evidence. | Working map with legend, timestamps and source details. |
| Predictive modelling | Historical event labels; rainfall baseline; one compact ML model if data supports it. | Reproducible temporal evaluation and error analysis. |
| Community waterlogging reports | Image, location, observation time and moderation status. | Complete submit–review–publish workflow. |
| Alerts and route suggestions | Area subscriptions; traceable alerts; routes excluding verified active road hazards. | Alert lifecycle and rerouting demonstrations. |
| Limited data and uncertainty | Explicit missing-data states, provenance and calibrated likelihood only when justified. | Stale-feed test and understandable uncertainty messages. |

## Proposed MVP boundary
- Select **one urban catchment covering roughly 3–5 wards**. Adjust the boundary to available evidence and keep routing inside a small study area.
- Use 250 m analysis cells only where source resolution supports them; otherwise use coarser cells or wards and state the resolution limit.
- Aim for a **next-three-hour flood-occurrence forecast**, refreshed every 15 minutes when new data exists. Confirm feasibility in Week 2 before committing to that horizon.
- Deliver a resident view, an administrator view and a reproducible local demonstration. IoT hardware, mobile apps and city-wide expansion are optional extensions.

> **Scope gate:** If trustworthy event labels or adequate time resolution are unavailable, deliver a susceptibility map and threshold-based warning prototype. Present historical replay and simulated data separately, and record that predictive accuracy could not be established.

## Why it is interdisciplinary
**CSE** supplies the application and data pipeline; **civil engineering** informs drainage and road exposure; **geography** supplies GIS analysis; **meteorology** informs rainfall interpretation; **disaster management** shapes clear, actionable communication.

<!-- PAGE -->
# End-to-end implementation pipeline

The core workflow converts evidence into a geographically specific risk update. Every stage produces an inspectable artifact, so a failed feed or uncertain prediction can be traced to its source.

[PIPELINE]

## How one processing cycle works
1. A scheduler fetches new observations or advances a historical replay. Each record carries observation time, receipt time, source and quality status.

2. Valid records are stored and joined to the study area. Features are calculated using information available at the prediction issue time only.

3. A versioned baseline or model writes a risk record containing its area, forecast window, reason, evidence freshness and uncertainty status.

4. The map refreshes. Alert rules check subscribed areas and recent deliveries. Routing excludes active verified hazard segments and explains remaining uncertainty.

5. New community evidence enters moderation. Verified outcomes support a later evaluation run; they do not automatically retrain the live model.

> **Two linked streams:** Prediction uses environmental data to estimate future risk. Community reports describe observed conditions. Show them together while keeping their meanings, timestamps and verification states distinct.

~ M1–M6 are the six member assignments defined on the next page. Recompute on new evidence; a 15-minute scheduler does not make an hourly source more current.

<!-- PAGE -->
# Work allocation for six people

Each member owns one substantial module, its documentation and its component tests. Suggested commitment: **6–8 hours per person per week for eight weeks**, or 288–384 team hours. Replace the member labels with names when the team is formed.

<!-- widths: 0.19, 0.48, 0.33 -->
| Member and role | Primary work and accountable deliverables | Main handoff and completion evidence |
| --- | --- | --- |
| **M1 — Data and requirements** | Choose pilot with team; inventory sources; collect rainfall, levels and historical events; create data dictionary, adapters and quality checks. Coordinate scope decisions. | Clean, versioned observations and event ledger to M2/M3; adapter contract to M4. Re-run from raw files and explain missingness. |
| **M2 — GIS and routing** | Prepare boundaries, terrain, drainage and OSM roads; build spatial joins and feature layers; map verified hazards to road edges; implement route exclusions. | GeoJSON and spatial features to M3/M5; route service to M4. Show correct joins and a route avoiding a seeded closure. |
| **M3 — ML and evaluation** | Define target with M1; construct labels; build baselines and one candidate model; prevent leakage; choose thresholds; quantify errors and uncertainty. | Versioned prediction function to M4; model card and evaluation report to all. Reproduce held-out results or document data limits. |
| **M4 — Backend and integration** | Define API schemas; build database migrations, access roles, upload handling, report moderation and service integration; manage application error states. | Working endpoints to M5/M6; secure data and image access. Run API and permission checks against one shared fixture. |
| **M5 — Frontend and usability** | Build map, legend, filters, evidence panel, report form, subscriptions and admin review screens; support mobile use and accessible messages. | Complete resident/admin flows using M4 APIs. Demonstrate keyboard operation and accurate handling of stale or unknown data. |
| **M6 — Alerts, QA and deployment** | Implement alert rules and delivery adapter with M4; coordinate integration tests, deployment, run logs and the final demonstration. Track release readiness. | Alert history, test matrix, deploy/run guide and demo bundle. Show retries, deduplication, expiry and recovery from an outage. |

## Shared responsibilities and review
M1 and M3 review labels and leakage; M2 and M5 review map interpretation; M4 and M6 review alert delivery and operational failures. Each owner tests their module before handoff. M6 coordinates system QA rather than becoming the only tester.

**Completion rule:** A module is done when it runs from documented inputs, handles one realistic failure, passes its agreed checks and has been reviewed by another member. All six contribute to the report and can explain the full pipeline.

<!-- PAGE -->
# Work packages and integration contracts

Agree on interfaces before parallel implementation. Use a small shared fixture: two study cells, several rainfall observations, one historical flood event, one unverified report, one verified road closure and one stale feed.

<!-- widths: 0.09, 0.15, 0.31, 0.30, 0.15 -->
| ID | Owner | Work package and input | Output / definition of done | Depends on |
| --- | --- | --- | --- | --- |
| P1 | M1 + all | Interpret brief; inspect local evidence. | Signed-off scope, pilot boundary and source inventory. | Start |
| P2 | M1 | Read historical and current data. | Raw archive, clean schema, quality flags and event ledger. | P1 |
| P3 | M2 | Align boundaries, elevation and roads. | Validated spatial layers, cell IDs and routable graph. | P1 |
| P4 | M3 | Join P2/P3; define observable targets. | Baselines, model if feasible, historical evaluation and model card. | P2, P3 |
| P5 | M4 | Implement shared API and storage contracts. | Database, roles, risk/report/route endpoints and upload checks. | P1; then P2–P4 |
| P6 | M5 | Build UI against agreed fixtures. | Resident map, reporting and administrator review flows. | P1; then P5 |
| P7 | M6 + M2 | Connect risk decisions, subscriptions and road hazards. | Tested alerts and route exclusions exposed through P5. | P3–P6 |
| P8 | All; M6 leads | Run acceptance tests and package release. | Reproducible demo, evidence, report and contribution record. | P4–P7 |

## Minimum handoff contracts
- **Observation:** source ID, observed-at UTC, received-at UTC, location, variable, value, unit and quality flag. A unique source-record key prevents duplicate ingestion.
- **Spatial feature:** stable cell/ward ID, geometry version, source resolution, feature timestamp and missing-data indicators. Exchange map geometry as WGS84 GeoJSON.
- **Prediction:** area ID, issue time, validity window, score type, risk level, evidence status, reason codes and model/rule version. Unknown values remain explicitly unknown.
- **Report / road hazard:** private reporter reference, observation time, geometry, image reference, review state and expiry. A closure references specific road-edge IDs.
- **Alert:** area, trigger/risk version, message version, recipient subscription, expiry and delivery state. Use an idempotency key for each recipient and alert version.

## Team working rhythm
Use one repository, short feature branches and reviewed pull requests. Hold two short integration meetings each week, keep API examples in the repository, and run the shared fixture before merging a contract change. Maintain a decision log and an individual contribution log throughout.

<!-- PAGE -->
# Data sourcing and collection

**M1 leads; M2 checks spatial suitability; M3 checks modelling usefulness.** Choose sources after inspecting coverage, timestamps, licensing and actual access. A nearby station, satellite pixel or river gauge may not represent waterlogging on a specific street.

<!-- widths: 0.19, 0.34, 0.25, 0.22 -->
| Data | Candidate source and use | Collection plan | Key limitation |
| --- | --- | --- | --- |
| Rainfall / weather | IMD observations; NASA GPM IMERG; Open-Meteo where terms and coverage fit. | Obtain historical files and one feed adapter; retain product name and resolution. | Satellite/grid rainfall needs local validation; some products arrive late. |
| Water levels | Available CWC / India-WRIS or municipal records; optional bench sensor. | Record gauge location, units, datum and threshold source. | River level may poorly represent local drainage or road depth. |
| Terrain / drainage | Suitable public DEM, municipal drains and available land-cover layers. | Clip to pilot; record date, licence and horizontal/vertical resolution. | Coarse DEMs omit kerbs, culverts and small drains. |
| Roads / boundaries | OpenStreetMap and an authoritative ward layer when available. | Save dated extracts, road directions and map attribution. | Missing roads, uncertain boundaries and incomplete restrictions. |
| Historical floods | Municipal incident logs, verified event records and documented local evidence. | Build an event ledger with location, timing, provenance and confidence. | No report does not prove no flooding. |
| Community evidence | Consenting prototype participants or clearly marked demo submissions. | Image, map pin, observed time and structured severity description. | Duplicates, wrong locations and delayed reports require review. |

## Collection procedure
1. List candidate sources and inspect a small sample before coding an adapter. Confirm usable history, time interval, location coverage and permission to use the data.

2. Preserve original files in a read-only raw-data folder. Record file checksums, download time, source URL, units, licence and any processing assumptions.

3. Convert accepted records into a common schema. Quarantine invalid coordinates, impossible values and unit conflicts; never silently replace them with zero.

4. Schedule ingestion according to source availability. Retry transient failures, cache successful responses and expose the time of the last valid observation.

5. Prepare a labelled historical replay for the demonstration. If a source cannot be accessed, use documented sample data or a simulator and visibly mark its status.

> **Week 2 decision:** Proceed with prediction only if independent events, usable observation times and credible labels exist. Data availability determines the achievable forecast resolution and claim.

<!-- PAGE -->
# Cleaning, GIS and feature engineering

The output of this stage is a reproducible feature table indexed by **area ID and prediction issue time**. M1 owns temporal cleaning, M2 owns geographic preparation and M3 approves the final feature definitions.

## Step 1 — Clean and align observations
- Standardise rainfall in millimetres and level measurements in a documented unit and datum. Distinguish cumulative counters, interval totals and intensity; handle resets explicitly.
- Store time in UTC and display local time. Reconcile observation time with receipt time; a record received later must not appear in an earlier replay prediction.
- Deduplicate records, flag impossible changes and preserve gaps. Use only past information for any justified short-gap imputation, attach an imputation flag and set a maximum gap.
- Resample at a frequency supported by the original data. Hourly observations do not justify minute-level claims. Do not interpolate future observations into earlier feature rows.

## Step 2 — Prepare spatial layers
Validate geometries and coordinate systems, clip to the pilot and assign stable cell IDs. Use a suitable local projected CRS for distance, area and road snapping; export WGS84 for the web map. Document the DEM source, drainage assumptions and the date of the OSM extract.

<!-- widths: 0.26, 0.43, 0.31 -->
| Feature group | Candidate features available at issue time | Interpretation / caution |
| --- | --- | --- |
| Rainfall history | Past 1 h, 3 h, 6 h and 24 h accumulation; recent maximum intensity where resolution allows. | Missing coverage affects reliability; accumulation needs correct interval semantics. |
| Water-level trend | Latest valid level, rise over a prior interval and distance to a documented local threshold. | Relative gauge values cannot be treated as road-water depth. |
| Terrain / drainage | Elevation, slope, distance to mapped drains/water bodies and drainage density where reliable. | Proximity alone does not establish flood cause or protection. |
| Surface / exposure | Land-cover or imperviousness proxy; road class and population exposure when available. | Keep exposure separate from probability of flooding. |
| Evidence quality | Source age, missing fraction, imputed fraction and spatial-resolution flags. | Drives unknown/limited-support states as well as model diagnostics. |

## Step 3 — Produce a versioned feature dataset
Define every feature's unit, look-back window and availability rule. Fit imputers, scalers and encoders on the training portion only. Save feature code, geometry version, dataset fingerprint and split IDs alongside each experiment.

> **No hidden precision:** A coarse weather grid can support broad risk context; it cannot independently locate street-level flooding. Road exclusions require separate, current hazard evidence.

<!-- PAGE -->
# Prediction target and modelling plan

## Define exactly what the model predicts
The preferred target is: **Will a documented flood or waterlogging event occur in this analysis area during the next three hours?** At issue time t, features use information available by t; the label concerns the interval after t. Adjust the horizon only after inspecting event timing and source frequency.

<!-- widths: 0.20, 0.51, 0.29 -->
| Label state | Assignment rule | How it is used |
| --- | --- | --- |
| Positive | Credible, geolocated evidence places flooding in the target area and forecast window. Link the row to an event ID. | Train/evaluate subject to evidence quality. |
| Negative | A documented observation process or inspected record supports no flooding in that window. | Train/evaluate only where coverage is credible. |
| Unknown | Timing, location or observation coverage is insufficient. Absence of a report falls here by default. | Exclude from supervised labels; quantify the coverage gap. |
| Synthetic | Generated rainfall, labels or reports for development and demonstrations. | Test software behaviour; exclude from real-world accuracy claims. |

## Model development sequence
1. **Describe the dataset.** Count independent storms/events, observed areas, positive labels, credible negatives, unknowns and missingness. Repeated rows from one storm are not independent events.

2. **Implement baselines.** Evaluate a prevalence/persistence baseline where appropriate and an interpretable rainfall/level threshold rule. Thresholds must come from documented local guidance or be selected on training/validation data.

3. **Fit one compact candidate.** Start with logistic regression; compare a small random forest if justified. Use class weighting inside training and avoid unnecessary model complexity.

4. **Tune with temporal validation.** Select features, hyperparameters and operating thresholds without accessing the final test outcomes. Keep preprocessing inside the fitted pipeline.

5. **Package the chosen approach.** Save the feature schema, fitted artifact or rule configuration, version, input checks and a deterministic inference function for M4.

## Separate three different meanings
**Flood likelihood** estimates occurrence. **Impact/exposure** describes affected people, infrastructure or road segments. **Data support** explains whether available evidence is timely and adequate. Present them separately so a severe impact is not confused with a high probability.

> **Sparse-data fallback:** Produce a documented relative susceptibility index and observed threshold warnings. Call a hand-weighted score an index, not a probability, and do not claim validated forecasting from labels generated by the same rule.

<!-- PAGE -->
# Historical validation and uncertainty

**M3 leads evaluation; M1 audits event evidence; M6 repeats the frozen run.** The project description explicitly requires validation against available historical data. The final report should show the evidence behind its claims, including results that limit the approach.

## Evaluation design
- Prefer chronological train/validation/test blocks, for example 60/20/20 when data volume permits. Keep one storm's related observations together and purge overlapping target/look-back windows across boundaries.
- Tune on training/validation only. Reserve the most recent suitable events as the final test. If enough areas exist, add a held-out-area check and state whether it measures geographic transfer.
- Reconstruct what was available at each issue time. Use archived forecasts only if their original issue times are available; otherwise use an observation-only model.
- For very few events, use clearly described event-level backtesting and list the event count. Report uncertainty or descriptive results instead of presenting a fragile estimate as reliable city-wide accuracy.

<!-- widths: 0.27, 0.40, 0.33 -->
| Measure | Why it matters | What to report |
| --- | --- | --- |
| Recall and missed events | Detecting true floods is central to usefulness. | Confusion matrix, denominator and missed-event examples. |
| Precision / false alarms | Excessive alerts reduce trust. | Precision and false alerts per area/event period. |
| PR-AUC and class balance | Floods may be rare; accuracy can be misleading. | PR curve with test prevalence and comparison to baselines. |
| Lead time | Useful notice must precede the observed event. | Time from first qualifying alert to onset; late alerts separately. |
| Calibration | A displayed likelihood should match observed frequency. | Reliability plot/Brier score if sample size is adequate. |
| Spatial and event errors | Aggregate scores hide neighbourhood and storm differences. | Error map, event breakdown and source-coverage limits. |

## Decide how uncertainty appears in the product
Only display a numeric probability if validation supports its interpretation. Otherwise show a named risk level or relative score with its limitations. Define **adequate, limited or insufficient data support** using documented freshness, completeness and coverage rules; these are evidence indicators, not confidence intervals.

For enough independent events, estimate metric intervals by resampling events, not individual correlated rows. If the sample is too small, state the counts and instability directly.

> **Promotion gate:** Use the candidate model only if the held-out comparison supports improvement over the baseline at a tolerable alert burden. If not, ship the more defensible baseline and include the negative result in the report. No accuracy percentage is promised in advance.

<!-- PAGE -->
# Architecture, database and APIs

Use a small modular application: **Python + FastAPI**, **PostgreSQL/PostGIS**, **GeoPandas + scikit-learn**, and **React + Leaflet**. A scheduled worker handles ingestion and inference; M2 can use OSMnx/NetworkX for the pilot road graph. Add MQTT only if a real or simulated IoT feed needs it.

[ARCHITECTURE]

## Storage design
<!-- widths: 0.29, 0.71 -->
| Entity group | Minimum content and relationships |
| --- | --- |
| Areas and observations | Versioned cell/ward geometry; source metadata; observed/received time; variable, value, unit and quality flag. |
| Events and risk runs | Evidence-backed event IDs; feature snapshot ID; model/rule version; issue/validity times; score type, risk and support status. |
| Reports and road hazards | Reporter kept private; image reference; geometry; observed time; review audit; verified road-edge IDs and expiry. |
| Subscriptions and alerts | Consented area/channel subscription; trigger reference; message/decision version; recipient delivery attempts, state and expiry. |

## API contracts to build first
- `GET /areas`, `GET /risk?area_id=...` and `GET /reports`: return filtered map data with provenance, timestamps and explicit unknown states.
- `POST /reports`: validate location/time/text and return a pending report ID. Use authenticated moderation to change its status and record a reason.
- `POST /subscriptions` and `DELETE /subscriptions/{id}`: manage opt-in area alerts with ownership checks. `GET /alerts` returns authorised history.
- `POST /routes`: accept start/end points; return route geometry, excluded hazard IDs, calculation time and caveats, or an explicit unavailable result.
- `GET /health`: expose service status without secrets. Operational logs record job IDs and errors, never access tokens or private images.

## Integration behaviour
Validate schemas at boundaries and use atomic writes for related risk/alert records. A slow prediction job must not block map or report requests. Keep API keys in environment configuration, provide a safe `.env.example`, and version database migrations with the application.

<!-- PAGE -->
# Community reports and moderation

**M5 owns the submission experience; M4 owns validation and review controls; M2 links verified hazards to roads.** Reports add local evidence but do not automatically become ground truth or public road closures.

## Resident submission workflow
1. Select a map location or deliberately share device location. Enter when the condition was observed, a short description and an optional structured severity description.

2. Attach an image for the evidence workflow. Offer a text-only fallback if upload/connectivity fails and label that report as lacking image evidence. Avoid requesting risky on-site measurements.

3. Validate location bounds, timestamp, length and file content. Decode/re-encode supported images, strip location-bearing EXIF metadata and enforce an initial 5 MB upload limit.

4. Store the submission privately as **pending**. Return a report ID and status. Show personal contact information only where strictly needed for administration.

<!-- widths: 0.20, 0.47, 0.33 -->
| Review state | Moderator action | Public / routing effect |
| --- | --- | --- |
| Pending / unverified | Check image relevance, location, time, duplicates and corroborating evidence. | May appear in a separate unverified layer; does not automatically block roads. |
| Verified | Record reviewer, reason, observed severity and affected geometry. | Publish evidence marker; create a bounded road hazard when justified. |
| Rejected / duplicate | Record reason and link a duplicate to its existing report. | Exclude from active hazards; retain an appropriate audit record. |
| Expired / resolved | Expire after configured TTL or record verified resolution. Preserve history. | Remove active restriction. Expiry alone does not prove the road is clear. |

## Trust and privacy controls
Require moderator authentication and authorise every state change. Use request limits and duplicate checks to reduce spam. Keep raw uploads private, return controlled image URLs, obscure reporter identity and review images for faces or number plates before public use.

Choose a documented prototype retention policy, for example deleting unnecessary original uploads after 30 days and retaining only consented, de-identified evidence required for evaluation. Make subscriptions easy to withdraw and provide a simple report correction/deletion route.

> **Historical labels need separate review:** A moderated report can still have uncertain onset time or geography. M1/M3 must assess whether it is suitable for a specific training label; the backend must not add it to training automatically.

<!-- PAGE -->
# Alert decisions and communication

**M6 owns the decision rules and delivery adapter; M3 supplies model limits; M4 provides durable records; M5 presents the messages.** Demonstrate alerts with test accounts and one delivery channel before attempting multiple providers.

<!-- widths: 0.20, 0.45, 0.35 -->
| State | Trigger and decision | Community presentation |
| --- | --- | --- |
| Unknown | Required evidence is missing, too old or outside reliable coverage. | “Current conditions cannot be estimated reliably.” Retain last update visibly. |
| Low / monitor | Evidence is usable and the locally defined warning trigger is not met. | Show monitoring state; do not label an area guaranteed safe. |
| Elevated / high | Validated score/rule crosses its documented trigger, with supporting evidence. | Explain affected area, forecast window, evidence and a practical action. |
| Observed hazard | A current report/incident has been verified. | Clearly distinguish observed waterlogging from forecast risk. |
| Updated / expired | Severity, evidence or validity changes; a configured validity window ends. | Send meaningful updates; remove expired alerts without asserting all-clear. |

## Alert processing pipeline
1. Validate risk age and data support; select subscribers whose chosen area intersects the affected geometry. Store the decision and explanation before attempting delivery.

2. Apply deduplication and hysteresis: a separate clearance rule prevents repeated toggling near a threshold. A proposed 30-minute cooldown suppresses unchanged reminders; meaningful severity increases can bypass it.

3. Build a plain-language message with location, issue time, valid-until time, predicted/observed status, evidence limitation and suggested action. Use icons plus words, not colour alone.

4. Deliver through in-app alerts plus an email or SMS test adapter. Record queued/sent/failed/expired states; provider acceptance is not proof that a person read the message.

5. Retry transient failures with bounded backoff and an idempotency key. Stop retries after expiry and display delivery failures to administrators.

> **Example — simulated elevated-risk alert:** “Ward B: elevated waterlogging risk for the next 3 hours. Heavy recent rainfall is the main trigger. Data support is limited because the local level feed is stale. Avoid roads marked with current verified flood reports and check official local advisories. Issued 14:00 IST; valid until 17:00 IST.”

## Accessibility and authority
Prepare English plus one locally relevant language with human-reviewed wording. Keep the message readable on a small screen. Mark the project as a prototype, identify its source and distinguish its guidance from an official emergency order. Official contact information must be verified before inclusion.

<!-- PAGE -->
# GIS dashboard and route suggestions

## Resident map and administrator view
The resident view opens on the pilot area and makes four things immediately visible: **where the risk is, when it applies, what evidence supports it and what action is suggested**. M5 implements the interface with M2's layers and M4's APIs.

- **Base map and legend:** roads, study boundary and meaningful labels; retain OpenStreetMap and tile-provider attribution. Use an appropriate hosted/cached map source within its usage policy.
- **Risk layer:** cell/ward boundaries, risk words and a colour-accessible scale. Unknown areas use a distinct neutral pattern; show source resolution to avoid false street-level precision.
- **Evidence panel:** last observation time, prediction issue/expiry, data support, reason codes and source/model version. Predicted and observed information remain distinguishable.
- **Report layer:** separate verified and unverified markers, observed time and a privacy-reviewed image where available. Avoid showing reporter identity publicly.
- **Admin view:** pending reports, feed freshness, failed jobs, active hazards, alert delivery states and an audit trail. Keep moderation actions restricted to authorised users.

## Route-avoidance procedure
1. Build a directed road graph for the pilot with known one-way, access and travel-mode restrictions. Use distance as the initial cost unless reliable travel-time information exists.

2. Snap start/end positions to accessible nodes within a documented tolerance. Return a useful out-of-area or unreachable response when appropriate.

3. Join **current verified** hazard geometry to specific road segments. For the first prototype, exclude these edges; use a conservative spatial tolerance and inspect uncertain matches.

4. Run Dijkstra or A* on the filtered graph. Return the resulting geometry, known closures avoided, calculation time and any remaining data limitations.

5. If every connection is blocked, return **“No route avoiding the currently verified hazards could be found.”** Do not silently restore blocked edges. Recompute when a hazard or its validity changes.

> **Route wording:** “This suggestion avoids currently verified flooded segments. Other hazards or missing reports may exist.” A coarse risk cell or expired report does not establish that a particular road is safe.

## Completion checks
Use a small graph with one closure, an alternative route, a disconnected destination, a one-way road and an out-of-boundary point. Verify every returned edge against active exclusions. M2 reviews geometry; M5 checks mobile readability, keyboard access and loading/empty/error states.

<!-- PAGE -->
# Eight-week execution plan

The schedule is a proposed baseline. Protect the **Week 2 data-feasibility gate** and **Week 6 complete-system demo**. If the course deadline is shorter, reduce optional hardware, channels and model variants before removing validation or failure handling.

<!-- widths: 0.12, 0.22, 0.22, 0.22, 0.22 -->
| Owner | Weeks 1–2 | Weeks 3–4 | Weeks 5–6 | Weeks 7–8 |
| --- | --- | --- | --- | --- |
| **M1** | Scope, source audit, event samples and dictionary. | Reproducible cleaning, feed adapter and event ledger. | Data replay, freshness tests and label review. | Freeze data, write limitations and demonstrate provenance. |
| **M2** | Pilot geometry, roads and DEM suitability. | GIS features, joins and first routable graph. | Road-hazard matching and route exclusions. | Spatial tests, final maps and routing evidence. |
| **M3** | Target, label feasibility and split plan. | Baselines and first candidate model. | Evaluation, threshold choice and inference artifact. | Frozen test run, error analysis and model card. |
| **M4** | Schemas, API examples and database setup. | Auth, risk/report endpoints and private uploads. | Integrate model, moderation, routes and subscriptions. | Permission/security checks, migrations and runbook. |
| **M5** | User flows, map sketch and fixture-driven screens. | Map, evidence panel and resident report form. | Admin review, alerts and responsive integration. | Usability fixes, screenshots and demo polish. |
| **M6** | Test plan, local environment and alert contract. | Rule engine, test delivery and CI checks. | Integration QA, retries, logging and deployment. | Acceptance tests, release package and demo rehearsal. |

## Weekly milestones and exit gates
1. **Week 1 — Define:** choose pilot, agree MVP, assign names, inspect sources and commit shared contracts/fixtures.

2. **Week 2 — Prove feasibility:** document usable events and timestamps; choose forecasting or the explicitly labelled fallback. Show an initial map and API skeleton.

3. **Week 3 — Build the backbone:** raw data → cleaned observations → GIS features works; report creation and a basic map run together.

4. **Week 4 — Establish a baseline:** replay produces risk records; baseline evaluation exists; report moderation works end to end.

5. **Week 5 — Integrate action:** model/baseline output drives the map and test alert; verified hazards change a route.

6. **Week 6 — Demonstrate the whole flow:** run a realistic flood scenario and an outage scenario. Freeze features and fix integration gaps.

7. **Week 7 — Validate and harden:** complete held-out evaluation, usability checks, permission tests and final bug fixes.

8. **Week 8 — Submit:** reproduce on a clean setup, freeze the release, finalise the report and rehearse all six contributions.

<!-- PAGE -->
# Testing and acceptance checklist

Component owners create focused tests; M6 coordinates end-to-end evidence. Record the dataset version, environment and outcome for every acceptance run. The proposed engineering gates below are project targets; model performance must be reported from actual evaluation.

<!-- widths: 0.18, 0.17, 0.39, 0.26 -->
| Area | Owner | Meaningful test | Acceptance evidence |
| --- | --- | --- | --- |
| Data integrity | M1 | Duplicate observation, unit conflict, negative rainfall, missing interval and delayed receipt. | Duplicates ignored; invalid data flagged; gaps remain visible. |
| Spatial correctness | M2 | Misprojected layer, boundary edge, invalid geometry and road snap. | Correct documented CRS and joins; uncertain matches surfaced. |
| Model validity | M3 | Frozen temporal/event split, leakage audit, baseline comparison and repeat run. | Same inputs reproduce results; no synthetic examples in real accuracy figures. |
| API / access | M4 | Invalid payload, unauthorised moderation, another user's record and oversize/non-image upload. | Requests rejected correctly; no private identity or image exposure. |
| Product usability | M5 | Report submission, alert interpretation and finding evidence on phone/keyboard. | Five consenting testers; target at least 4/5 complete core tasks unassisted; note sample limits. |
| Alert delivery | M6 | Repeated trigger, failed provider, severity increase, expiry and stale input. | One unchanged alert per recipient/window; bounded retries; no expired sends. |
| Routing | M2 + M4 | Blocked edge, one-way route, disconnected graph and expired hazard. | No active excluded edge in a returned route; explicit no-route response. |
| System recovery | M4 + M6 | Feed outage, worker crash, database restart and historical replay. | Map shows freshness; replay resumes without duplicate records or alerts. |

## Performance and accessibility targets
On the recorded demo setup, target a typical cached map response under 3 seconds and a new alert decision within 60 seconds of a completed risk record. These exclude upstream data latency and external delivery time. Measure a small stated concurrency, such as 10 test clients, without implying city-scale readiness.

Use clear focus states, labelled controls, readable contrast, non-colour risk labels and text alternatives for map-only information. Review one local-language alert with a fluent reader.

> **Release gate:** All core user flows and data-limitation states must work. Close issues that produce misleading risk, expose personal information or return a route through an active excluded edge. Report any remaining limitation explicitly in the submission.

<!-- PAGE -->
# Deployment, budget and project risks

## Reproducible deployment pipeline
**Reviewed change → automated checks → local/staging build → database migration → smoke test → tagged demo release.** M4 owns application configuration; M6 owns the runbook. Use a local deployment as the baseline; a small hosted instance is optional if time, access and budget permit.

Provide setup instructions, pinned dependencies, a safe configuration template, seeded demo data and one command/script to start the services. Keep historical replay separate from live mode and display the active mode. Back up the database before migrations and retain a known-good model/rule artifact for rollback.

## Operating checks
Track last successful ingestion, rejected-record counts, inference duration, unresolved jobs, active hazard expiry and alert delivery failures. Mark stale predictions visibly; do not manufacture a fresh issue time when no new evidence exists. Test a restore once using the demo dataset.

<!-- widths: 0.29, 0.24, 0.47 -->
| Item | Planning allowance | Assumption |
| --- | --- | --- |
| Local software prototype | ₹0 incremental software cost | Existing laptops/connectivity; permitted open-source tools and datasets. |
| Optional hosted demo | Cap at ₹1,500/month | Verify current provider terms; local deployment is the fallback. |
| Optional notification trial | Cap at ₹500 for the demo | Use test/sandbox delivery where available; confirm actual provider charges. |
| Optional bench IoT node | Allow ₹2,000–₹4,000 | ESP32, suitable sensor, power and enclosure; local quotes required. |

~ These are budgeting assumptions, not supplier quotations. Paid datasets, existing equipment, internet and field installation are not included. Hardware is not required by the project brief.

<!-- widths: 0.28, 0.50, 0.22 -->
| Project risk | Mitigation / fallback | Owner |
| --- | --- | --- |
| Insufficient labels or history | Apply Week 2 scope gate; evaluate transparently; deliver susceptibility/threshold mode if needed. | M1 + M3 |
| Poor spatial resolution | Coarsen the prediction unit and show uncertainty; require independent road evidence. | M2 + M3 |
| Feed/provider outage | Cache data, show staleness, retry with limits and use a labelled replay for demo continuity. | M1 + M6 |
| Misleading reports or alerts | Moderate evidence, audit decisions, deduplicate and expire records clearly. | M4 + M6 |
| Integration or workload slip | Use shared fixtures early; freeze features in Week 6; share component testing. | All six |

<!-- PAGE -->
# Demonstration and submission package

## Ten-minute demonstration with six speakers
Use a declared historical replay or synthetic scenario. Do not present the demonstration's invented conditions as a live city emergency or as evidence of predictive accuracy.

<!-- widths: 0.16, 0.13, 0.71 -->
| Time | Speaker | Action and explanation |
| --- | --- | --- |
| 0:00–1:15 | M1 | Introduce the brief, pilot and data limits. Show raw evidence, cleaning and the event ledger. |
| 1:15–2:30 | M2 | Explain GIS layers, spatial resolution and the road graph; identify an initially available route. |
| 2:30–4:00 | M3 | Run the baseline/model; show held-out results, forecast validity and why uncertainty is displayed. |
| 4:00–5:30 | M4 | Submit and review a report; show validation, role permissions and the stored audit trail. |
| 5:30–7:00 | M5 | Show the resident map, evidence panel, verified hazard and updated route on a narrow screen. |
| 7:00–10:00 | M6 | Trigger one test alert, repeat to prove deduplication, simulate stale data and show recovery plus the release checklist. |

## Deliverables to submit
- **Project report:** problem statement, brief alignment, literature/source review, scope, interdisciplinary reasoning, architecture, methods, results, limitations and future work.
- **Application source:** versioned code, dependency files, database migrations, configuration template, deployment instructions and an identifiable release tag.
- **Data documentation:** source/licence register, dictionary, feature definitions, event ledger, split manifest and anonymised sample/replay data where permitted.
- **Model evidence:** baseline and candidate results, saved artifacts/configuration, error maps, model card and a clear explanation of any fallback used.
- **Product evidence:** map/report/moderation/alert/route screenshots, accessible message examples, integration test log and reproducible demonstration script or recording.
- **Team evidence:** named responsibility matrix, task history, reviewed contributions and a short individual reflection explaining each member's decisions and learning.

## Suggested report narrative
Move from the local flooding problem to data limitations, system design, implementation, historical evaluation and community usefulness. Separate observed results from planning targets. Use failure examples to explain what the prototype can and cannot support.

> **Final check:** Another team member should be able to recreate the demo from the README and sample data, identify the active model/rule version, reproduce the stated evaluation and explain the six-person division without relying on one person's laptop setup.

<!-- PAGE -->
# References and first-week checklist

## Source of the project requirements
**Provided document:** `project description.docx`, item 3, “Smart City Flood Prediction and Community Alert Platform.” This pipeline follows its environmental-data collection, GIS mapping, historical modelling, community evidence, alerting/routing and uncertainty requirements. It does not assume an additional course rubric.

## Official implementation and data references
The links below are starting points for source selection and implementation. Confirm current availability, local coverage, terms, quotas and resolution during the data audit; inclusion here does not imply guaranteed open access to every dataset.

<!-- widths: 0.34, 0.66 -->
| Reference | Relevance to this pipeline |
| --- | --- |
| [India Meteorological Department](https://mausam.imd.gov.in/) | Official meteorological information and routes to appropriate rainfall products. |
| [India-WRIS](https://indiawris.gov.in/wris/) | Candidate water-resource and gauge information; check station relevance and access. |
| [NASA GPM / IMERG](https://gpm.nasa.gov/data/imerg) | Satellite precipitation products; inspect latency, resolution and product version. |
| [Open-Meteo documentation](https://open-meteo.com/en/docs) | A candidate weather API; distinguish current, historical and forecast products. |
| [OpenStreetMap copyright](https://www.openstreetmap.org/copyright) | Data licence and attribution obligations for road/base-map use. |
| [GeoPandas documentation](https://geopandas.org/en/stable/) and [PostGIS documentation](https://postgis.net/documentation/) | Geometry processing, coordinate systems, spatial queries and storage. |
| [scikit-learn model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | Classification metrics and evaluation methods; apply temporal/event-aware splits. |
| [FastAPI documentation](https://fastapi.tiangolo.com/) and [Leaflet documentation](https://leafletjs.com/reference.html) | API implementation and interactive web mapping. |
| [OSMnx documentation](https://osmnx.readthedocs.io/en/stable/) | Creating and analysing a road network for the bounded routing prototype. |
| [OWASP file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Validation and safe handling of community image uploads. |

## Start here: first-week checklist
1. Replace M1–M6 with names and agree weekly availability and the actual course deadline.

2. Select the pilot using flood relevance, accessible evidence and a manageable boundary.

3. Audit sample rainfall, level, map and event data before promising model accuracy or resolution.

4. Commit the scope, data dictionary, API examples, shared fixture and task board.

5. Book the Week 2 feasibility review and Week 6 complete-system demonstration.

> **Project outcome:** A working, explainable prototype that connects environmental data, geographic context and reviewed community evidence to useful risk information, transparent alerts and route suggestions that account for known hazards.
