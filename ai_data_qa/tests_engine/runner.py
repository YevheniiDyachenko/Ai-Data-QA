import time
import json
import os
from typing import List
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.tests_engine.models import TestCase, TestResult
from ai_data_qa.utils.logger import logger

class TestRunner:
    def __init__(self, bq_client: BQClient):
        self.bq_client = bq_client

    def run_tests(self, tests: List[TestCase]) -> List[TestResult]:
        """Executes a list of tests and returns results."""
        results = []
        for test in tests:
            start_time = time.time()
            try:
                rows = self.bq_client.execute_query(test.sql)
                failed_rows = rows[0]["failed_rows"] if rows else 0
                execution_time = time.time() - start_time

                status = "PASSED" if failed_rows == 0 else "FAILED"

                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.test_name,
                    sql=test.sql,
                    failed_rows=failed_rows,
                    execution_time=execution_time,
                    status=status
                ))
                logger.info(f"Test {test.test_name} {status} ({failed_rows} failed rows)")
            except Exception as e:
                logger.error(f"Error running test {test.test_name}: {e}")
                results.append(TestResult(
                    table_name=test.table_name,
                    test_name=test.test_name,
                    sql=test.sql,
                    failed_rows=-1, # Indicates error
                    execution_time=time.time() - start_time,
                    status="ERROR"
                ))
        return results

    def save_results(self, results: List[TestResult], output_path: str = "test_results.json"):
        """Saves test results to a JSON file."""
        with open(output_path, "w") as f:
            json.dump([r.model_dump() for r in results], f, indent=2)
        logger.info(f"Saved test results to {output_path}")

    def load_results(self, input_path: str = "test_results.json") -> List[TestResult]:
        """Loads test results from a JSON file."""
        if not os.path.exists(input_path):
            return []
        with open(input_path, "r") as f:
            data = json.load(f)
        return [TestResult(**r) for r in data]
