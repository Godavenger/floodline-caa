"""Capture an illustrated user-guide walkthrough using an isolated demo runtime.

Run from the project root with a Python interpreter that has Playwright and Pillow.
The real application's runtime, reports and browser cookies are not used.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright, expect


ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "docs" / "user-guide" / "images"
QA = ROOT / "outputs" / "_qa" / "user-guide"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    verification = ROOT / ".verification"
    verification.mkdir(exist_ok=True)
    runtime = Path(tempfile.mkdtemp(prefix="user-guide-", dir=verification))
    env = os.environ.copy()
    env.update(FLOODLINE_RUNTIME=str(runtime), ADMIN_USERNAME="moderator",
               ADMIN_PASSWORD="floodline-demo", APP_MODE="synthetic")
    env.pop("DATABASE_URL", None)
    hidden = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    evaluation = subprocess.run([str(PYTHON), "-m", "backend.floodline", "evaluate"],
                                cwd=ROOT, env=env, capture_output=True, text=True,
                                check=True, creationflags=hidden)
    with socket.socket() as selected_socket:
        selected_socket.bind(("127.0.0.1", 0))
        port = selected_socket.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    checks, captures, errors = [], [], []
    def checked(name, detail=None):
        checks.append({"name": name, "passed": True, "detail": detail})
        print(name, flush=True)
    with (QA / "server.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([str(PYTHON), "-m", "backend.floodline", "serve", "--port", str(port)],
                                   cwd=ROOT, env=env, stdout=log, stderr=log,
                                   creationflags=hidden)
        try:
            deadline = time.monotonic() + 60
            while True:
                try:
                    with urlopen(base + "/api/health", timeout=1) as response:
                        health = json.load(response)
                    break
                except Exception:
                    if process.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError("The isolated guide server did not become ready.")
                    time.sleep(0.25)
            assert health["mode"] == "synthetic" and health["storage"] == "sqlite-local"
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 960},
                                              device_scale_factor=1, timezone_id="Asia/Kolkata",
                                              color_scheme="light")
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                def shot(name, target=None, full_page=False):
                    page.evaluate("document.activeElement?.blur()")
                    page.evaluate("document.fonts.ready")
                    page.wait_for_timeout(180)
                    path = ASSETS / f"{name}.png"
                    if target is not None:
                        target.screenshot(path=str(path))
                    else:
                        page.screenshot(path=str(path), full_page=full_page)
                    captures.append({"name": name, "file": str(path.relative_to(ROOT)),
                                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                     "size": Image.open(path).size})
                def navigate(screen):
                    page.locator(f".sidebar a[href='#{screen}']").click()
                    page.wait_for_timeout(160)
                def api(path):
                    return page.evaluate("async p => { const r = await fetch('/api' + p); if (!r.ok) throw Error('Read failed: '+p); return r.json(); }", path)

                page.goto(base, wait_until="networkidle")
                expect(page.get_by_role("heading", name="Community flood map")).to_be_visible()
                expect(page.locator(".leaflet-container")).to_be_visible()
                dashboard = api("/dashboard")
                assert dashboard["summary"] == {"cells": 9, "warnings": 3, "unknown": 1, "active_hazards": 1}
                checked("Fresh map and synthetic starting state", dashboard["summary"])
                shot("01-flood-map")
                page.locator("#selected-area").select_option("C2")
                page.get_by_text("Rule and source details", exact=True).click()
                expect(page.locator(".reason-details[open]")).to_be_visible()
                shot("02-area-evidence", page.locator(".evidence-panel"))
                checked("Area selection and rule/source details")

                page.get_by_label("Appearance", exact=True).select_option("dark")
                expect(page.locator("html")).to_have_attribute("data-theme", "dark")
                shot("03-dark-map")
                page.get_by_label("Appearance", exact=True).select_option("light")
                page.set_viewport_size({"width": 390, "height": 844})
                page.get_by_role("button", name="Open navigation").click()
                expect(page.get_by_role("dialog", name="Navigation")).to_be_visible()
                shot("04-mobile-navigation")
                page.get_by_role("button", name="Close navigation").click()
                shot("05-mobile-map")
                checked("Appearance selector and mobile navigation")
                page.set_viewport_size({"width": 1440, "height": 960})

                navigate("routes")
                page.locator("#route-start").select_option("n0-1")
                page.locator("#route-end").select_option("n4-1")
                page.get_by_role("button", name="Find route", exact=True).click()
                expect(page.get_by_role("heading", name="Route found", exact=True)).to_be_visible()
                baseline = page.evaluate("async () => {const d=await (await fetch('/api/network')).json();const s=d.nodes.find(n=>n.id==='n0-1');const e=d.nodes.find(n=>n.id==='n4-1');return (await fetch('/api/routes',{method:'POST',headers:{'Content-Type':'application/json','X-Floodline-Client':'web'},body:JSON.stringify({start:{longitude:s.longitude,latitude:s.latitude},end:{longitude:e.longitude,latitude:e.latitude}})})).json()}")
                shot("06-route-found")
                checked("Library to Station route", {"status": baseline["status"], "distance_m": baseline["distance_m"]})
                segment = next(road for road in dashboard["network"]["features"]
                               if "road-n4-1-n4-2" == road["properties"]["segment_id"])
                assert any(edge in baseline["edge_ids"] for edge in segment["properties"]["edge_ids"])

                navigate("reports")
                expect(page.get_by_role("heading", name="Submit an observation")).to_be_visible()
                page.locator("#report-landmark").select_option("n4-1")
                description = "DEMO EXERCISE: Water covers the north approach to Station; passage is affected."
                page.locator("#report-description").fill(description)
                page.locator("#report-severity").select_option("slow_passage")
                shot("07-report-form")
                page.get_by_role("button", name="Submit for review").click()
                expect(page.get_by_text("Report saved as pending.", exact=False)).to_be_visible()
                expect(page.locator(".report-list-row .report-pending")).to_be_visible()
                assert api("/dashboard")["summary"]["active_hazards"] == 1
                shot("08-pending-report")
                checked("Resident report is pending and creates no road restriction")
                page.get_by_role("button", name="Correct", exact=True).click()
                page.locator(".inline-edit textarea").fill(description + " This is invented training evidence.")
                page.get_by_role("button", name="Save correction").click()
                expect(page.get_by_text("Your pending report has been corrected.", exact=True)).to_be_visible()
                checked("Pending report description correction")

                navigate("alerts")
                page.locator("#alert-ward").select_option("C")
                page.get_by_role("checkbox", name="I agree to receive in-app alerts for this ward in this resident session.").check()
                page.get_by_role("button", name="Subscribe", exact=True).click()
                expect(page.locator(".subscription-row")).to_have_count(1)
                expect(page.locator(".alert-row").first).to_be_visible()
                shot("09-alerts")
                checked("Explicit ward consent and simulated in-app alert history")

                navigate("data")
                page.get_by_text("Demo evaluation and promotion gate", exact=True).click()
                expect(page.get_by_text("Not promoted", exact=True)).to_be_visible()
                shot("10-data-model")
                checked("Data sources and unpromoted model evaluation")

                navigate("review")
                expect(page.get_by_role("heading", name="Sign in to review evidence")).to_be_visible()
                page.locator(".moderator-gate").get_by_role("button", name="Moderator sign in").click()
                shot("11-moderator-sign-in", page.locator(".login-dialog"))
                page.locator("#login-password").fill("floodline-demo")
                page.locator(".login-dialog").get_by_role("button", name="Sign in", exact=True).click()
                expect(page.get_by_role("heading", name="Evidence review", exact=True)).to_be_visible()
                page.get_by_role("button", name=description[:40], exact=False).click()
                page.locator("#review-reason").fill("Training review: the invented Station pin matches this synthetic road segment.")
                page.get_by_role("checkbox", name="Create a 2-hour road restriction from this reviewed observation.").check()
                page.locator("#review-road").select_option(segment["properties"]["id"])
                shot("12-evidence-review")
                page.get_by_role("button", name="Verify report", exact=True).click()
                expect(page.get_by_text("Review recorded. Map evidence and road restrictions are updated.", exact=True)).to_be_visible()
                assert api("/dashboard")["summary"]["active_hazards"] == 2
                checked("Authenticated report verification and matched road exclusion")
                shot("13-replay-health", page.locator(".demo-controls"))

                navigate("routes")
                page.get_by_role("button", name="Find route", exact=True).click()
                expect(page.get_by_role("heading", name="Route found", exact=True)).to_be_visible()
                comparison = page.evaluate("async () => {const d=await (await fetch('/api/network')).json();const s=d.nodes.find(n=>n.id==='n0-1');const e=d.nodes.find(n=>n.id==='n4-1');return (await fetch('/api/routes',{method:'POST',headers:{'Content-Type':'application/json','X-Floodline-Client':'web'},body:JSON.stringify({start:{longitude:s.longitude,latitude:s.latitude},end:{longitude:e.longitude,latitude:e.latitude}})})).json()}")
                assert baseline["edge_ids"] != comparison["edge_ids"]
                assert not set(comparison["edge_ids"]) & set(segment["properties"]["edge_ids"])
                shot("14-route-after-review")
                checked("Recalculated route excludes the new restriction", {"distance_before_m": baseline["distance_m"], "distance_after_m": comparison["distance_m"]})
                page.locator("#route-end").select_option("island")
                page.get_by_role("button", name="Find route", exact=True).click()
                expect(page.get_by_role("heading", name="Route unavailable", exact=True)).to_be_visible()
                shot("15-route-unavailable", page.locator(".route-controls"))
                checked("Disconnected destination shows Route unavailable")

                navigate("review")
                page.get_by_role("button", name="Feed outage", exact=True).click()
                expect(page.get_by_text("Synthetic scenario applied.", exact=False)).to_be_visible()
                outage = api("/dashboard")
                assert outage["summary"]["unknown"] == 9
                navigate("map")
                expect(page.get_by_text("All 9 cells have unknown conditions", exact=False)).to_be_visible()
                shot("16-feed-outage")
                checked("Outage shows all nine cells unknown")
                navigate("review")
                page.get_by_role("button", name="Recover feed", exact=True).click()
                expect(page.get_by_text("Synthetic scenario applied.", exact=False)).to_be_visible()
                assert api("/dashboard")["summary"]["unknown"] == 0
                checked("Explicit synthetic feed recovery")
                page.get_by_role("button", name="Return to resident", exact=True).click()
                expect(page.get_by_text("Moderator access ended.", exact=False)).to_be_visible()
                navigate("reports")
                page.get_by_role("button", name="Close form").click()
                expect(page.get_by_text("This is invented training evidence.", exact=False)).to_be_visible()
                checked("Moderator sign-out preserves resident report ownership")
                assert not errors, errors
                context.close()
                browser.close()
            result = {"status": "passed", "captured_at": datetime.now(timezone.utc).isoformat(),
                      "version": health["version"], "mode": "synthetic", "checks": checks,
                      "captures": captures, "javascript_errors": errors,
                      "scope": "Illustrated guide walkthrough in a new SQLite runtime using headless Edge. Separate from the recorded full browser acceptance and from human usability testing.",
                      "evaluation_summary": json.loads(evaluation.stdout)}
            (QA / "walkthrough.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"Completed {len(checks)} guide checks and {len(captures)} screenshots.", flush=True)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
