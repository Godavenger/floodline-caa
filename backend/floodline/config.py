from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc


def utc(value: str | datetime) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if result.tzinfo is None:
        raise ValueError("A timezone is required; send an ISO 8601 timestamp with an offset.")
    return result.astimezone(UTC)


def stamp(value: datetime) -> str:
    return utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def wall_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Settings:
    runtime: Path = field(default_factory=lambda: Path(os.getenv("FLOODLINE_RUNTIME", str(ROOT / ".runtime"))))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    admin_username: str = field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "moderator"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "floodline-demo"))
    demo_mode: bool = True
    worker_interval: float = 30.0
    worker_enabled: bool = True
    session_hours: int = 12
    upload_limit: int = 5 * 1024 * 1024
    frontend: Path = field(default_factory=lambda: ROOT / "frontend" / "dist")
    fixture: Path = field(default_factory=lambda: ROOT / "data" / "fixtures" / "pilot.json")
    observations: Path = field(default_factory=lambda: ROOT / "data" / "raw" / "demo_observations.json")
    allowed_origins: tuple[str, ...] = ("http://127.0.0.1:8000", "http://localhost:8000",
                                       "http://127.0.0.1:5173", "http://localhost:5173")

    def __post_init__(self):
        self.runtime = Path(self.runtime).resolve()
        self.runtime.mkdir(parents=True, exist_ok=True)
        (self.runtime / "images").mkdir(exist_ok=True)
        if not self.database_url:
            self.database_url = "sqlite:///" + str(self.runtime / "floodline.db")
        if os.getenv("APP_MODE", "synthetic") != "synthetic":
            raise ValueError("Only synthetic mode is implemented. A live mode needs audited pilot data.")
