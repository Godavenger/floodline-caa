"""Package the reviewed synthetic demo and verify it from an isolated extraction.

Run with the project interpreter after the frontend and acceptance checks pass:
    python scripts/package_release.py --verify
Installed dependencies, environment files, sessions and private uploads are never
included. Verification reuses the interpreter's installed dependencies; it does
not claim to test a fresh online dependency installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.floodline import __version__

ROOT = Path(__file__).resolve().parents[1]
VERSION = __version__
PREFIX = f"Floodline-{VERSION}"
RELEASES = ROOT / "outputs" / "releases"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_file(path: Path) -> Path:
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Release input leaves the project: {path.name}")
    if not path.is_file():
        raise FileNotFoundError(f"Missing release input: {path.relative_to(ROOT)}")
    return path


def collect_files() -> list[Path]:
    files = set()
    for name in [
        "README.md", "PRODUCT.md", "DESIGN.md", "THIRD_PARTY.md", ".env.example",
        ".gitignore", ".dockerignore", "start.bat", "start.cmd", "start.ps1", "Dockerfile",
        "compose.yaml", "project description.docx", ".impeccable/design.json",
        ".taste-skill/direction.json", "frontend/index.html", "frontend/package.json",
        "frontend/package-lock.json", "frontend/tsconfig.json", "frontend/vite.config.ts",
        "outputs/Smart_City_Flood_Prediction_CAA_Pipeline.md",
        "outputs/Smart_City_Flood_Prediction_CAA_Pipeline.pdf",
        "outputs/Floodline_Project_Report.pdf",
    ]:
        files.add(project_file(ROOT / name))
    source_groups = {
        ".github": {".yml", ".yaml"},
        "backend": {".py", ".sql", ".txt"},
        "frontend/src": {".tsx", ".ts", ".css"},
        "frontend/public": {".svg", ".png", ".ico", ".js"},
        "frontend/dist": {".html", ".js", ".css", ".svg", ".png", ".woff", ".woff2"},
        "scripts": {".py", ".mjs"},
        "data": {".json", ".csv"},
        "docs": {".md"},
        "outputs/evidence": {".json", ".csv", ".geojson", ".txt", ".md", ".png", ".pdf", ".joblib"},
        ".impeccable/review": {".md", ".json"},
    }
    for directory, extensions in source_groups.items():
        for path in (ROOT / directory).rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions and not any(
                part in {"__pycache__", "node_modules"} for part in path.parts
            ):
                files.add(project_file(path))
    for path in (ROOT / "third_party").rglob("*"):
        if path.is_file():
            files.add(project_file(path))
    browser = json.loads((ROOT / ".verification/browser-acceptance.json").read_text(encoding="utf-8"))
    for shot in browser["screenshots"]:
        files.add(project_file(ROOT / shot["path"]))
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def preflight() -> None:
    required = ["docs/ACCEPTANCE.md", "docs/PROJECT_STATUS.md", "frontend/dist/index.html", "start.bat",
                ".impeccable/review/finish-verdict.md"]
    for name in required:
        project_file(ROOT / name)
    verdict = (ROOT / ".impeccable/review/finish-verdict.md").read_text(encoding="utf-8")
    if "disposition: ship" not in verdict:
        raise ValueError("The final recorded fix verdict must be ship before packaging.")
    browser = json.loads((ROOT / ".verification/browser-acceptance.json").read_text(encoding="utf-8"))
    backend = json.loads((ROOT / "outputs/evidence/backend-acceptance.json").read_text(encoding="utf-8"))
    evaluation = json.loads((ROOT / "outputs/evidence/evaluation.json").read_text(encoding="utf-8"))
    if browser["status"] != "passed" or backend["status"] != "passed":
        raise ValueError("Backend and browser acceptance must pass before packaging.")
    launcher = json.loads((ROOT / "outputs/evidence/launcher-acceptance.json").read_text(encoding="utf-8"))
    if launcher["status"] != "passed":
        raise ValueError("Windows launcher acceptance must pass before packaging.")
    for name, checksum in launcher["source_sha256"].items():
        if digest(project_file(ROOT / name).read_bytes()) != checksum:
            raise ValueError("A Windows launcher input changed after acceptance; verify it again.")
    if browser["frontend_sha256"] != digest((ROOT / "frontend/dist/index.html").read_bytes()):
        raise ValueError("The built interface changed after browser acceptance; verify it again.")
    if browser.get("theme_bootstrap_sha256") != digest((ROOT / "frontend/dist/assets/theme.js").read_bytes()):
        raise ValueError("The early appearance script changed after browser acceptance; verify it again.")
    if evaluation["mode"] != "synthetic" or evaluation["candidate_promoted"]:
        raise ValueError("This release must retain its synthetic, unpromoted evaluation gate.")
    for shot in browser["screenshots"]:
        path = project_file(ROOT / shot["path"])
        if digest(path.read_bytes()) != shot["sha256"]:
            raise ValueError(f"A reviewed screenshot changed: {shot['name']}")
    exported = json.loads((ROOT / "outputs/evidence/browser-acceptance.json").read_text(encoding="utf-8"))
    if exported != browser:
        raise ValueError("Export the latest browser acceptance before packaging.")


def write_archive(files: list[Path], destination: Path) -> dict:
    contents = [(path.relative_to(ROOT).as_posix(), path.read_bytes()) for path in files]
    entries = [{"path": name, "bytes": len(data), "sha256": digest(data)} for name, data in contents]
    manifest = {
        "release": VERSION, "mode": "synthetic", "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_promoted": False, "historical_accuracy_established": False,
        "source_fingerprint": digest("\n".join(row["path"] + " " + row["sha256"] for row in entries).encode()),
        "files": entries,
        "excluded": ["installed dependencies", "environment files", "runtime databases", "sessions", "private uploads", "browser profiles"],
    }
    contents.append(("PACKAGE_MANIFEST.json", (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")))
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in contents:
            entry = ZipInfo(PREFIX + "/" + name, date_time=(2026, 11, 11, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compresslevel=9)
    return manifest


def verify_archive(destination: Path) -> dict:
    verification_root = (ROOT / ".verification/release").resolve()
    verification_root.mkdir(parents=True, exist_ok=True)
    extraction = Path(tempfile.mkdtemp(prefix="demo-", dir=verification_root)).resolve()
    if not extraction.is_relative_to(verification_root):
        raise ValueError("The release verification directory leaves its intended workspace.")
    with ZipFile(destination) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError("Archive entries are duplicated or corrupt.")
        for name in names:
            parts = PurePosixPath(name).parts
            if not parts or parts[0] != PREFIX or ".." in parts or PurePosixPath(name).is_absolute():
                raise ValueError("An archive path leaves the release folder.")
            if any(part in {".runtime", ".venv", "node_modules", ".env", "__pycache__"} for part in parts):
                raise ValueError("A private or installed runtime file entered the release.")
        manifest = json.loads(archive.read(PREFIX + "/PACKAGE_MANIFEST.json"))
        if set(names) != {PREFIX + "/" + row["path"] for row in manifest["files"]} | {PREFIX + "/PACKAGE_MANIFEST.json"}:
            raise ValueError("The manifest does not cover every archive entry.")
        for row in manifest["files"]:
            data = archive.read(PREFIX + "/" + row["path"])
            if len(data) != row["bytes"] or digest(data) != row["sha256"]:
                raise ValueError("A release file does not match its manifest.")
        archive.extractall(extraction)
    released_root = extraction / PREFIX
    environment = {**os.environ, "FLOODLINE_RUNTIME": str(released_root / ".runtime"), "DATABASE_URL": "",
                   "APP_MODE": "synthetic", "ADMIN_USERNAME": "moderator", "ADMIN_PASSWORD": "floodline-demo"}
    environment.pop("PYTHONPATH", None)
    launcher_checked = False
    if os.name == "nt":
        launcher_environment = {**environment, "PYTHONPATH": os.pathsep.join(
            path for path in sys.path if Path(path).name.lower() == "site-packages"
        )}
        launcher_command = f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c ""{released_root / "start.bat"}" -PrepareOnly -NoBrowser"'
        launched = subprocess.run(launcher_command, cwd=extraction, env=launcher_environment,
                                  input="", capture_output=True, text=True, timeout=60,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        if launched.returncode != 0 or "Using the bundled interface" not in launched.stdout or "Preparation complete" not in launched.stdout:
            raise RuntimeError("Released Windows launcher failed:\n" + launched.stdout + launched.stderr)
        launcher_checked = True
    smoke = r'''
import json, re
from pathlib import Path
from fastapi.testclient import TestClient
from backend.floodline.config import ROOT, Settings
from backend.floodline.main import create_app
assert ROOT == Path.cwd().resolve(), "Smoke test must import the extracted source."
settings = Settings(worker_enabled=False)
with TestClient(create_app(settings)) as client:
    health = client.get("/api/health")
    assert health.status_code == 200 and health.json()["storage"] == "sqlite-local"
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["mode"] == "synthetic" and dashboard["forecast_validated"] is False
    assert dashboard["summary"]["cells"] == 9 and len(dashboard["wards"]) == 3
    assert dashboard["summary"]["warnings"] == 3 and dashboard["summary"]["unknown"] == 1
    html = client.get("/")
    assert html.status_code == 200
    asset = re.search(r'src="(/assets/[^\"]+)"', html.text)
    assert asset and client.get(asset.group(1)).status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
print(json.dumps({"status":"passed", "checks":["all archive checksums", "private runtime exclusions", "extracted-source imports", "fresh SQLite migrations and fixture", "synthetic map contracts", "bundled frontend and JavaScript", "offline API reference"], "summary":dashboard["summary"]}))
'''
    result = subprocess.run([sys.executable, "-c", smoke], cwd=released_root, env=environment,
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError("Released demo smoke test failed:\n" + result.stdout + result.stderr)
    evidence = json.loads(result.stdout.strip().splitlines()[-1])
    if launcher_checked:
        evidence["checks"].extend(["Windows batch launcher from unrelated working directory", "bundled interface without rebuilding"])
    evidence.update({"at": datetime.now(timezone.utc).isoformat(), "release": VERSION,
                     "archive": destination.relative_to(ROOT).as_posix(), "archive_sha256": digest(destination.read_bytes()),
                     "files": len(manifest["files"]), "extraction": extraction.relative_to(ROOT).as_posix(),
                     "scope": "Isolated archive extraction and Windows batch preparation using existing Python dependencies; no fresh online install or PostgreSQL validation."})
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Run manifest and extracted-demo acceptance.")
    arguments = parser.parse_args()
    preflight()
    RELEASES.mkdir(parents=True, exist_ok=True)
    destination = RELEASES / f"Floodline_CAA_Demo_v{VERSION}.zip"
    manifest = write_archive(collect_files(), destination)
    checksum = digest(destination.read_bytes())
    destination.with_suffix(".zip.sha256").write_text(checksum + "  " + destination.name + "\n", encoding="utf-8")
    evidence = verify_archive(destination) if arguments.verify else None
    if evidence:
        (RELEASES / "release-verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "packaged", "release": VERSION, "mode": "synthetic", "archive": str(destination),
                      "sha256": checksum, "files": len(manifest["files"]), "verification": evidence}, indent=2))


if __name__ == "__main__":
    main()
