from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from threading import Event, Thread
from uuid import uuid4

from shapely.geometry import Point, shape
from shapely.ops import transform

from .alerts import decide_alerts, deliver_alerts
from .config import stamp, utc, wall_now
from .data import ingest
from .geo import PROJECT, area_for_point, calculate_route, expanded_edges
from .prediction import RANK, read_risks, run_predictions


class DomainError(Exception):
    def __init__(self, status: int, detail: str):
        self.status, self.detail = status, detail


class Service:
    def __init__(self, db, settings):
        self.db, self.settings = db, settings
        self.stop = Event()
        self.thread = None

    def now(self, connection=None):
        if connection is None:
            with self.db.transaction() as connection:
                return self.now(connection)
        virtual = utc(self.db.meta(connection, "virtual_anchor"))
        anchor = utc(self.db.meta(connection, "wall_anchor"))
        return virtual + (wall_now() - anchor)

    def audit(self, connection, actor, action, subject, detail=None):
        self.db.execute(connection, "INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?)",
                        (uuid4().hex, actor, action, subject, stamp(self.now(connection)), json.dumps(detail or {})))

    def active_hazards(self, connection, now):
        return self.db.all(connection, "SELECT * FROM hazards WHERE resolved_at IS NULL AND expires_at > ? ORDER BY created_at", (stamp(now),))

    def expire(self, connection, now):
        reports = self.db.all(connection, "SELECT id FROM reports WHERE status IN ('pending', 'verified') AND expires_at <= ?", (stamp(now),))
        for report in reports:
            self.db.execute(connection, "UPDATE reports SET status = 'expired' WHERE id = ?", (report["id"],))
            self.audit(connection, None, "report_expired", report["id"], {"all_clear": False})
        expired_images = self.db.all(connection, "SELECT id, image_file FROM reports WHERE image_file IS NOT NULL AND submitted_at < ?",
                                    (stamp(now - timedelta(days=30)),))
        for report in expired_images:
            self.delete_image(report["image_file"])
            self.db.execute(connection, "UPDATE reports SET image_file = NULL, image_published = 0 WHERE id = ?", (report["id"],))
            self.audit(connection, None, "image_retention_cleanup", report["id"])
        self.db.execute(connection, "DELETE FROM sessions WHERE expires_at <= ?", (stamp(wall_now()),))

    def cycle_in_transaction(self, connection, kind):
        now, job_id = self.now(connection), uuid4().hex
        self.db.execute(connection, "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?)", (job_id, kind, stamp(now), None, "running", "{}"))
        self.expire(connection, now)
        predictions = run_predictions(self.db, connection, now)
        alerts = decide_alerts(self.db, connection, now)
        delivery = deliver_alerts(self.db, connection, now)
        outcome = {"new_risk_records": len(predictions), "new_alerts": alerts, "delivery": delivery}
        self.db.execute(connection, "UPDATE jobs SET finished_at = ?, status = 'complete', details_json = ? WHERE id = ?",
                        (stamp(self.now(connection)), json.dumps(outcome), job_id))
        return outcome

    def cycle(self, kind="scheduler"):
        with self.db.transaction() as connection:
            return self.cycle_in_transaction(connection, kind)

    def start_worker(self):
        def work():
            while not self.stop.wait(self.settings.worker_interval):
                try:
                    self.cycle()
                except Exception as error:
                    # Store error class only; driver messages can contain credentials.
                    with self.db.transaction() as connection:
                        now = stamp(self.now(connection))
                        self.db.execute(connection, "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?)",
                                        (uuid4().hex, "scheduler", now, now, "failed", json.dumps({"error_type": type(error).__name__})))
        self.thread = Thread(target=work, name="floodline-worker", daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=5)

    def areas(self, connection):
        return self.db.all(connection, "SELECT * FROM areas ORDER BY id")

    def area_collection(self, connection):
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "id": area["id"], "geometry": json.loads(area["geometry_json"]),
             "properties": {"id": area["id"], "name": area["name"], "ward_id": area["ward_id"], **json.loads(area["properties_json"])}}
            for area in self.areas(connection)]}

    def network(self, connection):
        roads = self.db.all(connection, "SELECT * FROM road_edges ORDER BY id")
        segments = {}
        for road in roads:
            segment = segments.setdefault(road["segment_id"], {"type": "Feature", "geometry": json.loads(road["geometry_json"]),
                                           "properties": {"id": road["id"], "name": road["name"], "segment_id": road["segment_id"], "edge_ids": []}})
            segment["properties"]["edge_ids"].append(road["id"])
        fixture_nodes = json.loads(self.settings.fixture.read_text(encoding="utf-8"))["nodes"]
        return {"type": "FeatureCollection", "features": list(segments.values()), "nodes": fixture_nodes,
                "projected_crs": "EPSG:32645", "snap_tolerance_m": 250, "mode": "synthetic"}

    def public_report(self, row, now, private=False):
        status = "expired" if row["status"] in ("pending", "verified") and utc(row["expires_at"]) <= now else row["status"]
        result = {key: row[key] for key in ["id", "area_id", "description", "severity", "longitude", "latitude", "observed_at", "submitted_at", "expires_at"]}
        result.update(status=status, synthetic=True, has_image=bool(row["image_file"]),
                      image_available=bool(row["image_file"] and (private or row["image_published"])),
                      image_url=f"/api/reports/{row['id']}/image" if row["image_file"] and (private or row["image_published"]) else None)
        if private:
            result.update(review_reason=row["review_reason"], duplicate_of=row["duplicate_of"])
        return result

    def create_report(self, user, payload):
        with self.db.transaction() as connection:
            now = self.now(connection)
            area = area_for_point(self.areas(connection), payload.longitude, payload.latitude)
            if not area:
                raise DomainError(422, "The report pin must be inside the synthetic study area.")
            if payload.observed_at > now + timedelta(minutes=5):
                raise DomainError(422, "Observation time is more than five minutes ahead of the demo clock.")
            if payload.observed_at < now - timedelta(hours=24):
                raise DomainError(422, "For this prototype, submit observations from the last 24 demo hours.")
            count = self.db.one(connection, "SELECT COUNT(*) AS n FROM reports WHERE user_id = ? AND submitted_at > ?",
                                (user["id"], stamp(now - timedelta(hours=1))))["n"]
            if count >= 10:
                raise DomainError(429, "Ten reports have been submitted in the last demo hour. Please try later.")
            report_id = uuid4().hex
            expires = max(now + timedelta(minutes=15), payload.observed_at + timedelta(hours=2))
            self.db.execute(connection, "INSERT INTO reports(id, user_id, area_id, description, severity, longitude, latitude, observed_at, submitted_at, expires_at, status) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
                            (report_id, user["id"], area["id"], payload.description, payload.severity, payload.longitude, payload.latitude,
                             stamp(payload.observed_at), stamp(now), stamp(expires)))
            self.audit(connection, user["id"], "report_submitted", report_id, {"state": "pending", "no_automatic_road_closure": True})
            row = self.db.one(connection, "SELECT * FROM reports WHERE id = ?", (report_id,))
            return self.public_report(row, now, True)

    def moderate(self, user, report_id, payload):
        with self.db.transaction() as connection:
            now = self.now(connection)
            self.expire(connection, now)
            row = self.db.one(connection, "SELECT * FROM reports WHERE id = ? AND deleted_at IS NULL", (report_id,))
            if not row:
                raise DomainError(404, "Report not found.")
            allowed = row["status"] == "pending" and payload.status in ("verified", "rejected", "duplicate")
            allowed = allowed or (row["status"] == "verified" and payload.status == "resolved")
            if not allowed:
                raise DomainError(409, f"Cannot change a {row['status']} report to {payload.status}.")
            if payload.publish_image and (not payload.privacy_reviewed or not row["image_file"] or payload.status != "verified"):
                raise DomainError(422, "Publishing an image requires an attached image and an explicit privacy review during verification.")
            if payload.status == "duplicate":
                target = self.db.one(connection, "SELECT * FROM reports WHERE id = ? AND deleted_at IS NULL", (payload.duplicate_of,))
                if not target or target["id"] == report_id or target["status"] not in ("pending", "verified"):
                    raise DomainError(422, "Select a different pending or verified report as the duplicate target.")
            if payload.road_edge_ids and payload.status != "verified":
                raise DomainError(422, "Only a verified report can create a road restriction.")
            chosen = []
            if payload.road_edge_ids:
                roads = self.db.all(connection, "SELECT * FROM road_edges")
                try:
                    chosen = expanded_edges(roads, payload.road_edge_ids)
                except ValueError as error:
                    raise DomainError(422, str(error)) from error
                point = transform(PROJECT, Point(row["longitude"], row["latitude"]))
                for road in roads:
                    if road["id"] in chosen and transform(PROJECT, shape(json.loads(road["geometry_json"]))).distance(point) > 150:
                        raise DomainError(422, "A selected segment is over 150 m from the report pin. Review the location instead of guessing.")
            expires = min(now + timedelta(minutes=payload.ttl_minutes), utc(row["observed_at"]) + timedelta(hours=6))
            if payload.status == "verified" and expires <= now:
                raise DomainError(409, "The observation is too old for a new active restriction.")
            self.db.execute(connection, "UPDATE reports SET status = ?, review_reason = ?, duplicate_of = ?, expires_at = ?, image_published = ? WHERE id = ?",
                            (payload.status, payload.reason, payload.duplicate_of if payload.status == "duplicate" else None,
                             stamp(expires), int(payload.publish_image), report_id))
            if chosen:
                self.db.execute(connection, "INSERT INTO hazards VALUES (?, ?, ?, ?, ?, NULL)",
                                (uuid4().hex, report_id, json.dumps(chosen), stamp(now), stamp(expires)))
            if payload.status == "resolved":
                self.db.execute(connection, "UPDATE hazards SET resolved_at = ? WHERE report_id = ? AND resolved_at IS NULL", (stamp(now), report_id))
            self.audit(connection, user["id"], "report_" + payload.status, report_id,
                       {"reason": payload.reason, "edge_ids": chosen, "privacy_reviewed": payload.privacy_reviewed})
            self.cycle_in_transaction(connection, "moderation")
            updated = self.db.one(connection, "SELECT * FROM reports WHERE id = ?", (report_id,))
            return self.public_report(updated, now, True)

    def subscribe(self, user, payload):
        with self.db.transaction() as connection:
            ward_ids = {area["ward_id"] for area in self.areas(connection)}
            if payload.ward_id not in ward_ids:
                raise DomainError(422, "Choose a ward inside the synthetic pilot.")
            now = self.now(connection)
            existing = self.db.one(connection, "SELECT * FROM subscriptions WHERE user_id = ? AND ward_id = ? AND channel = ?",
                                   (user["id"], payload.ward_id, payload.channel))
            subscription_id = existing["id"] if existing else uuid4().hex
            self.db.execute(connection, "INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, 1) ON CONFLICT(user_id, ward_id, channel) "
                            "DO UPDATE SET active = 1, consented_at = excluded.consented_at",
                            (subscription_id, user["id"], payload.ward_id, payload.channel, stamp(now)))
            self.audit(connection, user["id"], "subscription_consented", subscription_id, {"ward_id": payload.ward_id, "channel": "in_app"})
            self.cycle_in_transaction(connection, "subscription")
            return {"id": subscription_id, "ward_id": payload.ward_id, "channel": "in_app", "active": True}

    def route(self, payload):
        with self.db.transaction() as connection:
            now = self.now(connection)
            result = calculate_route(self.areas(connection), self.db.all(connection, "SELECT * FROM road_nodes"),
                                     self.db.all(connection, "SELECT * FROM road_edges"), self.active_hazards(connection, now),
                                     (payload.start.longitude, payload.start.latitude), (payload.end.longitude, payload.end.latitude))
            result.update(calculated_at=stamp(now), mode="synthetic")
            return result

    def scenario(self, user, name):
        if name not in ("normal", "storm", "outage", "recovery"):
            raise DomainError(404, "Unknown synthetic scenario.")
        with self.db.transaction() as connection:
            now = self.now(connection) + timedelta(minutes=105 if name == "outage" else 15)
            self.db.set_meta(connection, "virtual_anchor", stamp(now))
            self.db.set_meta(connection, "wall_anchor", stamp(wall_now()))
            self.db.set_meta(connection, "scenario", name)
            outcome = {"accepted": 0, "duplicates": 0, "quarantined": 0}
            if name != "outage":
                records = []
                for area in self.areas(connection):
                    centroid = shape(json.loads(area["geometry_json"])).centroid
                    end = (now - timedelta(minutes=2)).replace(second=0, microsecond=0)
                    end = end.replace(minute=(end.minute // 15) * 15)
                    # Refill a complete three-hour history after an outage, visibly synthetic.
                    for index in range(12):
                        observed = end - timedelta(minutes=index * 15)
                        rain = (12 + (ord(area["ward_id"]) - 65) * 3) if name in ("storm", "recovery") else 0.5
                        records.append({"source_record_key": f"{name}-{stamp(now)}-{area['id']}-{index}", "source_id": "demo-rain", "area_id": area["id"],
                                        "observed_at": stamp(observed), "received_at": stamp(now), "variable": "rainfall", "value": rain,
                                        "unit": "mm", "quality": "good", "interval_minutes": 15, "longitude": centroid.x, "latitude": centroid.y})
                    records.append({"source_record_key": f"{name}-{stamp(now)}-{area['id']}-gauge", "source_id": "demo-level", "area_id": area["id"],
                                    "observed_at": stamp(now - timedelta(minutes=2)), "received_at": stamp(now), "variable": "water_level", "value": 4.8 if name != "normal" else 2.4,
                                    "unit": "m", "quality": "good", "interval_minutes": 15, "longitude": centroid.x, "latitude": centroid.y})
                outcome = ingest(self.db, connection, records)
            self.audit(connection, user["id"], "synthetic_scenario", name, {"ingestion": outcome})
            cycle = self.cycle_in_transaction(connection, "scenario-" + name)
            return {"scenario": name, "clock": stamp(now), "ingestion": outcome, **cycle}

    def delete_image(self, filename):
        if not filename:
            return
        folder = (self.settings.runtime / "images").resolve()
        path = (folder / filename).resolve()
        if path.parent != folder:
            raise ValueError("Image path is outside private storage.")
        path.unlink(missing_ok=True)
