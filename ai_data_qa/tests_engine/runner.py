import time
import json
import os
from typing import List, Optional, Union
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.tests_engine.models import TestCase, TestResult, RuleDefinition
from ai_data_qa.tests_engine.sql_validator import validate_select_query
from ai_data_qa.utils.logger import logger, log_event
from ai_data_qa.errors import AppError, ExecutionError


class TestRunner:
    def __init__(self, bq_client: BQClient, max_rows_limit: int = 10000):
        self.bq_client = bq_client
        self.max_rows_limit = max_rows_limit

    def run_tests(self, tests: List[Union[TestCase, RuleDefinition]], include_tags: Optional[List[str]] = None) -> List[TestResult]:
        """Executes a list of tests and returns results."""
        results = []
        normalized_tests: List[RuleDefinition] = []
        for test in tests:
            if isinstance(test, RuleDefinition):
                normalized_tests.append(test)
            else:
                normalized_tests.append(RuleDefinition(
                    id=test.test_name,
                    table_name=test.table_name,
                    rule_type="legacy_test_case",
                    severity="medium",
                    owner="unknown",
                    dimension="consistency",
                    sql=test.sql,
                    enabled=True,
                    tags=test.tags,
                    metadata={"description": test.description} if test.description else {},
                ))

        selected_tests = normalized_tests
        if include_tags:
            include_set = set(include_tags)
            selected_tests = [t for t in normalized_tests if include_set.intersection(t.tags)]

        for test in selected_tests:
            if not test.enabled:
                log_event(
                    "test_skipped_disabled",
                    table_name=test.table_name,
                    rule_id=test.id,
                    severity=test.severity,
                    owner=test.owner,
                )
                continue

            start_time = time.time()
            try:
                safe_sql = validate_select_query(test.sql, max_limit=self.max_rows_limit)
                rows = self.bq_client.execute_query(safe_sql)
                failed_rows = rows[0]["failed_rows"] if rows else 0
                execution_time = time.time() - start_time

                status = "PASSED" if failed_rows == 0 else "FAILED"

                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.id,
                    sql=safe_sql,
                    failed_rows=failed_rows,
                    execution_time=execution_time,
                    status=status,
                ))
                log_event(
                    "test_executed",
                    table_name=test.table_name,
                    test_name=test.id,
                    rule_id=test.id,
                    severity=test.severity,
                    owner=test.owner,
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
                    test_name=test.id,
                    rule_id=test.id,
                    severity=test.severity,
                    owner=test.owner,
                    category=app_error.category,
                    code=app_error.code,
                    details=app_error.details,
                )
                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.id,
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
                wrapped_error = ExecutionError("Unhandled error running test", test_name=test.id, reason=str(e))
                logger.error(f"Error running test {test.id}: {e}")
                log_event(
                    "test_execution_error",
                    table_name=test.table_name,
                    test_name=test.id,
                    rule_id=test.id,
                    severity=test.severity,
                    owner=test.owner,
                    category=wrapped_error.category,
                    code=wrapped_error.code,
                    details=wrapped_error.details,
                )
                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.id,
                    sql=test.sql,
                    failed_rows=-1,
                    execution_time=execution_time,
                    status="ERROR",
                    error_category=wrapped_error.category,
                    error_code=wrapped_error.code,
                    error_message=wrapped_error.message,
                ))
        return results

    def save_results(self, results: List[TestResult], output_path: str = "test_results.json"):
        """Saves test results to a JSON file."""
        with open(output_path, "w") as f:
            json.dump({"results": [r.model_dump() for r in results]}, f, indent=2)
        logger.info(f"Saved test results to {output_path}")

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
