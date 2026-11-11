"""Exercise the Windows launchers with isolated demo folders and databases.

Successful runs reuse installed Python dependencies and block Node/npm. The
first-install failure check uses a fresh venv with pip's network access disabled.
It does not claim to verify a fresh online dependency installation.
"""
from __future__ import annotations

import hashlib
import ctypes
from ctypes import wintypes
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION = ROOT / ".verification" / "launcher"
HIDDEN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class WindowsProcessJob:
    """Keep each test launcher and its children in an owned Windows job."""
    def __init__(self):
        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("minimum_working_set", ctypes.c_size_t),
                        ("maximum_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io", IoCounters),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.kernel.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.get_last_error()
            self.close()
            raise ctypes.WinError(error)

    def assign(self, process):
        if not self.kernel.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class LauncherAcceptance(unittest.TestCase):
    def setUp(self):
        VERIFICATION.mkdir(parents=True, exist_ok=True)
        self.project = Path(tempfile.mkdtemp(prefix="demo with spaces-", dir=VERIFICATION)).resolve()
        if not self.project.is_relative_to(VERIFICATION.resolve()):
            raise ValueError("Launcher fixture leaves its verification folder.")
        for name in ("start.bat", "start.cmd", "start.ps1"):
            shutil.copyfile(ROOT / name, self.project / name)
        for name in ("backend", "data", "frontend/dist"):
            shutil.copytree(ROOT / name, self.project / name, ignore=shutil.ignore_patterns("__pycache__"))
        self.other_folder = self.project / "unrelated working folder"
        self.other_folder.mkdir()
        self.tools = self.project / "blocked node tools"
        self.tools.mkdir()
        (self.tools / "npm.cmd").write_text("@echo Node build must not run in the bundled demo.\n@exit /b 97\n", encoding="ascii")
        packages = [item for item in sys.path if Path(item).name.lower() == "site-packages"]
        task_path = [item for item in os.environ.get("PATH", "").split(os.pathsep) if "nodejs" not in item.lower()]
        self.environment = {
            **os.environ, "PATH": os.pathsep.join([str(self.tools), *task_path]),
            "PYTHONPATH": os.pathsep.join(packages), "DATABASE_URL": "",
            "FLOODLINE_RUNTIME": str(self.project / ".runtime"), "APP_MODE": "synthetic",
            "ADMIN_USERNAME": "moderator", "ADMIN_PASSWORD": "floodline-demo",
        }
        self.processes = []
        self.jobs = []
        self.output_files = []

    def tearDown(self):
        for job in self.jobs:
            job.close()
        for process in self.processes:
            process.wait(timeout=10)
            if process.stdin:
                process.stdin.close()
        for stream in self.output_files:
            stream.close()

    def launch(self, *arguments, filename="start.bat", environment=None):
        # Arguments are controlled switches/integers. Windows filenames cannot
        # contain quotes, so cmd's outer quote pair safely retains folder spaces.
        launcher = self.project / filename
        command = f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c ""{launcher}" -NoBrowser {" ".join(arguments)}"'
        log = self.project / f"process-{len(self.processes)}.log"
        stream = log.open("wb")
        self.output_files.append(stream)
        job = WindowsProcessJob()
        self.jobs.append(job)
        process = subprocess.Popen(command, cwd=self.other_folder, env=environment or self.environment,
                                   stdin=subprocess.PIPE, stdout=stream, stderr=subprocess.STDOUT,
                                   creationflags=HIDDEN)
        self.processes.append(process)
        job.assign(process)
        return process, log

    def finish(self, process, log):
        code = process.wait(timeout=45)
        return code, log.read_text(encoding="utf-8", errors="replace")

    def await_dashboard(self, process, log, port=None):
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            output = log.read_text(encoding="utf-8", errors="replace")
            self.assertIsNone(process.poll(), output)
            if port is None:
                match = re.search(r"Floodline synthetic pilot: http://127\.0\.0\.1:(\d+)", output)
                candidate = int(match[1]) if match else None
            else:
                candidate = port
            if candidate:
                try:
                    with urlopen(f"http://127.0.0.1:{candidate}/api/health", timeout=0.5) as response:
                        health = json.load(response)
                    if health["status"] == "ok" and health["mode"] == "synthetic":
                        return candidate, output
                except (OSError, ValueError):
                    pass
            time.sleep(0.2)
        self.fail("The launcher did not serve a healthy dashboard:\n" + log.read_text(encoding="utf-8", errors="replace"))

    @staticmethod
    def occupied_port(port=0):
        listener = socket.socket()
        listener.bind(("127.0.0.1", port))
        listener.listen()
        return listener

    def test_bat_serves_bundled_dashboard_without_node(self):
        with self.occupied_port() as reservation:
            port = reservation.getsockname()[1]
        process, log = self.launch("-Port", str(port))
        port, output = self.await_dashboard(process, log, port)
        self.assertIn("Using the bundled interface", output)
        with urlopen(f"http://127.0.0.1:{port}/api/dashboard") as response:
            dashboard = json.load(response)
        self.assertEqual(dashboard["summary"], {"cells": 9, "warnings": 3, "unknown": 1, "active_hazards": 1})
        with urlopen(f"http://127.0.0.1:{port}/") as response:
            html = response.read().decode()
        asset = re.search(r'src="(/assets/[^\"]+)"', html)
        self.assertIsNotNone(asset)
        with urlopen(f"http://127.0.0.1:{port}{asset[1]}") as response:
            self.assertEqual(response.status, 200)

    def test_cmd_prepares_backs_up_and_preserves_existing_data(self):
        process, log = self.launch("-PrepareOnly", filename="start.cmd")
        code, output = self.finish(process, log)
        self.assertEqual(code, 0, output)
        database = self.project / ".runtime" / "floodline.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE launcher_sentinel (value TEXT)")
            connection.execute("INSERT INTO launcher_sentinel VALUES ('retained')")
        process, log = self.launch("-PrepareOnly", filename="start.cmd")
        code, output = self.finish(process, log)
        self.assertEqual(code, 0, output)
        self.assertIn("Backup written to", output)
        with sqlite3.connect(database) as connection:
            self.assertEqual(connection.execute("SELECT value FROM launcher_sentinel").fetchone()[0], "retained")
        backups = list((self.project / ".runtime" / "backups").glob("before-launch-*.db"))
        self.assertTrue(backups)
        with sqlite3.connect(backups[0]) as connection:
            self.assertEqual(connection.execute("SELECT value FROM launcher_sentinel").fetchone()[0], "retained")

    def test_default_port_skips_occupied_8000(self):
        try:
            listener = self.occupied_port(8000)
        except OSError:
            listener = None  # An existing server already occupies the port.
        try:
            process, log = self.launch()
            port, output = self.await_dashboard(process, log)
            self.assertGreater(port, 8000, output)
            self.assertIn("Port 8000 is in use; using port", output)
        finally:
            if listener:
                listener.close()

    def test_requested_occupied_port_reports_failure_without_closing_silently(self):
        with self.occupied_port() as listener:
            process, log = self.launch("-Port", str(listener.getsockname()[1]))
            code, output = self.finish(process, log)
        self.assertEqual(code, 1, output)
        self.assertIn("already in use", output)
        self.assertIn("Startup log:", output)
        self.assertNotIn("Database migrations complete", output)
        transcript = next((self.project / ".runtime" / "launcher-logs").glob("*.log"))
        self.assertIn("already in use", transcript.read_text(encoding="utf-8-sig", errors="replace"))

    def test_missing_bundled_interface_reports_rebuild_instructions(self):
        (self.project / "frontend" / "dist" / "index.html").unlink()
        process, log = self.launch("-SkipBuild", "-PrepareOnly")
        code, output = self.finish(process, log)
        self.assertEqual(code, 1, output)
        self.assertIn("bundled interface is missing", output)
        self.assertIn("-Rebuild", output)

    def test_invalid_settings_are_reported_without_execution(self):
        (self.project / ".env").write_text("UNSUPPORTED_SETTING=invalid\n", encoding="utf-8")
        process, log = self.launch("-PrepareOnly")
        code, output = self.finish(process, log)
        self.assertEqual(code, 1, output)
        self.assertIn("unsupported setting", output)
        self.assertIn("Startup log:", output)

    def test_first_setup_failure_has_visible_retry_instructions(self):
        environment = dict(self.environment)
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment.update({"PIP_NO_INDEX": "1", "PIP_CONFIG_FILE": os.devnull, "PIP_FIND_LINKS": ""})
        result = subprocess.run([sys.executable, "-m", "venv", str(self.project / ".venv")],
                                env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                creationflags=HIDDEN, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout.decode(errors="replace"))
        process, log = self.launch("-PrepareOnly", environment=environment)
        code, output = self.finish(process, log)
        self.assertEqual(code, 1, output)
        self.assertIn("Installing pinned Python dependencies", output)
        self.assertIn("Python dependency installation failed", output)
        self.assertIn("start.bat -Install", output)
        self.assertIn("Startup log:", output)


def main():
    if os.name != "nt":
        raise SystemExit("This acceptance script exercises Windows batch and PowerShell launchers.")
    began = time.monotonic()
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LauncherAcceptance)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    evidence = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "at": datetime.now(timezone.utc).isoformat(), "tests": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "elapsed_seconds": round(time.monotonic() - began, 3),
        "scope": "Real batch/PowerShell startup and HTTP requests in isolated folders with spaces, installed Python dependency reuse, Node blocked, and offline first-install failure. No fresh online installation or interactive console approval is claimed.",
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                          for name in ("start.bat", "start.cmd", "start.ps1", "scripts/verify_launcher.py")},
    }
    output = ROOT / "outputs" / "evidence"
    output.mkdir(parents=True, exist_ok=True)
    (output / "launcher-tests.txt").write_text(stream.getvalue(), encoding="utf-8")
    (output / "launcher-acceptance.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(stream.getvalue())
    print(json.dumps(evidence, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
