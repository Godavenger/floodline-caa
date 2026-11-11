# Source and licence register

The user approved a synthetic pilot on 11 November 2026. None of the registered
environmental or road data below came from a live city feed. Coordinates are
WGS84 development geometry; their proximity to a real place does not make the
wards, streets, gauges or drainage observations authoritative.

| Source / artifact | Origin | Frequency / resolution | Rights and limitation |
| --- | --- | --- | --- |
| Assignment requirements | Supplied project description.docx, item 3 | Assignment text | Preserve the supplied document; no extra rubric assumed |
| Implementation pipeline | outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md | Eight-week plan | Supplied project planning artifact; gates are planning targets |
| pilot.json | scripts/build_demo.py | Nine approximately 1 km cells, three wards; WGS84 | Project-authored synthetic fixture; invented terrain, drains and roads |
| demo-rain | data/raw/demo_observations.json | 15-minute interval totals in mm | Project-authored simulator; not a station or satellite product |
| demo-level | Same raw archive | 15-minute samples in m | Declared arbitrary demo datum; not road-water depth |
| Seed reports/events | pilot.json | Timestamped fixture cases | No participant or field evidence; excluded from real accuracy |
| synthetic_evaluation.csv | backend/floodline/evaluation.py, seed 20261111 | 18 separated storm groups; nine areas and four issue times per storm | Synthetic labels and credible-negative flags are simulator constructs |
| Manrope | Locally bundled @fontsource-variable/manrope | Variable font | SIL Open Font License; notice included in the release |
| Leaflet and UI libraries | Locked npm packages | Application components | Respective package licences; see THIRD_PARTY.md |
| Optional OSM tiles | OpenStreetMap, requested only when enabled | Online tile layer | OSM attribution retained; no OSM-derived roads in this fixture |

The data/manifest.json file records source file paths and SHA-256 values. The
seed verifies pilot and raw-observation checksums before loading. Evaluation
records its dataset and split fingerprints separately.

## Real-pilot source audit to complete

| Candidate | Inspect before use | Current status |
| --- | --- | --- |
| IMD rainfall | Coverage, timestamp semantics, access and permission | Not accessed or ingested |
| NASA GPM IMERG | Product/version, latency and coarse spatial resolution | Not accessed or ingested |
| Open-Meteo | Observation versus forecast issue time, terms and coverage | Not accessed or ingested |
| CWC / India-WRIS / municipality | Gauge relevance, vertical datum and thresholds | Not accessed or ingested |
| Suitable DEM and municipal drains | Resolution, date, licence and missing infrastructure | Not accessed or ingested |
| Authoritative wards and OSM roads | Date, licence, one-way/access rules and geometry | Not accessed or ingested |
| Municipal incident records | Time/location evidence and credible negative coverage | Not supplied |
| Consenting community participants | Consent, privacy review and retention agreement | No human study conducted |

The original pipeline contains official starting-point links. Inclusion as a
candidate does not establish permission, availability or street-level accuracy.
Use data/templates/event_ledger.csv to record actual evidence when available.
