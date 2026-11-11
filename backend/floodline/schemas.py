from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import utc


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Point(Contract):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)


class ReportInput(Point):
    description: str = Field(min_length=10, max_length=800)
    severity: Literal["water_on_road", "slow_passage", "impassable", "unknown"] = "unknown"
    observed_at: datetime

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value):
        return utc(value)


class ReportCorrection(Contract):
    description: str = Field(min_length=10, max_length=800)


class ModerationInput(Contract):
    status: Literal["verified", "rejected", "duplicate", "resolved"]
    reason: str = Field(min_length=10, max_length=500)
    road_edge_ids: list[str] = Field(default_factory=list, max_length=20)
    ttl_minutes: int = Field(default=120, ge=15, le=360)
    duplicate_of: str | None = None
    publish_image: bool = False
    privacy_reviewed: bool = False


class SubscriptionInput(Contract):
    ward_id: str = Field(min_length=1, max_length=50)
    channel: Literal["in_app"] = "in_app"
    consented: Literal[True]


class RouteInput(Contract):
    start: Point
    end: Point


class LoginInput(Contract):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class DeliveryFault(Contract):
    fail_next: int = Field(ge=0, le=10)


class IngestInput(Contract):
    records: list[dict] = Field(min_length=1, max_length=1000)


class ObservationInput(Point):
    source_record_key: str = Field(min_length=1, max_length=150)
    source_id: str = Field(min_length=1, max_length=80)
    area_id: str = Field(min_length=1, max_length=50)
    observed_at: datetime
    received_at: datetime
    variable: Literal["rainfall", "water_level"]
    value: float | None = None
    unit: str = Field(min_length=1, max_length=30)
    quality: Literal["good", "suspect", "missing"] = "good"
    interval_minutes: int = Field(ge=1, le=1440)

    @field_validator("observed_at", "received_at")
    @classmethod
    def require_timezone(cls, value):
        return utc(value)
