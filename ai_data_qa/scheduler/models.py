from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class SchedulerJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset: str = Field(..., min_length=1)
    cron: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, gt=0)
    enabled: bool = True
    retry_count: int = Field(default=3, ge=0)
    backoff_seconds: float = Field(default=2.0, ge=0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run_at: Optional[str] = None

    @model_validator(mode="after")
    def validate_schedule(self) -> "SchedulerJob":
        has_cron = bool(self.cron)
        has_interval = self.interval_seconds is not None
        if has_cron == has_interval:
            raise ValueError("Exactly one of 'cron' or 'interval_seconds' must be set")
        return self


class SchedulerJobUpdate(BaseModel):
    dataset: Optional[str] = Field(default=None, min_length=1)
    cron: Optional[str] = None
    interval_seconds: Optional[int] = Field(default=None, gt=0)
    enabled: Optional[bool] = None
    retry_count: Optional[int] = Field(default=None, ge=0)
    backoff_seconds: Optional[float] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_schedule(self) -> "SchedulerJobUpdate":
        if self.cron is not None and self.interval_seconds is not None:
            raise ValueError("Provide either 'cron' or 'interval_seconds', not both")
        return self
