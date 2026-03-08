"""FastAPI server exposing AI Data QA CLI workflows as HTTP endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import typer
import yaml

from ai_data_qa.cli import (
    analyze as cli_analyze,
    generate_tests as cli_generate_tests,
    report as cli_report,
    run_tests as cli_run_tests,
    scan as cli_scan,
)
from ai_data_qa.config import load_config

REPORT_PATH = Path("reports/data_quality_report.json")
HISTORY_PATH = Path("reports/dq_history.json")

app = FastAPI(title="AI Data QA API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DatasetRequest(BaseModel):
    """Base request model for dataset-driven QA operations."""

    dataset: str = Field(..., min_length=1, description="BigQuery dataset name")
    config_path: str = Field(default="config.yaml", description="Path to config file")


class ScanRequest(DatasetRequest):
    """Request payload for scan endpoint."""

    profile: bool = True


class GenerateTestsRequest(DatasetRequest):
    """Request payload for generate-tests endpoint."""

    use_ai: bool = False


class OperationResponse(BaseModel):
    """Standard API response for QA command execution."""

    status: str
    message: str
    action: str
    dataset: str


def _run_with_dataset(
    *, dataset: str, config_path: str, operation: Callable[..., None], **kwargs: Any
) -> None:
    """Run a CLI operation using a temporary config with an overridden dataset."""
    config = load_config(config_path)
    config.dataset = dataset

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
            yaml.safe_dump(config.model_dump(), tmp_file, sort_keys=False)
            temp_path = tmp_file.name
        operation(config_path=temp_path, **kwargs)
    except typer.Exit as exc:
        raise RuntimeError(f"Command exited with code {exc.exit_code}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


def _update_report_status(action: str, dataset: str, status: str, message: str) -> None:
    """Persist operation status metadata into reports/data_quality_report.json."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if REPORT_PATH.exists():
        try:
            payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"dataset": dataset, "tables": []}
    else:
        payload = {"dataset": dataset, "tables": []}

    payload.setdefault("dataset", dataset)
    payload.setdefault("tables", [])
    payload["last_operation"] = {
        "action": action,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _execute_operation(
    *,
    action: str,
    dataset: str,
    config_path: str,
    operation: Callable[..., None],
    message: str,
    **kwargs: Any,
) -> OperationResponse:
    """Execute an operation and normalize response/error handling."""
    try:
        _run_with_dataset(
            dataset=dataset,
            config_path=config_path,
            operation=operation,
            **kwargs,
        )
        _update_report_status(action, dataset, "completed", message)
        return OperationResponse(
            status="completed",
            message=message,
            action=action,
            dataset=dataset,
        )
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
        _update_report_status(action, dataset, "error", error_message)
        raise HTTPException(status_code=500, detail=error_message) from exc


@app.post("/scan", response_model=OperationResponse)
def scan_endpoint(request: ScanRequest) -> OperationResponse:
    """Scan schema/profile data for a dataset."""
    return _execute_operation(
        action="scan",
        dataset=request.dataset,
        config_path=request.config_path,
        operation=cli_scan,
        profile=request.profile,
        message="Scan completed",
    )


@app.post("/generate-tests", response_model=OperationResponse)
def generate_tests_endpoint(request: GenerateTestsRequest) -> OperationResponse:
    """Generate static and optional AI-assisted data quality tests."""
    return _execute_operation(
        action="generate-tests",
        dataset=request.dataset,
        config_path=request.config_path,
        operation=cli_generate_tests,
        use_ai=request.use_ai,
        message="Test generation completed",
    )


@app.post("/run-tests", response_model=OperationResponse)
def run_tests_endpoint(request: DatasetRequest) -> OperationResponse:
    """Execute generated tests in BigQuery."""
    return _execute_operation(
        action="run-tests",
        dataset=request.dataset,
        config_path=request.config_path,
        operation=cli_run_tests,
        message="Test execution completed",
    )


@app.post("/analyze", response_model=OperationResponse)
def analyze_endpoint(request: DatasetRequest) -> OperationResponse:
    """Analyze failed tests with AI insights."""
    return _execute_operation(
        action="analyze",
        dataset=request.dataset,
        config_path=request.config_path,
        operation=cli_analyze,
        message="Failure analysis completed",
    )


@app.post("/report", response_model=OperationResponse)
def report_endpoint(request: DatasetRequest) -> OperationResponse:
    """Generate an updated data quality report."""
    return _execute_operation(
        action="report",
        dataset=request.dataset,
        config_path=request.config_path,
        operation=cli_report,
        message="Report generation completed",
    )


@app.get("/report")
def get_report() -> dict[str, Any]:
    """Return the latest JSON data quality report."""
    if not REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Report JSON is invalid") from exc


@app.get("/history")
def get_history() -> dict[str, Any]:
    """Return trend history data if available."""
    if not HISTORY_PATH.exists():
        return {"dataset": "", "history": []}

    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="History JSON is invalid") from exc
