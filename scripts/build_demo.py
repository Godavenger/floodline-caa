"""Create deterministic, clearly synthetic GIS and observation fixtures."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.floodline.geo import metric_distance

BASE = datetime(2026, 11, 11, 8, 30, tzinfo=timezone.utc)
iso = lambda value: value.isoformat(timespec="seconds").replace("+00:00", "Z")


def polygon(west, south, east, north):
    return {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}


def main():
    areas = []
    ward_names = ["Westbank", "Market ward", "Eastbank"]
    for column, ward in enumerate(ward_names):
        for row in range(3):
            west, south = 88.325 + column * 0.011, 22.560 + row * 0.010
            areas.append({"id": f"{chr(65 + column)}{row + 1}", "ward_id": chr(65 + column),
                          "name": f"{ward} · {'South' if row == 0 else 'Central' if row == 1 else 'North'}",
                          "geometry": polygon(west, south, west + 0.011, south + 0.010),
                          "properties": {"ward_name": ward, "geometry_version": "synthetic-gis-v1",
                                         "source_resolution_m": 1000, "projected_crs": "EPSG:32645",
                                         "impervious_fraction": round(0.35 + column * 0.15 + row * 0.04, 2),
                                         "drainage_constraint": round(0.2 + column * 0.25, 2),
                                         "relative_elevation_m": 8 - column * 2 - row * 0.5,
                                         "distance_to_water_m": 1200 - column * 450,
                                         "synthetic": True}})
    names = {(0, 1): "Library", (2, 1): "Market square", (4, 1): "Station",
             (1, 2): "Community hall", (3, 2): "Clinic", (0, 0): "School", (4, 3): "Riverside park"}
    nodes = [{"id": f"n{x}-{y}", "longitude": round(88.328 + x * 0.0065, 6),
              "latitude": round(22.563 + y * 0.008, 6), "name": names.get((x, y), f"Junction {x + 1}.{y + 1}"),
              "landmark": (x, y) in names} for y in range(4) for x in range(5)]
    nodes.append({"id": "island", "name": "Disconnected demo point", "longitude": 88.356, "latitude": 22.589, "landmark": True})
    lookup = {node["id"]: node for node in nodes}
    roads = []
    for y in range(4):
        for x in range(5):
            for dx, dy in [(1, 0), (0, 1)]:
                if x + dx >= 5 or y + dy >= 4:
                    continue
                a, b = f"n{x}-{y}", f"n{x + dx}-{y + dy}"
                segment = f"road-{a}-{b}"
                one_way = x == 0 and y == 0 and dx == 1
                for source, target, suffix in [(a, b, ""), *([] if one_way else [(b, a, "-r")])]:
                    first, last = lookup[source], lookup[target]
                    coordinates = [[first["longitude"], first["latitude"]], [last["longitude"], last["latitude"]]]
                    roads.append({"id": segment + suffix, "segment_id": segment, "source_node": source, "target_node": target,
                                  "name": "Market street" if y == 1 and dx else f"{'Cross street' if dx else 'Bank road'} {y + 1 if dx else x + 1}",
                                  "length_m": round(metric_distance(*coordinates), 2),
                                  "geometry": {"type": "LineString", "coordinates": coordinates}, "one_way": one_way})
    fixture = {"version": "synthetic-pilot-v1", "mode": "synthetic", "base_time": iso(BASE + timedelta(minutes=2)),
               "name": "Riverside demo catchment", "description": "Invented wards and roads anchored in WGS84 for GIS tests. This is not a real municipal boundary.",
               "bounds": [[22.560, 88.325], [22.590, 88.358]], "areas": areas, "nodes": nodes, "roads": roads,
               "sources": [{"id": "demo-rain", "name": "Synthetic rainfall replay", "kind": "simulated", "unit": "mm",
                            "interval_minutes": 15, "spatial_resolution_m": 1000, "licence": "Project-authored synthetic fixture"},
                           {"id": "demo-level", "name": "Synthetic gauge replay", "kind": "simulated", "unit": "m",
                            "datum": "Invented local demo datum; not street-water depth", "interval_minutes": 15,
                            "licence": "Project-authored synthetic fixture"}],
               "cartography": {"river": {"type": "LineString", "coordinates": [[88.356, 22.558], [88.3575, 22.571], [88.3555, 22.580], [88.357, 22.592]]},
                               "parks": [polygon(88.326, 22.581, 88.331, 22.588), polygon(88.350, 22.583, 88.354, 22.588)]},
               "seed_reports": [{"id": "demo-verified-market", "area_id": "B2", "longitude": 88.34425, "latitude": 22.571,
                                  "description": "Synthetic scenario: standing water covers the Market street connection. Reviewed for the route-avoidance demonstration.",
                                  "severity": "impassable", "status": "verified", "observed_offset_minutes": -20,
                                  "expires_offset_minutes": 100, "edge_ids": ["road-n2-1-n3-1"]},
                                 {"id": "demo-pending-east", "area_id": "C2", "longitude": 88.352, "latitude": 22.574,
                                  "description": "Synthetic scenario: water is collecting near the eastern junction. Location and severity still need review.",
                                  "severity": "water_on_road", "status": "pending", "observed_offset_minutes": -10,
                                  "expires_offset_minutes": 110, "edge_ids": []}],
               "events": [{"id": "synthetic-event-1", "area_id": "B2", "onset": iso(BASE + timedelta(hours=1)),
                           "label_state": "synthetic", "evidence": "Development scenario only; excluded from historical accuracy."}]}
    observations = []
    for area in areas:
        centroid = [sum(p[0] for p in area["geometry"]["coordinates"][0][:-1]) / 4,
                    sum(p[1] for p in area["geometry"]["coordinates"][0][:-1]) / 4]
        for index in range(96):
            observed = BASE - timedelta(minutes=15 * (95 - index))
            # C3 deliberately lacks the most recent two hours of rainfall.
            if area["id"] == "C3" and observed > BASE - timedelta(hours=2):
                continue
            column = ord(area["ward_id"]) - ord("A")
            value = 0.3 if index < 84 else (1.0 + column * 0.8 if index < 92 else 3.0 + column * 4.0)
            observations.append({"source_record_key": f"initial-{area['id']}-rain-{index}", "source_id": "demo-rain", "area_id": area["id"],
                                 "observed_at": iso(observed), "received_at": iso(observed + timedelta(minutes=2)),
                                 "variable": "rainfall", "value": value, "unit": "mm", "quality": "good", "interval_minutes": 15,
                                 "longitude": centroid[0], "latitude": centroid[1]})
        level_time = BASE - timedelta(minutes=10 if area["ward_id"] != "C" else 180)
        observations.append({"source_record_key": f"initial-{area['id']}-level", "source_id": "demo-level", "area_id": area["id"],
                             "observed_at": iso(level_time), "received_at": iso(level_time + timedelta(minutes=1)),
                             "variable": "water_level", "value": round(2.4 + column * 1.4, 1), "unit": "m", "quality": "good",
                             "interval_minutes": 15, "longitude": centroid[0], "latitude": centroid[1]})
    observations.append(dict(observations[0]))  # Idempotency fixture.
    negative = dict(observations[0], source_record_key="invalid-negative", value=-3)
    conflict = dict(observations[0], source_record_key="invalid-unit", unit="metres-per-second")
    delayed = dict(observations[-4], source_record_key="delayed-receipt", observed_at=iso(BASE - timedelta(minutes=5)),
                   received_at=iso(BASE + timedelta(minutes=30)))
    observations.extend([negative, conflict, delayed])
    paths = [(ROOT / "data" / "fixtures" / "pilot.json", fixture),
             (ROOT / "data" / "raw" / "demo_observations.json", {"mode": "synthetic", "records": observations})]
    entries = []
    for path, content in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(content, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        path.write_bytes(encoded)
        entries.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(encoded).hexdigest(),
                        "source": "scripts/build_demo.py", "licence": "Project-authored synthetic fixture", "synthetic": True})
    evaluation = ROOT / "data" / "fixtures" / "synthetic_evaluation.csv"
    if evaluation.exists():
        entries.append({"path": "data/fixtures/synthetic_evaluation.csv", "sha256": hashlib.sha256(evaluation.read_bytes()).hexdigest(),
                        "source": "backend/floodline/evaluation.py", "licence": "Project-authored synthetic fixture", "synthetic": True})
    (ROOT / "data" / "manifest.json").write_text(json.dumps({"version": "synthetic-pilot-v1", "files": entries}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"areas": len(areas), "nodes": len(nodes), "directed_edges": len(roads), "raw_observations": len(observations), "mode": "synthetic"}))


if __name__ == "__main__":
    main()
