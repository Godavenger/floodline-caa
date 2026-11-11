from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from uuid import uuid4

from pydantic import ValidationError
from shapely.geometry import Point, shape

from .auth import create_moderator
from .config import ROOT, stamp, utc, wall_now
from .geo import expanded_edges
from .schemas import ObservationInput


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def ingest(db, connection, records):
    sources = {row["id"]: json.loads(row["metadata_json"]) for row in db.all(connection, "SELECT * FROM sources")}
    areas = {row["id"]: row for row in db.all(connection, "SELECT * FROM areas")}
    outcome = {"accepted": 0, "duplicates": 0, "quarantined": 0, "reasons": []}
    for raw in records:
        raw_fingerprint = fingerprint(raw)
        try:
            observation = ObservationInput.model_validate(raw)
            if observation.source_id not in sources or observation.area_id not in areas:
                raise ValueError("Unknown source or analysis area.")
            if not shape(json.loads(areas[observation.area_id]["geometry_json"])).covers(Point(observation.longitude, observation.latitude)):
                raise ValueError("Observation location is outside its declared analysis cell.")
            if observation.received_at < observation.observed_at:
                raise ValueError("Receipt time precedes observation time.")
            value, unit = observation.value, observation.unit.lower()
            target = "mm" if observation.variable == "rainfall" else "m"
            factors = {"mm": 1, "cm": 10, "in": 25.4} if target == "mm" else {"m": 1, "cm": 0.01, "mm": 0.001}
            if unit not in factors:
                raise ValueError("Unit is incompatible with the observed variable.")
            expected_source_unit = sources[observation.source_id]["unit"]
            if target != expected_source_unit:
                raise ValueError("Variable conflicts with the source register.")
            if observation.interval_minutes != sources[observation.source_id]["interval_minutes"]:
                raise ValueError("Observation interval conflicts with the registered source frequency.")
            if value is None and observation.quality != "missing":
                raise ValueError("A null value must carry the missing quality flag.")
            if observation.quality == "missing":
                value = None
            elif value is not None:
                value *= factors[unit]
                if value < 0 or value > (500 if target == "mm" else 30):
                    raise ValueError("Measurement is outside the documented demo plausibility bounds.")
            key = observation.source_id + ":" + observation.source_record_key
            existing = db.one(connection, "SELECT raw_fingerprint FROM observations WHERE source_key = ?", (key,))
            if existing:
                if existing["raw_fingerprint"] != raw_fingerprint:
                    raise ValueError("Source-record key conflicts with a previously accepted value.")
                outcome["duplicates"] += 1
                continue
            db.execute(connection, "INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (uuid4().hex, key, observation.source_id, observation.area_id, observation.variable, value,
                        target, observation.quality, stamp(observation.observed_at), stamp(observation.received_at),
                        observation.interval_minutes, observation.longitude, observation.latitude, raw_fingerprint))
            outcome["accepted"] += 1
        except (ValueError, ValidationError) as error:
            reason = str(error).split("\n")[0][:300]
            cursor = db.execute(connection, "INSERT INTO quarantine VALUES (?, ?, ?, ?, ?) ON CONFLICT(fingerprint) DO NOTHING",
                                (uuid4().hex, raw_fingerprint, stamp(wall_now()), reason, json.dumps(raw, default=str)))
            outcome["quarantined"] += int(cursor.rowcount > 0)
            if len(outcome["reasons"]) < 10:
                outcome["reasons"].append(reason)
    return outcome


def verify_manifest(settings):
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    by_name = {entry["path"]: entry for entry in manifest["files"]}
    for path, relative in [(settings.fixture, "data/fixtures/pilot.json"), (settings.observations, "data/raw/demo_observations.json")]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != by_name[relative]["sha256"]:
            raise ValueError(f"Fixture checksum mismatch: {relative}. Rebuild and review the manifest.")


def seed(db, settings):
    verify_manifest(settings)
    fixture = json.loads(settings.fixture.read_text(encoding="utf-8"))
    with db.transaction() as connection:
        moderator_id = create_moderator(db, connection, settings.admin_username, settings.admin_password)
        if db.meta(connection, "pilot_version"):
            return
        if fixture["mode"] != "synthetic":
            raise ValueError("This seed must be explicitly synthetic.")
        for source in fixture["sources"]:
            db.execute(connection, "INSERT INTO sources VALUES (?, ?)", (source["id"], json.dumps(source)))
        for area in fixture["areas"]:
            geometry = shape(area["geometry"])
            if not geometry.is_valid or geometry.is_empty:
                raise ValueError("The pilot contains invalid geometry.")
            db.execute(connection, "INSERT INTO areas(id, ward_id, name, geometry_json, properties_json) VALUES (?, ?, ?, ?, ?)",
                       (area["id"], area["ward_id"], area["name"], json.dumps(area["geometry"]), json.dumps(area["properties"])))
        for node in fixture["nodes"]:
            db.execute(connection, "INSERT INTO road_nodes VALUES (?, ?, ?, ?)",
                       (node["id"], node["name"], node["longitude"], node["latitude"]))
        for road in fixture["roads"]:
            db.execute(connection, "INSERT INTO road_edges(id, segment_id, source_node, target_node, name, length_m, geometry_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (road["id"], road["segment_id"], road["source_node"], road["target_node"], road["name"], road["length_m"], json.dumps(road["geometry"])))
        base = utc(fixture["base_time"])
        db.set_meta(connection, "pilot_version", fixture["version"])
        db.set_meta(connection, "virtual_anchor", stamp(base))
        db.set_meta(connection, "wall_anchor", stamp(wall_now()))
        db.set_meta(connection, "scenario", "initial")
        db.set_meta(connection, "fail_next_deliveries", 0)
        db.set_meta(connection, "fixture", {key: fixture[key] for key in ["name", "description", "bounds", "cartography", "version"]})
        raw = json.loads(settings.observations.read_text(encoding="utf-8"))
        db.set_meta(connection, "initial_ingestion", ingest(db, connection, raw["records"]))
        roads = db.all(connection, "SELECT * FROM road_edges")
        for report in fixture["seed_reports"]:
            observed = base + timedelta(minutes=report["observed_offset_minutes"])
            expires = base + timedelta(minutes=report["expires_offset_minutes"])
            db.execute(connection, "INSERT INTO reports(id, user_id, area_id, description, severity, longitude, latitude, observed_at, submitted_at, expires_at, status, review_reason) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (report["id"], moderator_id, report["area_id"], report["description"], report["severity"], report["longitude"], report["latitude"],
                        stamp(observed), stamp(base), stamp(expires), report["status"], "Seeded synthetic evidence; no field validation." if report["status"] == "verified" else None))
            if report["edge_ids"]:
                edge_ids = expanded_edges(roads, report["edge_ids"])
                db.execute(connection, "INSERT INTO hazards VALUES (?, ?, ?, ?, ?, ?)",
                           ("demo-market-hazard", report["id"], json.dumps(edge_ids), stamp(base), stamp(expires), None))
        for event in fixture["events"]:
            db.execute(connection, "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
                       (event["id"], event["area_id"], event["onset"], event["label_state"], json.dumps(event["evidence"])))


def feature_snapshot(db, connection, area_id: str, issued_at):
    # Both clocks matter: late receipts never leak into an earlier issue-time row.
    rows = db.all(connection, "SELECT * FROM observations WHERE area_id = ? AND observed_at <= ? AND received_at <= ? "
                  "AND observed_at > ? ORDER BY observed_at, received_at", (area_id, stamp(issued_at), stamp(issued_at), stamp(issued_at - timedelta(hours=25))))
    rain = [row for row in rows if row["variable"] == "rainfall" and row["quality"] == "good" and row["value"] is not None]
    levels = [row for row in rows if row["variable"] == "water_level" and row["quality"] == "good" and row["value"] is not None]
    result = {"issued_at": stamp(issued_at), "rainfall_observed_at": rain[-1]["observed_at"] if rain else None,
              "level_observed_at": levels[-1]["observed_at"] if levels else None,
              "water_level_m": levels[-1]["value"] if levels else None,
              "rainfall_age_minutes": (issued_at - utc(rain[-1]["observed_at"])).total_seconds() / 60 if rain else None,
              "level_age_minutes": (issued_at - utc(levels[-1]["observed_at"])).total_seconds() / 60 if levels else None,
              "source_record_ids": [row["id"] for row in rows], "imputed_fraction": 0,
              "datum": "Synthetic local demo datum; not road-water depth."}
    for hours in [1, 3, 6, 24]:
        selected = [row for row in rain if utc(row["observed_at"]) > issued_at - timedelta(hours=hours)]
        # Interval totals only; do not multiply an interval amount by frequency.
        countable = {(row["observed_at"], row["source_id"]): row for row in selected}
        covered_minutes = sum(row["interval_minutes"] for row in countable.values())
        coverage = min(1, covered_minutes / (hours * 60))
        result[f"rainfall_{hours}h_mm"] = round(sum(row["value"] for row in countable.values()), 2) if selected else None
        result[f"coverage_{hours}h"] = round(coverage, 4)
    result["missing_fraction"] = round(1 - result["coverage_3h"], 4)
    result["available_at"] = max((row["received_at"] for row in rows), default=None)
    result["fingerprint"] = fingerprint({"area": area_id, "records": [(row["id"], row["value"], row["quality"]) for row in rows]})
    return result
