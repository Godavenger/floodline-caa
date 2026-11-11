from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

from .config import stamp, utc
from .data import fingerprint
from .prediction import CLEAR_INDEX, FRESH_RAIN_MINUTES, RANK, read_risks

COOLDOWN_MINUTES = 30
MAX_ATTEMPTS = 3


def evidence_current(db, connection, alert, now, risks=None):
    if utc(alert["expires_at"]) <= now:
        return False
    if alert["kind"] == "observed_hazard":
        return bool(db.one(connection, "SELECT id FROM hazards WHERE id = ? AND resolved_at IS NULL AND expires_at > ?",
                           (alert["trigger_id"], stamp(now))))
    if alert["kind"] != "threshold_warning":
        return False
    row = db.one(connection, "SELECT payload_json FROM risk_runs WHERE id = ?", (alert["trigger_id"],))
    payload = json.loads(row["payload_json"]) if row else None
    observed = payload["features"]["rainfall_observed_at"] if payload else None
    if observed is None or now - utc(observed) > timedelta(minutes=FRESH_RAIN_MINUTES):
        return False
    current = next((risk for risk in (risks if risks is not None else read_risks(db, connection, now))
                    if risk["area_id"] == payload["area_id"]), None)
    return bool(current and not current["stale"] and current["data_support"] != "insufficient"
                and current["risk_level"] in ("elevated", "high")
                and RANK[current["risk_level"]] >= RANK[alert["severity"]])


def decide_alerts(db, connection, now):
    risks = read_risks(db, connection, now)
    subscriptions = db.all(connection, "SELECT * FROM subscriptions WHERE active = 1")
    created = 0
    for subscription in subscriptions:
        relevant = [risk for risk in risks if risk["ward_id"] == subscription["ward_id"] and not risk["stale"]]
        strongest = max(relevant, key=lambda risk: RANK[risk["risk_level"]], default=None)
        state = db.one(connection, "SELECT * FROM alert_state WHERE subscription_id = ?", (subscription["id"],))
        if strongest and strongest["index"] is not None and strongest["index"] < CLEAR_INDEX:
            db.execute(connection, "INSERT INTO alert_state VALUES (?, 'low', NULL, NULL) "
                       "ON CONFLICT(subscription_id) DO UPDATE SET active_severity = 'low'", (subscription["id"],))
        if strongest and strongest["risk_level"] in ("elevated", "high") and strongest["data_support"] != "insufficient":
            severity = strongest["risk_level"]
            increased = state is None or RANK[severity] > RANK.get(state["active_severity"], -1)
            in_cooldown = bool(state and state["last_notified_at"] and now - utc(state["last_notified_at"]) < timedelta(minutes=COOLDOWN_MINUTES))
            if increased or not in_cooldown:
                key = fingerprint({"subscription": subscription["id"], "trigger": strongest["id"], "message_version": "en-demo-v1"})
                ward = strongest["area_name"].split(" · ")[0]
                message = (f"Synthetic prototype: {ward} has {severity} waterlogging warning conditions. "
                           f"Known recent rainfall is {strongest['features']['rainfall_3h_mm']:.1f} mm over three hours. "
                           f"Data support is {strongest['data_support']}. This is a demo threshold index, not a validated forecast. "
                           "Avoid segments with current verified reports and check official local advisories. "
                           f"Issued {strongest['issued_at']}; valid until {strongest['valid_until']}.")
                cursor = db.execute(connection, "INSERT INTO alerts(id, user_id, subscription_id, ward_id, kind, severity, trigger_id, idempotency_key, state, next_attempt_at, issued_at, expires_at, message, support) "
                                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(idempotency_key) DO NOTHING",
                                    (uuid4().hex, subscription["user_id"], subscription["id"], subscription["ward_id"], "threshold_warning", severity,
                                     strongest["id"], key, "queued", stamp(now), strongest["issued_at"], strongest["valid_until"], message, strongest["data_support"]))
                if cursor.rowcount:
                    created += 1
                    db.execute(connection, "INSERT INTO alert_state VALUES (?, ?, ?, ?) ON CONFLICT(subscription_id) DO UPDATE SET "
                               "active_severity = excluded.active_severity, last_notified_at = excluded.last_notified_at, last_trigger = excluded.last_trigger",
                               (subscription["id"], severity, stamp(now), strongest["id"]))
        hazards = db.all(connection, "SELECT hazards.*, reports.area_id, reports.description FROM hazards JOIN reports ON reports.id = hazards.report_id "
                         "JOIN areas ON areas.id = reports.area_id WHERE areas.ward_id = ? AND hazards.resolved_at IS NULL AND hazards.expires_at > ?",
                         (subscription["ward_id"], stamp(now)))
        for hazard in hazards:
            key = fingerprint({"subscription": subscription["id"], "hazard": hazard["id"], "message_version": "observed-en-v1"})
            message = ("Synthetic prototype: a reviewed waterlogging report restricts a mapped road segment in your chosen ward. "
                       "The route planner excludes this observed hazard. Other conditions may be unreported. "
                       f"Observed evidence is separate from the risk index. Valid until {hazard['expires_at']}.")
            cursor = db.execute(connection, "INSERT INTO alerts(id, user_id, subscription_id, ward_id, kind, severity, trigger_id, idempotency_key, state, next_attempt_at, issued_at, expires_at, message, support) "
                                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(idempotency_key) DO NOTHING",
                                (uuid4().hex, subscription["user_id"], subscription["id"], subscription["ward_id"], "observed_hazard", "high", hazard["id"],
                                 key, "queued", stamp(now), hazard["created_at"], hazard["expires_at"], message, "reviewed_synthetic_evidence"))
            created += int(cursor.rowcount > 0)
    return created


def deliver_alerts(db, connection, now):
    db.execute(connection, "UPDATE alerts SET state = 'expired', next_attempt_at = NULL WHERE expires_at <= ? AND state != 'expired'", (stamp(now),))
    # Consent can be withdrawn while a send is queued or retrying.
    db.execute(connection, "UPDATE alerts SET state = 'cancelled', next_attempt_at = NULL WHERE state IN ('queued', 'failed') "
               "AND subscription_id IN (SELECT id FROM subscriptions WHERE active = 0)")
    jobs = db.all(connection, "SELECT * FROM alerts WHERE state IN ('queued', 'failed') AND attempts < ? "
                  "AND next_attempt_at IS NOT NULL AND next_attempt_at <= ? AND expires_at > ?", (MAX_ATTEMPTS, stamp(now), stamp(now)))
    counts = {"sent": 0, "failed": 0}
    risks = read_risks(db, connection, now) if jobs else []
    for alert in jobs:
        if not evidence_current(db, connection, alert, now, risks):
            db.execute(connection, "UPDATE alerts SET state = 'cancelled', next_attempt_at = NULL WHERE id = ?", (alert["id"],))
            db.execute(connection, "INSERT INTO audit VALUES (?, NULL, ?, ?, ?, ?)",
                       (uuid4().hex, "delivery_cancelled_obsolete_evidence", alert["id"], stamp(now), json.dumps({"all_clear": False})))
            continue
        fail_next = db.meta(connection, "fail_next_deliveries", 0)
        attempt = alert["attempts"] + 1
        if fail_next:
            db.set_meta(connection, "fail_next_deliveries", fail_next - 1)
            retry = stamp(now + timedelta(seconds=30 * 2 ** (attempt - 1))) if attempt < MAX_ATTEMPTS else None
            db.execute(connection, "UPDATE alerts SET state = 'failed', attempts = ?, next_attempt_at = ? WHERE id = ?", (attempt, retry, alert["id"]))
            counts["failed"] += 1
        else:
            db.execute(connection, "UPDATE alerts SET state = 'sent', attempts = ?, next_attempt_at = NULL, sent_at = ? WHERE id = ?",
                       (attempt, stamp(now), alert["id"]))
            counts["sent"] += 1
        db.execute(connection, "INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?)",
                   (uuid4().hex, None, "test_delivery_failed" if fail_next else "in_app_delivery_sent", alert["id"], stamp(now),
                    json.dumps({"attempt": attempt, "adapter": "simulated_in_app", "idempotency_key": alert["idempotency_key"]})))
    return counts
