import time
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.tests_engine.models import TestCase, TestResult
from ai_data_qa.tests_engine.sql_validator import validate_select_query
from ai_data_qa.utils.logger import logger, log_event
from ai_data_qa.errors import AppError, ExecutionError


class TestRunner:
    def __init__(self, bq_client: BQClient, max_rows_limit: int = 10000):
        self.bq_client = bq_client
        self.max_rows_limit = max_rows_limit

    def run_tests(self, tests: List[TestCase], include_tags: Optional[List[str]] = None) -> List[TestResult]:
        """Executes a list of tests and returns results."""
        results = []
        selected_tests = tests
        if include_tags:
            include_set = set(include_tags)
            selected_tests = [t for t in tests if include_set.intersection(t.tags)]

        for test in selected_tests:
            start_time = time.time()
            try:
                safe_sql = validate_select_query(test.sql, max_limit=self.max_rows_limit)
                rows = self.bq_client.execute_query(safe_sql)
                failed_rows = rows[0]["failed_rows"] if rows else 0
                execution_time = time.time() - start_time

                status = "PASSED" if failed_rows == 0 else "FAILED"

                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.test_name,
                    sql=safe_sql,
                    failed_rows=failed_rows,
                    execution_time=execution_time,
                    status=status,
                ))
                log_event(
                    "test_executed",
                    table_name=test.table_name,
                    test_name=test.test_name,
                    status=status,
                    failed_rows=failed_rows,
                    execution_time=execution_time,
                    tags=test.tags,
                )
            except AppError as app_error:
                execution_time = time.time() - start_time
                log_event(
                    "test_execution_error",
                    table_name=test.table_name,
                    test_name=test.test_name,
                    category=app_error.category,
                    code=app_error.code,
                    details=app_error.details,
                )
                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.test_name,
                    sql=test.sql,
                    failed_rows=-1,
                    execution_time=execution_time,
                    status="ERROR",
                    error_category=app_error.category,
                    error_code=app_error.code,
                    error_message=app_error.message,
                ))
            except Exception as e:
                execution_time = time.time() - start_time
                wrapped_error = ExecutionError("Unhandled error running test", test_name=test.test_name, reason=str(e))
                logger.error(f"Error running test {test.test_name}: {e}")
                log_event(
                    "test_execution_error",
                    table_name=test.table_name,
                    test_name=test.test_name,
                    category=wrapped_error.category,
                    code=wrapped_error.code,
                    details=wrapped_error.details,
                )
                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.test_name,
                    sql=test.sql,
                    failed_rows=-1,
                    execution_time=execution_time,
                    status="ERROR",
                    error_category=wrapped_error.category,
                    error_code=wrapped_error.code,
                    error_message=wrapped_error.message,
                ))
        return results

    def generate_run_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{timestamp}-{uuid4().hex[:8]}"

    def save_results(
        self,
        results: List[TestResult],
        output_path: str = "test_results.json",
        run_id: Optional[str] = None,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> str:
        """Saves test results to a run-specific JSON file and returns run_id."""
        current_run_id = run_id or self.generate_run_id()
        runs_root = Path("reports") / "runs"
        run_dir = runs_root / current_run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "run_id": current_run_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "results": [r.model_dump() for r in results],
        }

        run_results_path = run_dir / "test_results.json"
        run_results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        latest_path = runs_root / "latest_run.txt"
        latest_path.write_text(current_run_id, encoding="utf-8")

        with open(output_path, "w") as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Saved test results to {run_results_path}")
        return current_run_id

    def load_results(self, input_path: str = "test_results.json") -> List[TestResult]:
        """Loads test results from a JSON file."""
        if not os.path.exists(input_path):
            return []
        with open(input_path, "r") as f:
            data = json.load(f)

        if isinstance(data, dict) and "results" in data:
            raw_results = data["results"]
        else:
            raw_results = data
        return [TestResult(**r) for r in raw_results]
