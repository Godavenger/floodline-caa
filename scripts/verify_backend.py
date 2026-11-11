"""Run backend acceptance and write reproducible evidence without demo data."""
from __future__ import annotations

import io
import json
import platform
import sys
import time
import unittest
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    started = datetime.now(timezone.utc).isoformat()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "backend" / "tests"))
    stream = io.StringIO()
    began = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    folder = ROOT / "outputs" / "evidence"
    folder.mkdir(parents=True, exist_ok=True)
    log = stream.getvalue().replace(str(ROOT), "[project]")
    (folder / "backend-tests.txt").write_text(log, encoding="utf-8")
    evidence = {"status": "passed" if result.wasSuccessful() else "failed", "mode": "synthetic",
                "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
                "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                "skipped": len(result.skipped), "elapsed_seconds": round(time.perf_counter() - began, 3),
                "python": platform.python_version(), "platform": platform.platform(),
                "packages": {name: version(name) for name in ["fastapi", "starlette", "pydantic", "Pillow", "numpy", "scikit-learn", "shapely", "pyproj", "networkx"]}}
    (folder / "backend-acceptance.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(log)
    print(json.dumps(evidence, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
