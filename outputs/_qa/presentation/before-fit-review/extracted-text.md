<!-- Slide number: 1 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\hero.jpg](background_1.jpg)
CAA PROJECT PRESENTATION

FLOODLINE

![Layers](s01_cover_wordmark_icon_4.jpg)
From rainfall
to local decisions.
Smart City Flood Prediction
& Community Alert Platform

SYNTHETIC PILOT  /  v0.1.1
12 November 2026

9 analysis cells

![MapPinned](s01_cover_context_icon_73.jpg)
Evidence at area level

Review before action

![ShieldCheck](s01_cover_context_icon_77.jpg)
Reports → verified road evidence

A3
B3
C3

A2
B2
C2

A1
B1
C1

INVENTED GEOGRAPHY  /  3 WARDS
01  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Floodline — From rainfall to local decisions
Suggested speaking time: 30 seconds.

MAIN POINT
Floodline connects environmental context and reviewed community observations to understandable local actions.

PRESENTER SCRIPT
Introduce the project with its full assignment title. Floodline is the project name. Say early that this is a working synthetic pilot: the wards, rainfall, gauges and roads are development fixtures. We will show the data-to-action pipeline, the working interface, recorded checks, and the evidence required for a real pilot. Do not describe the displayed index as a probability.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
project description.docx, item 3; PRODUCT.md; docs/PROJECT_REPORT.md; docs/PROJECT_STATUS.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 2 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_2.jpg)
THE PROBLEM
Limited data has to become a useful local decision.
Residents and municipal reviewers need location, evidence and a supported next step.

01

![MapPinned](s02_question_0_icon_7.jpg)
Where is it vulnerable?
Rainfall, terrain and drainage need a shared geographic context.

02

![Eye](s02_question_1_icon_12.jpg)
What has been observed?
A report needs a time, a location and a reviewable account of conditions.

03

![Route](s02_question_2_icon_17.jpg)
Which action is supported?
Warnings and routes must reflect current, verified evidence.
Floodline brings these decisions into one traceable workflow.
02  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Limited data has to become a useful local decision.
Suggested speaking time: 40 seconds.

MAIN POINT
The assignment challenge is turning limited environmental data into timely, understandable information.

PRESENTER SCRIPT
Frame the problem through these three questions. A rainfall value alone cannot establish water on a particular street. A community report alone is not yet a verified road closure. The platform gives environmental evidence and reported conditions their own review paths, then joins them in an understandable map and action workflow. The disciplines are computer science, geography, civil engineering, meteorology and disaster management.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
project description.docx, item 3; PRODUCT.md; docs/PROJECT_REPORT.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 3 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_3.jpg)
SYSTEM CONCEPT
One platform. Two evidence streams.
Environmental warnings and observed road conditions keep their own meanings.

![CloudRain](s03_environmental_icon_6.jpg)
Environmental evidence
Rainfall + geographic features
→ interpretable warning rule

![Bell](s03_actions_icon_21.jpg)
Ward alerts
Consent-based
in-app delivery

![Route](s03_actions_icon_25.jpg)
Route suggestions
Exclude active
verified road hazards

![Map](s03_map_output_icon_16.jpg)
Shared map
Source • time • support

![ShieldCheck](s03_community_icon_10.jpg)
Community observations
Private report + moderator review
→ current road-edge hazard
03  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
One platform. Two evidence streams.
Suggested speaking time: 45 seconds.

MAIN POINT
Environmental risk context and moderator-verified road hazards are separate action streams.

PRESENTER SCRIPT
Walk left to right as the diagram builds. The environmental stream validates observations and combines recent rain with synthetic static susceptibility. The community stream keeps pending observations private and requires authenticated review before creating a bounded road restriction. Both streams appear in the map with source and validity information. Alerts use consent and a persistent delivery lifecycle. Routes exclude active verified edges; a coarse risk cell does not automatically close roads. Community reports do not automatically become model training labels.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/ARCHITECTURE.md; docs/API_CONTRACTS.md; docs/MODEL_CARD.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 4 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_4.jpg)
WORKING PROTOTYPE
The map is the starting point.
A real capture of the delivered interface, with ward evidence beside the geography.

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\dashboard.png](s04_actual_dashboard_image_6.jpg)
3
synthetic wards
9
analysis cells
61
directed road edges
04  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
The map is the starting point.
Suggested speaking time: 35 seconds.

MAIN POINT
The application leads with a map and evidence, rather than hiding the data behind a single score.

PRESENTER SCRIPT
Point out the map, the warning summary, the selected area and source-support panel. In the recorded initial state, three of the eight evaluated cells meet the warning rule and one cell is unknown. The geometry is invented, although its display uses WGS84 coordinates. The interface has resident reporting, routing, alerts, data/model details and moderator review. Light, Dark and System appearance are implemented. The screenshot is from the accepted dark-mode workflow and is a backup if the live demonstration is unavailable.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
.impeccable/review/desktop-dark.png; docs/ACCEPTANCE.md; data/fixtures/pilot.json.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 5 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\data.jpg](background_5.jpg)
DATA ENGINEERING
Raw data becomes traceable evidence.
Checksums, explicit units and receipt-time availability make the input reproducible.

![Database](s05_ingestion_totals_icon_6.jpg)
869 raw records
866
accepted observations

1 DUPLICATE
2 QUARANTINED

![FileCheck2](s05_data_flow_icon_15.jpg)

![GitBranch](s05_data_flow_icon_19.jpg)
Validate
Preserve reasons
Units, ranges, timestamps
and provenance
Invalid records enter
a quarantine ledger

What was available at issue time?

Observed
Issued
Received late
This late record is excluded from the earlier snapshot.
05  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Raw data becomes traceable evidence.
Suggested speaking time: 40 seconds.

MAIN POINT
Quality checks and receipt time prevent invalid inputs and temporal leakage.

PRESENTER SCRIPT
The initial raw archive has 869 records: 866 accepted, one exact duplicate ignored, and two invalid records quarantined with reasons. SHA-256 manifests freeze the fixture inputs. Units are converted explicitly. Explain the timeline: a reading may have an earlier observation timestamp but arrive after a warning was issued, so it cannot be used in that earlier feature snapshot. Missing intervals remain missing; absence does not become zero rainfall.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/PROJECT_REPORT.md, Data and GIS; docs/DATA_DICTIONARY.md; data/manifest.json; outputs/evidence/backend-acceptance.json.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 6 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_6.jpg)
GEOGRAPHIC REASONING
GIS connects area context to a directed road graph.
The illustration uses the supplied synthetic geometry and road connections.

A3
B3
C3

A2
B2
C2

A1
B1
C1

WESTBANK
MARKET WARD
EASTBANK

![Layers](s06_gis_facts_icon_90.jpg)
9 analysis cells
Approximately 1 km spatial support

![Waypoints](s06_gis_facts_icon_94.jpg)
21 nodes / 61 directed edges
One-way and disconnected cases included
WGS84 for display
UTM 45N for distances
Area susceptibility and road-water depth require different evidence.
06  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
GIS connects area context to a directed road graph.
Suggested speaking time: 40 seconds.

MAIN POINT
GIS keeps map display, distance calculation and road restrictions at the appropriate spatial scales.

PRESENTER SCRIPT
Explain the nine approximately one-kilometre cells and the directed road graph of 21 nodes and 61 edges. Display coordinates are WGS84, but distances and spatial matching are projected to EPSG:32645, UTM zone 45N. The test fixture includes one-way and disconnected routes. A kilometre-scale warning cell cannot determine water depth on a street. Road exclusions require reviewed evidence matched to a particular edge. The colored cells reproduce the recorded initial-state schematic, and all geography remains synthetic.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
data/fixtures/pilot.json; docs/ARCHITECTURE.md; docs/PROJECT_REPORT.md; backend/floodline/geo.py.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 7 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\data.jpg](background_7.jpg)
ACTIVE BASELINE
An interpretable rule runs the demo.
The current index combines static susceptibility with recent rainfall.

0.35 S
0.65 R
=
+
INDEX
Rounded relative warning index

![Building2](s07_rule_features_icon_13.jpg)

![CloudRain](s07_rule_features_icon_17.jpg)
S: static susceptibility
R: recent rainfall
Imperviousness, drainage, relative
elevation and distance to water
Three-hour rainfall scaled to
75 mm, capped at 100

MONITOR
ELEVATED
HIGH
UNKNOWN
Index < 55
55–74
≥ 75
Missing / stale rain
07  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
An interpretable rule runs the demo.
Suggested speaking time: 45 seconds.

MAIN POINT
The active service uses a transparent threshold rule, not the unpromoted logistic model.

PRESENTER SCRIPT
The active version is demo-threshold-v1. Static susceptibility S equals 100 times 0.35 times impervious fraction, plus 0.35 times drainage constraint, plus 0.20 times max(0,1-relative elevation/10), plus 0.10 times max(0,1-distance to water/1500), rounded. R is min(100, rainfall in three hours / 75 times 100). The current index is round(0.35 S + 0.65 R). High begins at 75, Elevated at 55, otherwise Monitor. Missing rainfall, rain older than 90 minutes, or under 75 percent expected interval coverage gives Unknown with a null index. Gauge values are contextual and affect support flags, not this numeric index. All weights and thresholds are demo assumptions. The three-hour validity limit is a record lifetime, not an established forecasting horizon.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/MODEL_CARD.md, Active rule; backend/floodline/prediction.py.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 8 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_8.jpg)
RESIDENT EXPERIENCE
The evidence is visible beside the map.
Risk words, timestamps and support flags help a resident interpret the display.

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\dashboard_map.png](s08_evidence_map_image_6.jpg)

EASTBANK · CENTRAL

HIGH  /  DEMO RULE
81
/ 100
64.8 mm rain / past 3 hours
Observed 14:00 IST  •  support: Limited
Relative index; no calibrated probability.
08  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
The evidence is visible beside the map.
Suggested speaking time: 35 seconds.

MAIN POINT
The interface separates the warning index from the quality and time support of its evidence.

PRESENTER SCRIPT
This native summary reproduces the selected C2 area in the captured dashboard: High, index 81 out of 100, 64.8 millimetres known rainfall in the past three hours, observed at 14:00 IST, and Limited support. The source panel also shows a stale synthetic gauge reading of 5.2 metres with an arbitrary datum. Explain that a large index does not mean an 81 percent flood probability. Unknown cells remain visibly different and appear in the summary denominator. The accessible interface uses words as well as color, a text alternative to map-only information, and keyboard focus.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
.impeccable/review/desktop-dark.png; docs/MODEL_CARD.md; docs/ACCEPTANCE.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 9 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_9.jpg)
COMMUNITY REPORTING
Reports earn trust through review.
An observation stays private while its time, location and publication permissions are checked.

RESIDENT / SUBMIT

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\report_form.png](s09_resident_report_image_8.jpg)
Image + location
+ observed time
Pending reports and images remain private.

MODERATOR / VERIFY

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\moderation.png](s09_moderation_review_image_15.jpg)
Authenticated review → bounded road hazard

09  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Reports earn trust through review.
Suggested speaking time: 40 seconds.

MAIN POINT
Reports become actionable only after authenticated and documented review.

PRESENTER SCRIPT
A resident supplies observed conditions, a location pin or coordinates, time, optional image, and publication permissions. Pending reports and images belong to the resident session and are private. Uploads are size and content validated, oriented, stripped of EXIF metadata, and re-encoded. A moderator checks time and location, records a reason, matches evidence to an appropriate road segment, and confirms privacy handling before verification. Publication is a separate explicit choice. Verified current restrictions can then affect routes and alerts. An unreviewed report cannot block a road. Do not invent human testing or field verification; these are software workflow demonstrations.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
.impeccable/review/report-form-dark.png; .impeccable/review/moderation-dark.png; docs/API_CONTRACTS.md; docs/ACCEPTANCE.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 10 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_10.jpg)
VERIFIED HAZARD ROUTING
Reviewed evidence changes the route.
The recorded Library → Station comparison excludes a newly verified segment.

BEFORE / 1 ACTIVE HAZARD

Library
Station

AFTER / 2 ACTIVE HAZARDS

Library
Station

The synthetic graph contains tied paths.
Only current, verified edge hazards are excluded.
Different edges. Same 4.445 km.
10  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Reviewed evidence changes the route.
Suggested speaking time: 40 seconds.

MAIN POINT
The route behavior is demonstrated with different edges, without claiming a shorter or universally safe path.

PRESENTER SCRIPT
Both recorded routes are 4444.9 metres long because the fixture has tied alternatives. Initially the route follows the north approach to Station. After verification, both directions of that approach are excluded along with the already-active hazard. The recalculated route uses different edges. The diagrams are editable renderings of the exact before/after edge IDs in browser-acceptance.json. The service handles one-way rules and unreachable destinations. A route avoids currently verified hazards on the mapped graph; other unreported hazards and original-pin connectors may still exist.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
outputs/evidence/browser-acceptance.json, route_comparison; data/fixtures/pilot.json; .impeccable/review/route-before-dark.png; .impeccable/review/route-after-dark.png.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 11 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_11.jpg)
CONSENT AND DELIVERY
Alerts remember consent, retries and expiry.
Persistent decisions prevent repeated processing from becoming repeated messages.

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\alerts.png](s11_alert_capture_image_6.jpg)
Opt in to a ward

![Bell](s11_alert_step_0_icon_7.jpg)
A resident chooses subscriptions.
Deduplicate the trigger

![CheckCheck](s11_alert_step_1_icon_10.jpg)
Unchanged reminders use a 30-minute cooldown.
Bound delivery attempts

![TimerReset](s11_alert_step_2_icon_13.jpg)
Retries after 30 and 60 seconds; 3 attempts maximum.
Cancel stale actions

![Clock3](s11_alert_step_3_icon_16.jpg)
Withdrawal, expiry and resolved hazards stop delivery.
11  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Alerts remember consent, retries and expiry.
Suggested speaking time: 40 seconds.

MAIN POINT
The notification lifecycle is implemented and tested, using a simulated in-app adapter.

PRESENTER SCRIPT
Residents must opt in to a ward. Persistent idempotency prevents duplicate deliveries for the same trigger. A 30-minute cooldown applies to unchanged warning reminders, while severity escalation may bypass it. A simulated failed attempt retries after 30 seconds, then after 60 seconds, with three attempts in total. Withdrawn consent, stale or superseded evidence, resolved hazards and expiry stop queued delivery. These are in-app simulation records; no real email or SMS is sent. The captured interface is the actual delivery-history screen.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/DEMO_RUNBOOK.md, Replay controls and delivery; docs/ACCEPTANCE.md; .impeccable/review/alerts-active-dark.png.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 12 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\data.jpg](background_12.jpg)
SOFTWARE EXPERIMENT
Synthetic evaluation keeps events separate.
18 invented storms supply 624 usable rows; later storms remain held out.

TRAIN
10
events / 345 rows
Fit preprocessing

VALIDATE
4
events / 141 rows
Select F₂ threshold

TEST
4
events / 138 rows
Freeze final comparison

![GitBranch](s12_temporal_rule_icon_20.jpg)
Earlier events → later events. No row substitutes for an independent storm.
12  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Synthetic evaluation keeps events separate.
Suggested speaking time: 40 seconds.

MAIN POINT
The logistic candidate is a separate software experiment with chronological event-level splits.

PRESENTER SCRIPT
There are 18 synthetic storms and 624 usable rows. Twenty-four unknown-label rows are excluded. Ten training events produce 345 rows, four validation events 141 rows, and four final-test events 138 rows. Positive onset times fall after issue time within the three-hour target window. Imputation, missing indicators, scaling and class weighting are fitted on training only. Validation F2 selects a threshold of 0.3, which is frozen before the final test. Storm groups are separated chronologically, and target/look-back overlaps are purged as whole groups if present. This dataset has no real historical validation.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
outputs/evidence/evaluation.json; outputs/evidence/split-manifest.json; docs/MODEL_CARD.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 13 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\data.jpg](background_13.jpg)
EVALUATION RESULT
Higher recall brought more false positives.
Held-out synthetic rows compare the logistic candidate with a rainfall-only baseline.

TEST-ROW ERRORS
Logistic
Rain-only
40
8
False
positives
0
12
Missed
positives
138 rows / 4 test storms

### Chart: Held-out synthetic comparison

| Category | Logistic candidate | Rainfall-only |
|---|---|---|
| Recall | 100.0 | 87.76 |
| Precision | 71.01 | 91.49 |Candidate remains unpromoted: it flags every test row.
13  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Higher recall brought more false positives.
Suggested speaking time: 50 seconds.

MAIN POINT
The candidate’s perfect synthetic recall comes with an unacceptable false-positive burden for promotion.

PRESENTER SCRIPT
At the validation-selected 0.3 threshold, the logistic candidate flags all 138 test rows: 98 true positives, 40 false positives, zero true negatives and zero missed positives. Recall is 1.0 and precision 0.7101. The separate 75 mm rainfall-only comparator has 86 true positives, 32 true negatives, eight false positives and 12 misses: recall 0.8776 and precision 0.9149. The rainfall-only comparator is not the composite rule running in the map. These correlated rows are decision opportunities, not distinct delivered messages or independent storms. Four synthetic test storms cannot support stable calibration, metric intervals, city-level accuracy or model promotion. The running application never loads the candidate for decisions.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
outputs/evidence/evaluation.json; docs/MODEL_CARD.md; docs/PROJECT_REPORT.md, Baseline and separate model experiment.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 14 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\warning.jpg](background_14.jpg)
FAILURE HANDLING
Unknown data stays visibly unknown.
The outage scenario preserves original issue times instead of refreshing stale evidence.

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\outage_map.png](s14_outage_capture_image_12.jpg)
9 / 9
cells become Unknown
during the recorded feed outage

![CloudOff](s14_outage_explanation_icon_8.jpg)
Feed outage
No invented observations
and no zero-rain substitution
14  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Unknown data stays visibly unknown.
Suggested speaking time: 35 seconds.

MAIN POINT
The tested outage path represents missing support honestly and suppresses stale actions.

PRESENTER SCRIPT
The moderator’s Feed outage control advances demo time by 105 minutes without inserting rainfall. All nine cells become Unknown with null current indices, and previous issue times are retained. Stale or expired evidence stops queued alert delivery. Recover feed advances synthetic time by 15 minutes and reconstructs a clearly labelled synthetic history; it does not pretend missing observations from a real outage were recovered. The backend suite also injects a worker inference failure, logs its class, rolls back related writes, and verifies recovery without duplicate decisions.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
.impeccable/review/feed-outage-dark.png; outputs/evidence/browser-acceptance.json; docs/ACCEPTANCE.md; docs/DEMO_RUNBOOK.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 15 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\data.jpg](background_15.jpg)
RECORDED ACCEPTANCE
The delivery is backed by inspectable checks.
Acceptance evidence for the synthetic v0.1.1 release, recorded 11 November 2026.

![ShieldCheck](s15_check_0_icon_6.jpg)
44
backend tests

![Map](s15_check_1_icon_10.jpg)
14
browser workflows

![CodeXml](s15_check_2_icon_14.jpg)
7
Windows launcher checks

![Eye](s15_check_3_icon_18.jpg)
62
captured UI states

![Users](s15_acceptance_context_icon_22.jpg)

![Activity](s15_acceptance_context_icon_26.jpg)
Light + Dark / phone to desktop
Local dashboard p95: 57.42 ms
320–1440 px captures, keyboard flows, consent,
moderation, routes, outage and recovery.
10 clients / 20 loopback requests / SQLite.
Fresh Linux CI also passes the automated workflow.
15  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
The delivery is backed by inspectable checks.
Suggested speaking time: 45 seconds.

MAIN POINT
Recorded software acceptance covers functional and failure paths, with transparent performance scope.

PRESENTER SCRIPT
Report these as recorded results dated 11 November 2026, not as tests newly executed while creating the slides: 44 backend tests, 14 browser flow checks, seven isolated Windows launcher checks and 62 screenshots across Light and Dark at 1440, 1024, 390 and 320 pixel widths. Browser acceptance records no uncaught JavaScript errors or horizontal overflow. Device/System appearance, persistence and AA text/control contrast are checked. The local p95 is 57.42 milliseconds and median 41.955 milliseconds for 20 dashboard requests from ten concurrent loopback clients using SQLite; upstream latency and city-scale load are outside this measurement. The recorded fresh Ubuntu CI installs dependencies and passes backend, production build and browser checks. Automated checks are not human usability studies.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/ACCEPTANCE.md; outputs/evidence/backend-acceptance.json; browser-acceptance.json; launcher-acceptance.json; performance.json; github-actions.json.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 16 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_16.jpg)
PRESENTATION DEMO
A focused demo follows six actions.
The same workflow can be shown live or explained using the preceding captures.

01
Inspect

![MapPinned](s16_demo_0_icon_7.jpg)
Select an area and
check its evidence.

02
Report

![Upload](s16_demo_1_icon_12.jpg)
Submit time, location
and an observation.

03
Verify

![ShieldCheck](s16_demo_2_icon_17.jpg)
Review evidence and
match a road segment.

04
Reroute

![Route](s16_demo_3_icon_22.jpg)
Compare changed edges
after verification.

05
Subscribe

![Bell](s16_demo_4_icon_27.jpg)
Opt in to a ward and
inspect delivery history.

06
Replay

![RefreshCw](s16_demo_5_icon_32.jpg)
Run heavy rain, outage
and synthetic recovery.

Launch start.bat beforehand. The console shows the selected address.
OPEN LOCAL DEMO
16  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
A focused demo follows six actions.
Suggested speaking time: 30 seconds, plus optional live demo.

MAIN POINT
The supplied demo runbook gives a reproducible six-person, ten-minute live workflow.

PRESENTER SCRIPT
If a live demo is included, pause the deck here. Launch start.bat from the project root before presenting; it opens the dashboard when ready, normally at http://127.0.0.1:8000, or the next available port. Use a separate rehearsal runtime to preserve normal data. The runbook’s proposed roles and timings are M1 scope/data 0:00–1:15; M2 GIS/route 1:15–2:30; M3 evaluation 2:30–4:00; M4 submission/privacy 4:00–5:30; M5 verification/reroute/mobile 5:30–7:00; M6 consent/alerts/failure replay 7:00–10:00. Use the displayed demo clock for observations. At Station, verify the north approach only when the submitted pin supports it. The moderator login in the local app is documented in the runbook. If time is short, describe the six actions using the preceding screenshots. The team labels are proposed responsibilities; named contributions are not yet supplied.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/DEMO_RUNBOOK.md; README.md; docs/TEAM_CONTRIBUTIONS.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 17 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_17.jpg)
NEXT EVIDENCE GATES
The path to a real pilot is clear.
The synthetic software workflow is delivered. Real-world readiness needs its own evidence.

![CircleCheck](s17_delivered_scope_icon_6.jpg)
Delivered now
Local map and area evidence

![Check](s17_delivered_scope_icon_8.jpg)
Private reports + moderation

![Check](s17_delivered_scope_icon_10.jpg)
Verified road exclusions

![Check](s17_delivered_scope_icon_12.jpg)
Consent-based alert lifecycle

![Check](s17_delivered_scope_icon_14.jpg)
Evaluation and release records

![Check](s17_delivered_scope_icon_16.jpg)

SYNTHETIC DEMONSTRATION
Choose a pilot and licensed inputs

![Globe](s17_gate_0_icon_20.jpg)
Audit source access, coverage and time semantics.
Validate with historical flood events

![Gauge](s17_gate_1_icon_23.jpg)
Use credible labels and separated held-out events.
Run field and human reviews

![Users](s17_gate_2_icon_26.jpg)
GIS, usability, local language and team sign-offs.
Accept the deployment environment

![Network](s17_gate_3_icon_29.jpg)
Test PostGIS, hosting and real notification delivery.
17  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
The path to a real pilot is clear.
Suggested speaking time: 40 seconds.

MAIN POINT
The next steps are evidence collection and validation gates, not unsupported claims of deployment readiness.

PRESENTER SCRIPT
The synthetic implementation closes the local software path. Real pilot selection and source/licence access remain open. Historical forecasting requires credible positive and negative event labels, receipt-time leakage checks, enough event-separated data and a frozen comparison at an acceptable alert burden. The team must complete named contributions, peer review and rehearsal. Field GIS review, five consenting human usability testers and a fluent local-language reviewer have not been recorded. The optional PostgreSQL/PostGIS adapter and container preparation are supplied but untested locally; hosting, real providers and multi-worker operation require separate acceptance.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/REMAINING_TASKS.md; docs/PROJECT_STATUS.md; docs/MODEL_CARD.md; docs/TEAM_CONTRIBUTIONS.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 18 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\hero.jpg](background_18.jpg)
TAKEAWAYS
Visible evidence supports useful local decisions.
FLOODLINE
Trace the data. Review the observation. Explain the action.

![Database](s18_takeaway_0_icon_7.jpg)
Traceable inputs

![ShieldCheck](s18_takeaway_1_icon_10.jpg)
Reviewed reports

![Bell](s18_takeaway_2_icon_13.jpg)
Accountable actions
Questions & discussion
github.com/Godavenger/floodline-caa
18  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Visible evidence supports useful local decisions.
Suggested speaking time: 25 seconds.

MAIN POINT
The delivered project’s value is a traceable local workflow, with honest limits.

PRESENTER SCRIPT
Close on three ideas: traceable data, reviewed community evidence and accountable actions. The platform demonstrates the complete local pipeline now, while explicitly leaving real forecasting validity and deployment approval to later evidence. Invite questions. If asked about accuracy, refer to slide 13 and its false-positive burden rather than quoting perfect recall alone. If asked about responsibilities or sources, the next two appendix slides provide backup. The repository link is clickable.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/PROJECT_REPORT.md; docs/PROJECT_STATUS.md; https://github.com/Godavenger/floodline-caa.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 19 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_19.jpg)
APPENDIX / TECHNICAL HANDOFFS
Six responsibility areas connect the stack.
M1–M6 are proposed team labels from the pipeline; named contribution records remain to be completed.

![Database](s19_role_0_icon_8.jpg)
M1
Data and sources
Python • provenance • quality checks

![Compass](s19_role_1_icon_14.jpg)
M2
GIS and routing
Shapely • PyProj • NetworkX

![SlidersHorizontal](s19_role_2_icon_20.jpg)
M3
Baseline and evaluation
Interpretable rule • scikit-learn

![CodeXml](s19_role_3_icon_26.jpg)
M4
Backend and integration
FastAPI • SQLite • authenticated APIs

![Map](s19_role_4_icon_32.jpg)
M5
Resident and moderator UI
React • TypeScript • Leaflet

![Bell](s19_role_5_icon_38.jpg)
M6
Alerts and acceptance
Delivery state • tests • release evidence
19  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Six responsibility areas connect the stack.
Suggested speaking time: Backup slide.

MAIN POINT
The implementation follows the proposed six-person module handoffs without inventing individual contributions.

PRESENTER SCRIPT
These labels come from the supplied pipeline and contribution template. Do not assign real people or claim hours, peer review or human usability results that have not been supplied. The delivered local architecture is Python/FastAPI and SQLite, React/TypeScript/Leaflet, Shapely/PyProj/NetworkX for GIS and scikit-learn for the separate experiment. PostgreSQL/PostGIS preparation exists as an optional path and is untested locally. Each member should be able to explain the entire data-to-action flow and one failure case, in addition to their proposed primary module.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/TEAM_CONTRIBUTIONS.md; docs/ARCHITECTURE.md; outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.

<!-- Slide number: 20 -->

![C:\Users\Sharanya\Documents\Snigdha CAA assignment\outputs\_build\presentation\assets\background.jpg](background_20.jpg)
APPENDIX / SOURCES
Requirements, implementation and evidence are linked.
Project-authored synthetic fixtures supply this release’s data.

![FileText](s20_project_records_icon_6.jpg)
Project records
Assignment
project description.docx, item 3
Implementation plan
Smart_City_Flood_Prediction_CAA_Pipeline.md
Release and limits
PROJECT_REPORT.md / MODEL_CARD.md
Measured evidence
evaluation.json / acceptance records
Data provenance
SOURCE_REGISTER.md / data/manifest.json

![BookOpen](s20_implementation_links_icon_19.jpg)
Implementation references
FastAPI
Leaflet
scikit-learn
PostGIS

![Globe](s20_candidate_sources_icon_26.jpg)
Real-pilot candidates
IMD • India-WRIS/CWC • NASA IMERG
Open-Meteo • municipal records • OSM
Access and suitability remain unverified.
20  /  20
FLOODLINE  /  CAA PROJECT

### Notes:
Requirements, implementation and evidence are linked.
Suggested speaking time: Backup slide.

MAIN POINT
The project evidence and implementation references are distinguishable from future real-data candidates.

PRESENTER SCRIPT
All environmental observations, event labels, wards and road geometry used by this release are project-authored synthetic fixtures. The assignment and pipeline define the scope. The source register records provenance, rights and candidate-source limitations. FastAPI, Leaflet, scikit-learn and PostGIS are implementation references, not evidence of flood-prediction accuracy. IMD, CWC/India-WRIS, NASA IMERG, Open-Meteo, municipalities and OSM are future candidates; their data has not been accessed or ingested in this release. Inspect access, licences, timestamp semantics, resolution and geographic relevance before accepting a real adapter. All displayed reference names on the implementation panel have clickable external links.

ANIMATION
The title and grouped content build automatically when the slide opens. Wait about one second for the full composition. Advance once to the next slide.

SOURCES
docs/SOURCE_REGISTER.md; docs/PROJECT_REPORT.md, Reference starting points; THIRD_PARTY.md; data/manifest.json.

SCOPE
This release uses invented development fixtures. The active warning index is relative susceptibility and threshold evidence. It is not a validated flood probability. External notifications are simulated.