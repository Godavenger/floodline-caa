from __future__ import annotations

import io
import csv
import json
import sqlite3
import tempfile
import unittest
import warnings
from datetime import timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch

from PIL import Image
from fastapi.testclient import TestClient

from backend.floodline.config import ROOT, Settings, stamp, utc, wall_now
from backend.floodline.data import feature_snapshot, ingest
from backend.floodline.database import Database
from backend.floodline.evaluation import create_synthetic_experiment, eligible_rows, temporal_event_split
from backend.floodline.geo import calculate_route, metric_distance
from backend.floodline.main import create_app
from backend.floodline.prediction import run_predictions

warnings.filterwarnings("ignore", category=DeprecationWarning, module="starlette")


class PipelineAcceptance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="floodline-test-")
        self.settings = Settings(runtime=Path(self.temp.name), database_url="", worker_enabled=False)
        self.app = create_app(self.settings)
        self.client = TestClient(self.app, headers={"X-Floodline-Client": "web"})
        self.client.__enter__()
        self.db, self.service = self.app.state.db, self.app.state.service
        self.client.post("/api/auth/guest")

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def login(self):
        response = self.client.post("/api/auth/login", json={"username": "moderator", "password": "floodline-demo"})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def advance(self, minutes):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "virtual_anchor", stamp(self.service.now(connection) + timedelta(minutes=minutes)))
            self.db.set_meta(connection, "wall_anchor", stamp(wall_now()))

    def report(self, **changes):
        payload = {"description": "Synthetic test observation: standing water affects this junction.", "severity": "water_on_road",
                   "observed_at": stamp(self.service.now()), "longitude": 88.341, "latitude": 22.571, **changes}
        response = self.client.post("/api/reports", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def route(self, start="n0-1", end="n4-1"):
        nodes = {node["id"]: node for node in self.client.get("/api/network").json()["nodes"]}
        point = lambda node: {"longitude": nodes[node]["longitude"], "latitude": nodes[node]["latitude"]}
        return self.client.post("/api/routes", json={"start": point(start), "end": point(end)}).json()

    def raw_observation(self, **changes):
        return {"source_record_key": "new-test-record", "source_id": "demo-rain", "area_id": "A1", "longitude": 88.3305, "latitude": 22.565,
                "observed_at": stamp(self.service.now() - timedelta(minutes=2)), "received_at": stamp(self.service.now()),
                "variable": "rainfall", "value": 3.0, "unit": "mm", "quality": "good", "interval_minutes": 15, **changes}

    def test_shared_fixture_and_scope_gate(self):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"], {"cells": 9, "warnings": 3, "unknown": 1, "active_hazards": 1})
        self.assertEqual(len(data["wards"]), 3)
        self.assertEqual(len(data["network"]["features"]), 31)
        self.assertFalse(data["forecast_validated"])

    def test_initial_duplicate_and_quarantine_counts(self):
        self.login()
        result = self.client.get("/api/admin/operations").json()["initial_ingestion"]
        self.assertEqual(result["accepted"], 866)
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual(result["quarantined"], 2)

    def test_unit_conversion_and_idempotency(self):
        raw = self.raw_observation(unit="cm", value=1.25)
        with self.db.transaction() as connection:
            first = ingest(self.db, connection, [raw, raw])
            value = self.db.one(connection, "SELECT value, unit FROM observations WHERE source_key = ?", ("demo-rain:new-test-record",))
        self.assertEqual(first["accepted"], 1)
        self.assertEqual(first["duplicates"], 1)
        self.assertEqual(value, {"value": 12.5, "unit": "mm"})

    def test_conflicting_source_key_is_quarantined(self):
        with self.db.transaction() as connection:
            raw = self.raw_observation()
            ingest(self.db, connection, [raw])
            result = ingest(self.db, connection, [dict(raw, value=10)])
        self.assertEqual(result["quarantined"], 1)
        self.assertIn("conflicts", result["reasons"][0])

    def test_invalid_values_do_not_become_zero(self):
        for key, change in [("negative", {"value": -1}), ("unit", {"unit": "m/s"}), ("coordinates", {"latitude": 80}),
                            ("interval", {"interval_minutes": 5}), ("naive-time", {"observed_at": "2026-11-11T08:30:00"})]:
            with self.subTest(key=key), self.db.transaction() as connection:
                result = ingest(self.db, connection, [self.raw_observation(source_record_key=key, **change)])
                self.assertEqual(result["accepted"], 0)
                self.assertEqual(result["quarantined"], 1)

    def test_explicit_missing_value_remains_null(self):
        with self.db.transaction() as connection:
            result = ingest(self.db, connection, [self.raw_observation(value=None, quality="missing")])
            row = self.db.one(connection, "SELECT value, quality FROM observations WHERE source_key = ?", ("demo-rain:new-test-record",))
        self.assertEqual(result["accepted"], 1)
        self.assertEqual(row, {"value": None, "quality": "missing"})

    def test_delayed_receipts_do_not_leak_into_features(self):
        issue = self.service.now()
        raw = self.raw_observation(source_record_key="late-test", observed_at="2026-11-11T08:00:00Z", received_at=stamp(issue + timedelta(minutes=10)), value=90)
        with self.db.transaction() as connection:
            before = feature_snapshot(self.db, connection, "A1", issue)
            ingest(self.db, connection, [raw])
            earlier = feature_snapshot(self.db, connection, "A1", issue)
            later = feature_snapshot(self.db, connection, "A1", issue + timedelta(minutes=11))
        self.assertEqual(before["rainfall_3h_mm"], earlier["rainfall_3h_mm"])
        self.assertGreater(later["rainfall_3h_mm"], earlier["rainfall_3h_mm"])

    def test_missing_cell_has_no_numeric_probability(self):
        risk = self.client.get("/api/risk?area_id=C3").json()["items"][0]
        self.assertEqual(risk["risk_level"], "unknown")
        self.assertEqual(risk["data_support"], "insufficient")
        self.assertIsNone(risk["index"])
        self.assertNotIn("probability", risk)

    def test_scheduler_does_not_manufacture_fresh_issue_times(self):
        before = self.client.get("/api/risk?area_id=A1").json()["items"][0]
        self.advance(100)
        self.service.cycle()
        after = self.client.get("/api/risk?area_id=A1").json()["items"][0]
        self.assertEqual(after["issued_at"], before["issued_at"])
        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["risk_level"], "unknown")
        self.assertIsNone(after["index"])
        self.assertTrue(after["stale"])

    def test_worker_records_inference_failure_and_recovers_without_duplicates(self):
        self.client.post("/api/subscriptions", json={"ward_id": "B", "consented": True})
        before_risks = self.client.get("/api/risk").json()["items"]
        before_alerts = self.client.get("/api/alerts").json()["items"]
        recovered = Event()
        calls = 0

        def fail_once(*arguments):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("Synthetic private credential must never enter job logs")
            result = run_predictions(*arguments)
            recovered.set()
            return result

        self.settings.worker_interval = 0.01
        with patch("backend.floodline.service.run_predictions", side_effect=fail_once):
            self.service.start_worker()
            try:
                self.assertTrue(recovered.wait(3), "The worker did not resume after a failed inference cycle.")
            finally:
                self.service.close()
        self.assertEqual(self.client.get("/api/risk").json()["items"], before_risks)
        self.assertEqual(self.client.get("/api/alerts").json()["items"], before_alerts)
        with self.db.transaction() as connection:
            failures = self.db.all(connection, "SELECT details_json FROM jobs WHERE status = 'failed'")
            self.assertEqual(len(failures), 1)
            self.assertEqual(json.loads(failures[0]["details_json"]), {"error_type": "RuntimeError"})
            self.assertEqual(self.db.one(connection, "SELECT COUNT(*) AS n FROM jobs WHERE status = 'running'")["n"], 0)

    def test_pending_report_is_private_and_does_not_close_roads(self):
        report = self.report()
        self.assertEqual(report["status"], "pending")
        public = self.client.get("/api/reports").json()["items"]
        self.assertNotIn(report["id"], [row["id"] for row in public])
        self.assertIn(report["id"], [row["id"] for row in self.client.get("/api/reports?mine=true").json()["items"]])
        self.assertEqual(self.client.get("/api/dashboard").json()["summary"]["active_hazards"], 1)

    def test_payload_validation_future_and_outside_location(self):
        for change in [{"latitude": 20}, {"observed_at": stamp(self.service.now() + timedelta(minutes=10))},
                       {"observed_at": "2026-11-11T08:30:00"}, {"user_id": "forged-user"}, {"description": "tiny"}]:
            with self.subTest(change=change):
                payload = {"description": "Synthetic test observation at a mapped junction.", "severity": "unknown", "observed_at": stamp(self.service.now()), "latitude": 22.571, "longitude": 88.341, **change}
                self.assertEqual(self.client.post("/api/reports", json=payload).status_code, 422)

    def test_authentication_and_role_guards(self):
        outsider = TestClient(self.app, headers={"X-Floodline-Client": "web"})
        self.assertEqual(outsider.post("/api/reports/demo-pending-east/moderate", json={"status": "verified", "reason": "Sufficient synthetic evidence."}).status_code, 401)
        self.assertEqual(self.client.get("/api/admin/operations").status_code, 403)
        self.assertEqual(self.client.post("/api/reports/demo-pending-east/moderate", json={"status": "verified", "reason": "Sufficient synthetic evidence."}).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/login", json={"username": "moderator", "password": "wrong"}).status_code, 401)

    def test_csrf_marker_and_origin_validation(self):
        self.assertEqual(self.client.post("/api/auth/guest", headers={"X-Floodline-Client": ""}).status_code, 403)
        self.assertEqual(self.client.post("/api/auth/guest", headers={"Origin": "https://unrelated.example"}).status_code, 403)
        cookie = self.client.cookies.get("fl_session")
        self.assertTrue(cookie)

    def test_moderator_signout_retains_resident_ownership(self):
        report = self.report()
        resident_cookie = self.client.cookies.get("fl_session")
        self.login()
        self.client.post("/api/auth/logout")
        self.assertEqual(self.client.cookies.get("fl_session"), resident_cookie)
        self.assertEqual(self.client.get("/api/auth/session").json()["role"], "resident")
        self.assertIn(report["id"], [row["id"] for row in self.client.get("/api/reports?mine=true").json()["items"]])

    def test_ownership_checks_for_correction_withdrawal_and_subscription(self):
        report = self.report()
        subscription = self.client.post("/api/subscriptions", json={"ward_id": "C", "channel": "in_app", "consented": True}).json()
        other = TestClient(self.app, headers={"X-Floodline-Client": "web"})
        other.post("/api/auth/guest")
        self.assertEqual(other.patch(f"/api/reports/{report['id']}", json={"description": "Another resident cannot edit this."}).status_code, 404)
        self.assertEqual(other.delete(f"/api/reports/{report['id']}").status_code, 404)
        self.assertEqual(other.delete(f"/api/subscriptions/{subscription['id']}").status_code, 404)
        self.assertEqual(other.get("/api/alerts").json()["items"], [])

    def test_correction_and_withdrawal(self):
        report = self.report()
        response = self.client.patch(f"/api/reports/{report['id']}", json={"description": "Corrected synthetic evidence with a clearer street location."})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["description"].startswith("Corrected"))
        self.assertEqual(self.client.delete(f"/api/reports/{report['id']}").status_code, 200)
        self.assertEqual(self.client.get("/api/reports?mine=true").json()["items"], [])

    def test_verification_creates_bounded_bidirectional_exclusions(self):
        report = self.report(longitude=88.3475)
        self.login()
        response = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "verified", "reason": "Reviewed synthetic location and road impact.", "road_edge_ids": ["road-n3-1-n4-1"], "ttl_minutes": 120})
        self.assertEqual(response.status_code, 200, response.text)
        data = self.client.get("/api/dashboard").json()
        hazard = next(item for item in data["hazards"] if item["report_id"] == report["id"])
        self.assertEqual(set(hazard["edge_ids"]), {"road-n3-1-n4-1", "road-n3-1-n4-1-r"})
        route = self.route()
        self.assertEqual(route["status"], "available")
        self.assertFalse(set(route["edge_ids"]) & set(hazard["edge_ids"]))
        with self.db.transaction() as connection:
            self.assertEqual(self.db.one(connection, "SELECT COUNT(*) AS n FROM events")["n"], 1)

    def test_distant_road_match_rejected_atomically(self):
        report = self.report()
        self.login()
        response = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "verified", "reason": "Synthetic reviewer attempted a distant road match.", "road_edge_ids": ["road-n4-2-n4-3"]})
        self.assertEqual(response.status_code, 422)
        with self.db.transaction() as connection:
            row = self.db.one(connection, "SELECT status FROM reports WHERE id = ?", (report["id"],))
            self.assertEqual(row["status"], "pending")

    def test_resolution_and_expiry_do_not_assert_all_clear(self):
        self.login()
        result = self.client.post("/api/reports/demo-verified-market/moderate", json={"status": "resolved", "reason": "Synthetic reviewer confirms the restriction is resolved."})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard").json()["summary"]["active_hazards"], 0)
        self.assertIn("Other hazards", self.route()["message"])

    def test_duplicate_requires_existing_target(self):
        report = self.report()
        self.login()
        response = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "duplicate", "reason": "This matches an existing reviewed report.", "duplicate_of": "nonexistent"})
        self.assertEqual(response.status_code, 422)
        response = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "duplicate", "reason": "This matches the existing synthetic Market report.", "duplicate_of": "demo-verified-market"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "duplicate")

    def test_uploaded_image_is_cleaned_and_private(self):
        report = self.report()
        image = Image.new("RGB", (20, 30), "#087f82")
        exif = Image.Exif(); exif[270] = "Private location-bearing caption"; exif[271] = "Private device name"; exif[274] = 6
        content = io.BytesIO(); image.save(content, "JPEG", exif=exif)
        response = self.client.post(f"/api/reports/{report['id']}/image", files={"image": ("original-location.jpg", content.getvalue(), "image/jpeg")})
        self.assertEqual(response.status_code, 200, response.text)
        decoded = Image.open(io.BytesIO(self.client.get(response.json()["image_url"]).content))
        self.assertFalse(decoded.getexif())
        self.assertEqual(decoded.size, (30, 20))
        self.assertEqual(TestClient(self.app).get(response.json()["image_url"]).status_code, 404)
        self.login()
        forbidden = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "verified", "reason": "Synthetic image reviewed for relevance.", "publish_image": True})
        self.assertEqual(forbidden.status_code, 422)
        allowed = self.client.post(f"/api/reports/{report['id']}/moderate", json={"status": "verified", "reason": "Plain synthetic pixels contain no identifying details.", "publish_image": True, "privacy_reviewed": True})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(TestClient(self.app).get(response.json()["image_url"]).status_code, 200)

    def test_non_image_and_oversize_upload_rejected(self):
        report = self.report()
        for content, expected in [(b"not an image", 422), (b"x" * (5 * 1024 * 1024 + 1), 413)]:
            response = self.client.post(f"/api/reports/{report['id']}/image", files={"image": ("evidence.jpg", content, "image/jpeg")})
            self.assertEqual(response.status_code, expected)

    def test_processed_image_retention_cleans_file_and_preserves_audit(self):
        report = self.report()
        content = io.BytesIO()
        Image.new("RGB", (20, 20), "#087f82").save(content, "PNG")
        attached = self.client.post(f"/api/reports/{report['id']}/image", files={"image": ("synthetic.png", content.getvalue(), "image/png")})
        self.assertEqual(attached.status_code, 200)
        with self.db.transaction() as connection:
            image_file = self.db.one(connection, "SELECT image_file FROM reports WHERE id = ?", (report["id"],))["image_file"]
        image_path = self.settings.runtime / "images" / image_file
        self.assertTrue(image_path.is_file())
        self.advance(30 * 24 * 60 + 1)
        self.service.cycle()
        self.assertFalse(image_path.exists())
        self.assertEqual(self.client.get(attached.json()["image_url"]).status_code, 404)
        with self.db.transaction() as connection:
            stored = self.db.one(connection, "SELECT description, image_file, image_published FROM reports WHERE id = ?", (report["id"],))
            self.assertEqual(stored["description"], report["description"])
            self.assertIsNone(stored["image_file"])
            self.assertEqual(stored["image_published"], 0)
            self.assertIsNotNone(self.db.one(connection, "SELECT id FROM audit WHERE subject_id = ? AND action = 'image_retention_cleanup'", (report["id"],)))

    def test_route_avoids_active_closure(self):
        route = self.route()
        self.assertEqual(route["status"], "available")
        self.assertFalse(set(route["edge_ids"]) & set(route["excluded_edge_ids"]))
        self.assertIn("road-n2-1-n3-1", route["excluded_edge_ids"])

    def test_disconnected_same_node_and_outside_routes(self):
        self.assertEqual(self.route(end="island")["status"], "unavailable")
        same = self.route(end="n0-1")
        self.assertEqual(same["distance_m"], 0)
        self.assertEqual(len(same["geometry"]["coordinates"]), 2)
        outside = self.client.post("/api/routes", json={"start": {"longitude": 88.4, "latitude": 22.6}, "end": {"longitude": 88.341, "latitude": 22.571}}).json()
        self.assertEqual(outside["status"], "outside_pilot")

    def test_unsnappable_route_point(self):
        result = self.client.post("/api/routes", json={"start": {"longitude": 88.325, "latitude": 22.560}, "end": {"longitude": 88.354, "latitude": 22.571}}).json()
        self.assertEqual(result["status"], "unsnappable")

    def test_all_connections_blocked_never_restores_edges(self):
        with self.db.transaction() as connection:
            edges = [row["id"] for row in self.db.all(connection, "SELECT id FROM road_edges WHERE source_node = 'n0-1'")]
            now = self.service.now(connection)
            self.db.execute(connection, "INSERT INTO hazards VALUES (?, ?, ?, ?, ?, NULL)", ("test-blocked", "demo-verified-market", json.dumps(edges), stamp(now), stamp(now + timedelta(hours=1))))
        result = self.route()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("No route avoiding", result["message"])

    def test_expired_hazard_removed_without_claiming_clear_roads(self):
        self.advance(105)
        result = self.route()
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["excluded_edge_ids"], [])
        self.assertIn("road-n2-1-n3-1", result["edge_ids"])
        self.assertIn("Other hazards", result["message"])

    def test_consent_and_idempotent_subscription(self):
        self.assertEqual(self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": False}).status_code, 422)
        payload = {"ward_id": "C", "channel": "in_app", "consented": True}
        first = self.client.post("/api/subscriptions", json=payload).json()
        second = self.client.post("/api/subscriptions", json=payload).json()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.client.get("/api/alerts").json()["items"]), 1)
        self.service.cycle()
        self.assertEqual(len(self.client.get("/api/alerts").json()["items"]), 1)

    def test_failed_delivery_retries_with_backoff_and_expiry(self):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "fail_next_deliveries", 1)
        self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": True})
        first = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(first["state"], "failed")
        self.assertEqual(first["attempts"], 1)
        self.advance(1); self.service.cycle()
        sent = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(sent["state"], "sent")
        self.assertEqual(sent["attempts"], 2)
        self.advance(200); self.service.cycle()
        self.assertEqual(self.client.get("/api/alerts").json()["items"][0]["state"], "expired")

    def test_delivery_attempts_bounded(self):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "fail_next_deliveries", 10)
        self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": True})
        for _ in range(5):
            self.advance(3); self.service.cycle()
        alert = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(alert["attempts"], 3)
        self.assertEqual(alert["state"], "failed")
        self.assertIsNone(alert["next_attempt_at"])

    def test_stale_evidence_stops_retry_before_alert_expiry(self):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "fail_next_deliveries", 1)
        self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": True})
        self.advance(100); self.service.cycle()
        alert = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(alert["state"], "cancelled")
        self.assertEqual(alert["attempts"], 1)
        self.assertFalse(alert["evidence_current"])

    def test_unsubscribe_cancels_queued_retry(self):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "fail_next_deliveries", 1)
        subscription = self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": True}).json()
        self.client.delete(f"/api/subscriptions/{subscription['id']}")
        self.advance(2); self.service.cycle()
        alert = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(alert["state"], "cancelled")
        self.assertEqual(alert["attempts"], 1)

    def test_new_low_risk_evidence_cancels_pending_warning_retry(self):
        with self.db.transaction() as connection:
            self.db.set_meta(connection, "fail_next_deliveries", 1)
        self.client.post("/api/subscriptions", json={"ward_id": "C", "consented": True})
        initial = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(initial["state"], "failed")
        self.login()
        self.client.post("/api/admin/scenarios/normal")
        self.client.post("/api/auth/logout")
        alert = next(item for item in self.client.get("/api/alerts").json()["items"] if item["id"] == initial["id"])
        self.assertEqual(alert["state"], "cancelled")
        self.assertEqual(alert["attempts"], 1)
        self.assertFalse(alert["evidence_current"])
        self.assertIsNone(alert["next_attempt_at"])

    def test_offline_api_reference_and_missing_frontend(self):
        reference = self.client.get("/docs")
        self.assertEqual(reference.status_code, 200)
        self.assertIn("/openapi.json", reference.text)
        self.assertIn("/api/reports", reference.text)
        self.assertNotIn("cdn.jsdelivr.net", reference.text)
        settings = Settings(runtime=Path(self.temp.name), database_url="", worker_enabled=False,
                            frontend=Path(self.temp.name) / "unbuilt-frontend")
        unbuilt = TestClient(create_app(settings))
        self.assertEqual(unbuilt.get("/").status_code, 503)

    def test_severity_increase_bypasses_cooldown_and_unchanged_repeat_does_not(self):
        self.client.post("/api/subscriptions", json={"ward_id": "B", "consented": True})
        initial = self.client.get("/api/alerts").json()["items"]
        self.login()
        self.client.post("/api/admin/scenarios/storm")
        self.client.post("/api/auth/logout")
        after = self.client.get("/api/alerts").json()["items"]
        self.assertGreater(len(after), len(initial))
        self.service.cycle()
        self.assertEqual(len(self.client.get("/api/alerts").json()["items"]), len(after))

    def test_outage_and_recovery_keep_unknown_and_no_false_freshness(self):
        self.login()
        before = self.client.get("/api/risk?area_id=A1").json()["items"][0]
        self.client.post("/api/admin/scenarios/outage")
        after = self.client.get("/api/risk?area_id=A1").json()["items"][0]
        self.assertEqual(before["issued_at"], after["issued_at"])
        self.assertEqual(after["risk_level"], "unknown")
        self.client.post("/api/admin/scenarios/recovery")
        recovered = self.client.get("/api/risk?area_id=A1").json()["items"][0]
        self.assertNotEqual(recovered["issued_at"], before["issued_at"])
        self.assertFalse(recovered["stale"])

    def test_database_backup_restore_and_migration_idempotency(self):
        self.db.migrate()
        destination = Path(self.temp.name) / "snapshot.db"
        self.db.backup(destination)
        restored = Database("sqlite:///" + str(destination))
        restored.migrate()
        with restored.transaction() as connection:
            self.assertEqual(restored.one(connection, "SELECT COUNT(*) AS n FROM areas")["n"], 9)
            self.assertEqual(restored.one(connection, "SELECT COUNT(*) AS n FROM schema_migrations")["n"], 1)
            self.assertEqual(restored.one(connection, "PRAGMA integrity_check")["integrity_check"], "ok")

    def test_database_transaction_rolls_back_related_writes(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.transaction() as connection:
                self.db.set_meta(connection, "should-rollback", True)
                self.db.execute(connection, "INSERT INTO sessions VALUES ('invalid', 'missing-user', 'now', 'later')")
        with self.db.transaction() as connection:
            self.assertIsNone(self.db.meta(connection, "should-rollback"))

    def test_no_training_promotion_and_no_private_fields_in_public_reports(self):
        evaluation = self.client.get("/api/evaluation").json()
        self.assertFalse(evaluation["historical_accuracy_established"])
        report = self.client.get("/api/reports").json()["items"][0]
        self.assertNotIn("user_id", report)
        self.assertNotIn("image_file", report)
        self.assertNotIn("review_reason", report)


class GeographicAndEvaluationChecks(unittest.TestCase):
    def test_positive_onsets_must_follow_issue_time(self):
        with tempfile.TemporaryDirectory() as directory:
            path = create_synthetic_experiment(Path(directory) / "experiment.csv")
            rows, _, _ = eligible_rows(path)
            self.assertTrue(all(utc(row["issued_at"]) < utc(row["onset"]) <= utc(row["label_window_end"])
                                for row in rows if row["label"] == "1"))
            with path.open(newline="", encoding="utf-8") as handle:
                records = list(csv.DictReader(handle))
            positive = next(row for row in records if str(row["label"]) == "1")
            positive["onset"] = positive["issued_at"]
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(records[0]))
                writer.writeheader(); writer.writerows(records)
            with self.assertRaisesRegex(ValueError, "future target window"):
                eligible_rows(path)

    def test_projected_distance_and_directed_one_way_graph(self):
        self.assertTrue(650 < metric_distance((88.328, 22.563), (88.3345, 22.563)) < 700)
        fixture = json.loads((ROOT / "data/fixtures/pilot.json").read_text())
        areas = [{**area, "geometry_json": json.dumps(area["geometry"])} for area in fixture["areas"]]
        roads = [{**road, "geometry_json": json.dumps(road["geometry"])} for road in fixture["roads"] if road["segment_id"] == "road-n0-0-n1-0"]
        first, last = (88.328, 22.563), (88.3345, 22.563)
        self.assertEqual(calculate_route(areas, fixture["nodes"], roads, [], first, last)["status"], "available")
        self.assertEqual(calculate_route(areas, fixture["nodes"], roads, [], last, first)["status"], "unavailable")

    def test_temporal_split_preserves_events_and_excludes_unknowns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = create_synthetic_experiment(Path(directory) / "experiment.csv")
            rows, excluded, mode = eligible_rows(path)
            blocks, manifest = temporal_event_split(rows)
        self.assertEqual(mode, "synthetic")
        self.assertGreater(excluded["unknown_label"], 0)
        ids = [set(manifest[name]["event_ids"]) for name in ["train", "validation", "test"]]
        self.assertFalse(ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])
        self.assertEqual(sum(len(blocks[name]) for name in blocks), len(rows))
        self.assertLess(max(utc(row["label_window_end"]) for row in blocks["train"]), min(utc(row["issued_at"]) for row in blocks["validation"]) - timedelta(hours=24))


if __name__ == "__main__":
    unittest.main(verbosity=2)
