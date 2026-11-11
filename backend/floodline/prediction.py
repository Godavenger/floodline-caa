from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

from .config import stamp, utc
from .data import feature_snapshot, fingerprint

RULE_VERSION = "demo-threshold-v1"
FRESH_RAIN_MINUTES = 90
FRESH_LEVEL_MINUTES = 60
CLEAR_INDEX = 45
ELEVATED_INDEX = 55
HIGH_INDEX = 75
RANK = {"unknown": -1, "low": 0, "elevated": 1, "high": 2}


def interpret(features, properties):
    static = round(100 * (0.35 * properties["impervious_fraction"] + 0.35 * properties["drainage_constraint"]
                          + 0.20 * max(0, 1 - properties["relative_elevation_m"] / 10)
                          + 0.10 * max(0, 1 - properties["distance_to_water_m"] / 1500)))
    reasons = []
    age = features["rainfall_age_minutes"]
    if age is None or age > FRESH_RAIN_MINUTES or features["coverage_3h"] < 0.75:
        reasons.append("Rainfall is missing, stale or has less than 75% of the three-hour intervals.")
        return {"risk_level": "unknown", "index": None, "susceptibility_index": static,
                "data_support": "insufficient", "reasons": reasons}
    support = "adequate"
    if features["coverage_1h"] < 0.99 or features["coverage_3h"] < 0.99 or age > 30:
        support = "limited"
        reasons.append("Rainfall coverage is incomplete or the latest observation is over 30 minutes old.")
    level_age = features["level_age_minutes"]
    if level_age is None or level_age > FRESH_LEVEL_MINUTES:
        support = "limited"
        reasons.append("The local gauge is stale or unavailable; its level is excluded from the warning rule.")
    rainfall = features["rainfall_3h_mm"]
    rain_component = min(100, rainfall / 75 * 100)
    index = round(0.35 * static + 0.65 * rain_component)
    level = "high" if index >= HIGH_INDEX else "elevated" if index >= ELEVATED_INDEX else "low"
    reasons.insert(0, f"{rainfall:.1f} mm of known rainfall in the preceding three hours drives the demo threshold.")
    reasons.append("Terrain and drainage values are synthetic; this relative index is not a flood probability.")
    return {"risk_level": level, "index": index, "susceptibility_index": static,
            "data_support": support, "reasons": reasons}


def run_predictions(db, connection, now):
    created = []
    for area in db.all(connection, "SELECT * FROM areas ORDER BY id"):
        features = feature_snapshot(db, connection, area["id"], now)
        properties = json.loads(area["properties_json"])
        key = fingerprint({"area": area["id"], "features": features["fingerprint"],
                           "geometry": properties["geometry_version"], "rule": RULE_VERSION})
        if db.one(connection, "SELECT id FROM risk_runs WHERE fingerprint = ?", (key,)):
            continue
        latest = db.one(connection, "SELECT issued_at FROM risk_runs WHERE area_id = ? ORDER BY issued_at DESC LIMIT 1", (area["id"],))
        if latest and (features["available_at"] is None or features["available_at"] <= latest["issued_at"]):
            continue
        result = interpret(features, properties)
        # Issue time is when the newest contributing evidence became available,
        # not when a scheduler happened to look at the same data again.
        issue = utc(features["available_at"]) if features["available_at"] else now
        record = {"id": uuid4().hex, "area_id": area["id"], "ward_id": area["ward_id"], "area_name": area["name"],
                  "issued_at": stamp(issue), "valid_from": stamp(issue), "valid_until": stamp(issue + timedelta(hours=3)),
                  "score_type": "relative_susceptibility_index", "mode": "synthetic", "rule_version": RULE_VERSION,
                  "forecast_validated": False, "source_resolution_m": properties["source_resolution_m"],
                  "features": features, "feature_fingerprint": features["fingerprint"], **result}
        db.execute(connection, "INSERT INTO risk_runs VALUES (?, ?, ?, ?, ?, ?)",
                   (record["id"], area["id"], key, record["issued_at"], record["valid_until"], json.dumps(record)))
        created.append(record["id"])
    return created


def read_risks(db, connection, now):
    rows = db.all(connection, "SELECT risk_runs.* FROM risk_runs JOIN "
                  "(SELECT area_id, MAX(issued_at) AS newest FROM risk_runs GROUP BY area_id) latest "
                  "ON risk_runs.area_id = latest.area_id AND risk_runs.issued_at = latest.newest ORDER BY risk_runs.area_id")
    results = []
    seen = set()
    for row in rows:
        if row["area_id"] in seen:
            continue
        seen.add(row["area_id"])
        result = json.loads(row["payload_json"])
        features = result["features"]
        observation = features["rainfall_observed_at"]
        age = (now - utc(observation)).total_seconds() / 60 if observation else None
        expired = utc(result["valid_until"]) <= now
        stale = age is None or age > FRESH_RAIN_MINUTES
        result["rainfall_age_minutes"] = round(age, 1) if age is not None else None
        result["stale"] = stale or expired
        result["expired"] = expired
        if stale or expired:
            result["previous_risk_level"] = result["risk_level"]
            result["previous_index"] = result["index"]
            result.update(risk_level="unknown", index=None, data_support="insufficient")
            result["reasons"] = ["The retained update is stale or expired. Current conditions cannot be estimated reliably.", *result["reasons"]]
        level_time = features["level_observed_at"]
        if level_time and (now - utc(level_time)).total_seconds() / 60 > FRESH_LEVEL_MINUTES and result["data_support"] == "adequate":
            result["data_support"] = "limited"
            result["reasons"] = [*result["reasons"], "The gauge has become stale since this update."]
        result["features"] = {key: value for key, value in features.items() if key != "source_record_ids"}
        results.append(result)
    return results
