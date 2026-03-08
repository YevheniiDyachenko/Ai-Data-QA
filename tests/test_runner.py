import pytest
from unittest.mock import MagicMock
from ai_data_qa.tests_engine.runner import TestRunner
from ai_data_qa.tests_engine.models import TestCase
from ai_data_qa.bigquery.client import BQClient

def test_run_tests():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [{"failed_rows": 5}]

    runner = TestRunner(mock_bq_client)
    tests = [
        TestCase(table_name="users", test_name="test1", sql="SELECT ...")
    ]

    results = runner.run_tests(tests)

    assert len(results) == 1
    assert results[0].test_name == "test1"
    assert results[0].failed_rows == 5
    assert results[0].status == "FAILED"

def test_run_tests_passed():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [{"failed_rows": 0}]

    runner = TestRunner(mock_bq_client)
    tests = [
        TestCase(table_name="users", test_name="test1", sql="SELECT ...")
    ]

    results = runner.run_tests(tests)

    assert results[0].status == "PASSED"
    assert results[0].failed_rows == 0
