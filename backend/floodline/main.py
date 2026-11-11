from __future__ import annotations

import hashlib
from html import escape
import json
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .alerts import evidence_current
from .auth import check_login, create_session, current_user
from .config import Settings, stamp, utc, wall_now
from .data import ingest, seed
from .database import Database
from .prediction import RANK, RULE_VERSION, read_risks
from .schemas import DeliveryFault, IngestInput, LoginInput, ModerationInput, ReportCorrection, ReportInput, RouteInput, SubscriptionInput
from .service import DomainError, Service
from .uploads import save_image


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    db = Database(settings.database_url)
    service = Service(db, settings)

    @asynccontextmanager
    async def lifespan(app):
        db.migrate()
        seed(db, settings)
        service.cycle("startup")
        if settings.worker_enabled:
            service.start_worker()
        yield
        service.close()

    app = FastAPI(title="Floodline synthetic flood-platform API", version=__version__, lifespan=lifespan,
                  description="CAA prototype. Demo data and indices are not real-world forecasts.", docs_url=None, redoc_url=None)
    app.state.db, app.state.service, app.state.settings = db, service, settings
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Content-Type", "X-Floodline-Client"])
    limits = defaultdict(deque)

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        return JSONResponse(status_code=error.status, content={"detail": error.detail})

    @app.middleware("http")
    async def web_safety(request: Request, call_next):
        if request.url.path.startswith("/api") and request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            own_origin = str(request.base_url).rstrip("/")
            if request.headers.get("X-Floodline-Client") != "web" or (origin and origin not in settings.allowed_origins and origin != own_origin):
                return JSONResponse(status_code=403, content={"detail": "The request origin or client marker is invalid."})
            if request.url.path.startswith(("/api/auth", "/api/reports")):
                key = (request.client.host if request.client else "local", request.url.path.split("/")[2])
                now = time.monotonic()
                recent = limits[key]
                while recent and recent[0] <= now - 60:
                    recent.popleft()
                if len(recent) >= 30:
                    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again in a minute."}, headers={"Retry-After": "60"})
                recent.append(now)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                                                       "img-src 'self' data: blob: https://*.tile.openstreetmap.org; font-src 'self'; "
                                                       "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def optional_user(request: Request):
        return current_user(db, request.cookies.get("fl_admin")) or current_user(db, request.cookies.get("fl_session"))

    def required_user(user=Depends(optional_user)):
        if not user:
            raise HTTPException(401, "Start a resident session or sign in as a moderator.")
        return user

    def moderator(user=Depends(required_user)):
        if user["role"] != "moderator":
            raise HTTPException(403, "Moderator access is required.")
        return user

    def session_cookie(response, request, token, name="fl_session"):
        response.set_cookie(name, token, httponly=True, secure=request.url.scheme == "https", samesite="strict",
                            max_age=settings.session_hours * 3600, path="/")

    @app.get("/api/health")
    def health():
        with db.transaction() as connection:
            db.one(connection, "SELECT version FROM schema_migrations LIMIT 1")
        return {"status": "ok", "version": __version__, "mode": "synthetic", "storage": "postgresql-postgis" if db.postgres else "sqlite-local",
                "worker": settings.worker_enabled, "rule_version": RULE_VERSION}

    @app.get("/api/clock")
    def clock():
        with db.transaction() as connection:
            return {"now": stamp(service.now(connection)), "mode": "synthetic", "timezone": "Asia/Kolkata", "scenario": db.meta(connection, "scenario")}

    @app.get("/api/auth/session")
    def session(user=Depends(optional_user)):
        return {"authenticated": bool(user), "role": user["role"] if user else "visitor", "username": user["username"] if user else None}

    @app.post("/api/auth/guest")
    def guest(request: Request, response: Response):
        existing = current_user(db, request.cookies.get("fl_session"))
        if existing:
            return {"authenticated": True, "role": existing["role"], "username": existing["username"]}
        with db.transaction() as connection:
            user_id = uuid4().hex
            db.execute(connection, "INSERT INTO users VALUES (?, NULL, 'resident', NULL, NULL, ?)", (user_id, stamp(wall_now())))
            token = create_session(db, connection, user_id, settings.session_hours)
        session_cookie(response, request, token)
        return {"authenticated": True, "role": "resident", "username": None}

    @app.post("/api/auth/login")
    def login(payload: LoginInput, request: Request, response: Response):
        with db.transaction() as connection:
            user = check_login(db, connection, payload.username, payload.password)
            if not user:
                raise HTTPException(401, "The moderator username or password is incorrect.")
            token = create_session(db, connection, user["id"], settings.session_hours)
            service.audit(connection, user["id"], "moderator_signed_in", user["id"])
        session_cookie(response, request, token, "fl_admin")
        return {"authenticated": True, "role": "moderator", "username": user["username"]}

    @app.post("/api/auth/logout")
    def logout(request: Request, response: Response):
        token = request.cookies.get("fl_admin")
        if token:
            with db.transaction() as connection:
                db.execute(connection, "DELETE FROM sessions WHERE token_hash = ?", (hashlib.sha256(token.encode()).hexdigest(),))
        response.delete_cookie("fl_admin", path="/")
        return {"role": "resident", "message": "Moderator access ended. Your resident session is retained."}

    @app.get("/api/areas")
    def areas():
        with db.transaction() as connection:
            return service.area_collection(connection)

    @app.get("/api/network")
    def network():
        with db.transaction() as connection:
            return service.network(connection)

    @app.get("/api/risk")
    def risks(area_id: str | None = None):
        with db.transaction() as connection:
            items = read_risks(db, connection, service.now(connection))
            if area_id:
                items = [risk for risk in items if risk["area_id"] == area_id]
                if not items:
                    raise HTTPException(404, "Analysis area not found.")
            return {"items": items, "mode": "synthetic", "forecast_validated": False}

    @app.get("/api/sources")
    def sources():
        with db.transaction() as connection:
            now = stamp(service.now(connection))
            result = []
            for row in db.all(connection, "SELECT * FROM sources ORDER BY id"):
                source = json.loads(row["metadata_json"])
                latest = db.one(connection, "SELECT MAX(observed_at) AS observed_at, MAX(received_at) AS received_at, COUNT(*) AS n "
                                "FROM observations WHERE source_id = ? AND quality = 'good' AND received_at <= ? AND observed_at <= ?", (row["id"], now, now))
                result.append({**source, "latest_observed_at": latest["observed_at"], "latest_received_at": latest["received_at"], "available_records": latest["n"]})
            return {"items": result}

    @app.get("/api/reports")
    def reports(mine: bool = False, status: str | None = None, user=Depends(optional_user)):
        with db.transaction() as connection:
            now = service.now(connection)
            sql, params = "SELECT * FROM reports WHERE deleted_at IS NULL", []
            private = bool(user and (mine or user["role"] == "moderator"))
            if mine:
                if not user:
                    raise HTTPException(401, "Start a resident session to view your reports.")
                sql += " AND user_id = ?"
                params.append(user["id"])
            elif not private:
                sql += " AND status = 'verified' AND expires_at > ?"
                params.append(stamp(now))
            if status:
                if status not in ("pending", "verified", "rejected", "duplicate", "expired", "resolved"):
                    raise HTTPException(422, "Unknown review state.")
                sql += " AND status = ?"
                params.append(status)
            sql += " ORDER BY submitted_at DESC LIMIT 100"
            return {"items": [service.public_report(row, now, private) for row in db.all(connection, sql, params)]}

    @app.post("/api/reports", status_code=201)
    def new_report(payload: ReportInput, user=Depends(required_user)):
        return service.create_report(user, payload)

    def owned_report(connection, report_id, user):
        row = db.one(connection, "SELECT * FROM reports WHERE id = ? AND deleted_at IS NULL", (report_id,))
        if not row or row["user_id"] != user["id"]:
            raise HTTPException(404, "Report not found.")
        return row

    @app.patch("/api/reports/{report_id}")
    def correct_report(report_id: str, payload: ReportCorrection, user=Depends(required_user)):
        with db.transaction() as connection:
            row = owned_report(connection, report_id, user)
            if row["status"] != "pending":
                raise HTTPException(409, "Only a pending report can be edited. Withdraw it if its evidence must be removed.")
            db.execute(connection, "UPDATE reports SET description = ? WHERE id = ?", (payload.description, report_id))
            service.audit(connection, user["id"], "report_corrected", report_id)
            return service.public_report(db.one(connection, "SELECT * FROM reports WHERE id = ?", (report_id,)), service.now(connection), True)

    @app.delete("/api/reports/{report_id}")
    def withdraw_report(report_id: str, user=Depends(required_user)):
        with db.transaction() as connection:
            row = owned_report(connection, report_id, user)
            service.delete_image(row["image_file"])
            db.execute(connection, "UPDATE reports SET description = 'Withdrawn by reporter', image_file = NULL, image_published = 0, deleted_at = ? WHERE id = ?",
                       (stamp(service.now(connection)), report_id))
            service.audit(connection, user["id"], "report_withdrawn", report_id, {"existing_reviewed_hazards_retained_until_resolution_or_expiry": True})
            return {"id": report_id, "withdrawn": True, "message": "Your evidence has been removed. An independently reviewed restriction remains until resolution or expiry."}

    @app.post("/api/reports/{report_id}/image")
    async def attach_image(report_id: str, image: UploadFile = File(...), user=Depends(required_user)):
        content = await image.read(settings.upload_limit + 1)
        await image.close()
        return save_image(service, user, report_id, content)

    @app.get("/api/reports/{report_id}/image")
    def report_image(report_id: str, user=Depends(optional_user)):
        with db.transaction() as connection:
            row = db.one(connection, "SELECT * FROM reports WHERE id = ? AND deleted_at IS NULL", (report_id,))
            owner_or_admin = bool(row and user and (row["user_id"] == user["id"] or user["role"] == "moderator"))
            public = bool(row and row["image_published"] and row["status"] == "verified" and row["expires_at"] > stamp(service.now(connection)))
            if not row or not row["image_file"] or not (owner_or_admin or public):
                raise HTTPException(404, "Image not found.")
            folder = (settings.runtime / "images").resolve()
            path = (folder / row["image_file"]).resolve()
            if path.parent != folder or not path.is_file():
                raise HTTPException(404, "Image not found.")
            return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, no-store"})

    @app.post("/api/reports/{report_id}/moderate")
    def review_report(report_id: str, payload: ModerationInput, user=Depends(moderator)):
        return service.moderate(user, report_id, payload)

    @app.get("/api/subscriptions")
    def subscriptions(user=Depends(required_user)):
        with db.transaction() as connection:
            return {"items": db.all(connection, "SELECT id, ward_id, channel, consented_at, active FROM subscriptions WHERE user_id = ? AND active = 1", (user["id"],))}

    @app.post("/api/subscriptions", status_code=201)
    def new_subscription(payload: SubscriptionInput, user=Depends(required_user)):
        return service.subscribe(user, payload)

    @app.delete("/api/subscriptions/{subscription_id}")
    def unsubscribe(subscription_id: str, user=Depends(required_user)):
        with db.transaction() as connection:
            row = db.one(connection, "SELECT id FROM subscriptions WHERE id = ? AND user_id = ?", (subscription_id, user["id"]))
            if not row:
                raise HTTPException(404, "Subscription not found.")
            db.execute(connection, "UPDATE subscriptions SET active = 0 WHERE id = ?", (subscription_id,))
            service.audit(connection, user["id"], "subscription_withdrawn", subscription_id)
            service.cycle_in_transaction(connection, "unsubscribe")
            return {"id": subscription_id, "active": False}

    @app.get("/api/alerts")
    def alerts(user=Depends(required_user)):
        with db.transaction() as connection:
            current_time = service.now(connection)
            now = stamp(current_time)
            current_risks = read_risks(db, connection, current_time)
            rows = db.all(connection, "SELECT id, ward_id, kind, severity, state, attempts, next_attempt_at, issued_at, expires_at, sent_at, message, support, trigger_id "
                          "FROM alerts WHERE user_id = ? ORDER BY issued_at DESC LIMIT 100", (user["id"],))
            for row in rows:
                row["evidence_current"] = evidence_current(db, connection, row, current_time, current_risks)
                del row["trigger_id"]
                if row["expires_at"] <= now:
                    row["state"] = "expired"
            return {"items": rows, "adapter": "simulated_in_app", "external_messages_sent": False}

    @app.post("/api/routes")
    def route(payload: RouteInput):
        return service.route(payload)

    @app.get("/api/dashboard")
    def dashboard():
        with db.transaction() as connection:
            now = service.now(connection)
            risks = read_risks(db, connection, now)
            reports = db.all(connection, "SELECT * FROM reports WHERE status = 'verified' AND deleted_at IS NULL AND expires_at > ? ORDER BY observed_at DESC LIMIT 5", (stamp(now),))
            hazards = service.active_hazards(connection, now)
            network = service.network(connection)
            ward_names = {area["ward_id"]: json.loads(area["properties_json"])["ward_name"] for area in service.areas(connection)}
            wards = []
            for ward_id, name in ward_names.items():
                relevant = [risk for risk in risks if risk["ward_id"] == ward_id]
                strongest = max(relevant, key=lambda risk: RANK[risk["risk_level"]])
                wards.append({"id": ward_id, "name": name, "risk_level": strongest["risk_level"], "cell_ids": [risk["area_id"] for risk in relevant],
                              "unknown_cells": sum(risk["risk_level"] == "unknown" for risk in relevant)})
            return {"pilot": db.meta(connection, "fixture"), "clock": stamp(now), "mode": "synthetic", "scenario": db.meta(connection, "scenario"),
                    "areas": service.area_collection(connection), "risk": risks, "wards": wards, "network": network,
                    "reports": [service.public_report(row, now) for row in reports],
                    "hazards": [{"id": row["id"], "report_id": row["report_id"], "edge_ids": json.loads(row["edge_ids_json"]), "expires_at": row["expires_at"]} for row in hazards],
                    "summary": {"cells": len(risks), "warnings": sum(risk["risk_level"] in ("high", "elevated") for risk in risks),
                                "unknown": sum(risk["risk_level"] == "unknown" for risk in risks), "active_hazards": len(hazards)},
                    "rule_version": RULE_VERSION, "forecast_validated": False}

    @app.get("/api/observations")
    def observations(area_id: str):
        with db.transaction() as connection:
            now = stamp(service.now(connection))
            if not db.one(connection, "SELECT id FROM areas WHERE id = ?", (area_id,)):
                raise HTTPException(404, "Analysis area not found.")
            return {"items": db.all(connection, "SELECT source_id, observed_at, received_at, variable, value, unit, quality, interval_minutes "
                                   "FROM observations WHERE area_id = ? AND received_at <= ? AND observed_at <= ? ORDER BY observed_at DESC LIMIT 110", (area_id, now, now)), "mode": "synthetic"}

    @app.get("/api/admin/operations")
    def operations(user=Depends(moderator)):
        with db.transaction() as connection:
            counts = {table: db.one(connection, f"SELECT COUNT(*) AS n FROM {table}")["n"] for table in ["observations", "quarantine", "risk_runs", "reports", "alerts"]}
            jobs = db.all(connection, "SELECT * FROM jobs ORDER BY started_at DESC LIMIT 12")
            audit = db.all(connection, "SELECT action, subject_id, at, detail_json FROM audit ORDER BY at DESC LIMIT 30")
            failures = db.all(connection, "SELECT id, state, attempts, next_attempt_at, expires_at, ward_id FROM alerts WHERE state = 'failed' ORDER BY issued_at DESC LIMIT 20")
            return {"counts": counts, "jobs": [{**row, "details": json.loads(row["details_json"])} for row in jobs],
                    "audit": [{"action": row["action"], "subject_id": row["subject_id"], "at": row["at"], "details": json.loads(row["detail_json"])} for row in audit],
                    "failed_deliveries": failures, "initial_ingestion": db.meta(connection, "initial_ingestion"), "clock": stamp(service.now(connection))}

    @app.post("/api/admin/ingest")
    def ingest_records(payload: IngestInput, user=Depends(moderator)):
        with db.transaction() as connection:
            result = ingest(db, connection, payload.records)
            service.audit(connection, user["id"], "observations_ingested", "batch", result)
            result["cycle"] = service.cycle_in_transaction(connection, "ingestion")
            return result

    @app.post("/api/admin/cycle")
    def cycle(user=Depends(moderator)):
        return service.cycle("manual")

    @app.post("/api/admin/scenarios/{name}")
    def scenario(name: str, user=Depends(moderator)):
        return service.scenario(user, name)

    @app.post("/api/admin/delivery-fault")
    def delivery_fault(payload: DeliveryFault, user=Depends(moderator)):
        with db.transaction() as connection:
            db.set_meta(connection, "fail_next_deliveries", payload.fail_next)
            service.audit(connection, user["id"], "simulated_delivery_failure_configured", "adapter", {"fail_next": payload.fail_next})
        return {"fail_next": payload.fail_next, "adapter": "simulated_in_app"}

    @app.get("/api/evaluation")
    def evaluation():
        path = settings.runtime / "evaluation.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
            "mode": "synthetic", "historical_accuracy_established": False,
            "reason": "No real historical event labels are present. The susceptibility/threshold fallback is active.",
            "rule_version": RULE_VERSION, "synthetic_training_promoted": False}

    @app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
    def api_reference():
        rows = "".join(f"<tr><td>{escape(method.upper())}</td><td><code>{escape(path)}</code></td>"
                       f"<td>{escape(operation.get('summary', ''))}</td></tr>"
                       for path, methods in app.openapi()["paths"].items() for method, operation in methods.items()
                       if method in {"get", "post", "patch", "delete"})
        return ("<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<title>Floodline API reference</title><style>body{font:16px/1.6 sans-serif;color:#21343d;background:#edf3f5;max-width:1100px;margin:32px auto;padding:0 20px}"
                "a{color:#087f82}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;padding:12px;border-bottom:1px solid #e2e9eb}"
                "code{overflow-wrap:anywhere}h1{font-size:28px} .table-wrap{overflow:auto}</style><body><main><h1>Floodline API reference</h1>"
                "<p>Offline reference for the synthetic CAA prototype. <a href='/'>Open the dashboard</a> · <a href='/openapi.json'>OpenAPI schemas and examples</a></p>"
                "<p>Write requests require <code>X-Floodline-Client: web</code>. Resident sessions own their reports and subscriptions; moderation requires sign in. "
                "All timestamps use ISO 8601 with a timezone. No live forecasts or real notifications are enabled.</p>"
                "<div class='table-wrap'><table><thead><tr><th>Method</th><th>Path</th><th>Action</th></tr></thead><tbody>" + rows + "</tbody></table></div></main></body></html>")

    if (settings.frontend / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=settings.frontend / "assets"), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API endpoint not found.")
        folder = settings.frontend.resolve()
        requested = (folder / path).resolve()
        if requested.is_relative_to(folder) and requested.is_file():
            return FileResponse(requested)
        if (folder / "index.html").is_file():
            return FileResponse(folder / "index.html")
        return JSONResponse(status_code=503, content={"detail": "Build the frontend with npm run build in frontend/, then restart the server."})

    return app
