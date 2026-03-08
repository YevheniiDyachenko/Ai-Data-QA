from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ai_data_qa.errors import ExecutionError
from ai_data_qa.scheduler.models import SchedulerJob, SchedulerJobUpdate


class SchedulerStore:
    def __init__(self, path: str = "reports/scheduler_jobs.json") -> None:
        self.path = Path(path)

    def list_jobs(self) -> list[SchedulerJob]:
        payload = self._read_payload()
        return [SchedulerJob(**item) for item in payload]

    def get_job(self, job_id: str) -> SchedulerJob:
        for job in self.list_jobs():
            if job.id == job_id:
                return job
        raise ExecutionError("Scheduler job not found", job_id=job_id, code="SCHEDULER_JOB_NOT_FOUND")

    def create_job(self, job: SchedulerJob) -> SchedulerJob:
        jobs = self.list_jobs()
        jobs.append(job)
        self._write_jobs(jobs)
        return job

    def update_job(self, job_id: str, update: SchedulerJobUpdate) -> SchedulerJob:
        jobs = self.list_jobs()
        now = datetime.now(timezone.utc).isoformat()

        for idx, job in enumerate(jobs):
            if job.id == job_id:
                updates = update.model_dump(exclude_none=True)
                if "cron" in updates:
                    updates.setdefault("interval_seconds", None)
                if "interval_seconds" in updates:
                    updates.setdefault("cron", None)

                updated = job.model_copy(update={**updates, "updated_at": now})
                jobs[idx] = SchedulerJob(**updated.model_dump())
                self._write_jobs(jobs)
                return jobs[idx]

        raise ExecutionError("Scheduler job not found", job_id=job_id, code="SCHEDULER_JOB_NOT_FOUND")

    def delete_job(self, job_id: str) -> None:
        jobs = self.list_jobs()
        filtered_jobs = [job for job in jobs if job.id != job_id]
        if len(filtered_jobs) == len(jobs):
            raise ExecutionError("Scheduler job not found", job_id=job_id, code="SCHEDULER_JOB_NOT_FOUND")
        self._write_jobs(filtered_jobs)

    def mark_run(self, job_id: str) -> SchedulerJob:
        jobs = self.list_jobs()
        now = datetime.now(timezone.utc).isoformat()

        for idx, job in enumerate(jobs):
            if job.id == job_id:
                updated = job.model_copy(update={"last_run_at": now, "updated_at": now})
                jobs[idx] = SchedulerJob(**updated.model_dump())
                self._write_jobs(jobs)
                return jobs[idx]

        raise ExecutionError("Scheduler job not found", job_id=job_id, code="SCHEDULER_JOB_NOT_FOUND")

    def _read_payload(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ExecutionError("Invalid scheduler jobs JSON", path=str(self.path)) from exc

        if isinstance(payload, dict) and "jobs" in payload:
            payload = payload["jobs"]
        if not isinstance(payload, list):
            raise ExecutionError("Scheduler jobs payload must be a list", path=str(self.path))
        return payload

    def _write_jobs(self, jobs: list[SchedulerJob]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"jobs": [job.model_dump() for job in jobs]}
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
