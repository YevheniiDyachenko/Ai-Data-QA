from unittest.mock import MagicMock
from ai_data_qa.tests_engine.runner import TestRunner
from ai_data_qa.tests_engine.models import TestCase
from ai_data_qa.bigquery.client import BQClient


def test_run_tests():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [{"failed_rows": 5}]

    runner = TestRunner(mock_bq_client)
    tests = [
        TestCase(table_name="users", test_name="test1", sql="SELECT 1 as failed_rows")
    ]

    results = runner.run_tests(tests)

    assert len(results) == 1
    assert results[0].test_name == "test1"
    assert results[0].failed_rows == 5
    assert results[0].status == "FAILED"
    assert "LIMIT" in results[0].sql.upper()


def test_run_tests_passed():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [{"failed_rows": 0}]

    runner = TestRunner(mock_bq_client)
    tests = [
        TestCase(table_name="users", test_name="test1", sql="SELECT 0 as failed_rows")
    ]

    results = runner.run_tests(tests)

    assert results[0].status == "PASSED"
    assert results[0].failed_rows == 0


def test_run_tests_filter_by_tags():
    mock_bq_client = MagicMock(spec=BQClient)
    mock_bq_client.execute_query.return_value = [{"failed_rows": 0}]

    runner = TestRunner(mock_bq_client)
    tests = [
        TestCase(table_name="users", test_name="freshness_test", sql="SELECT 0 as failed_rows", tags=["freshness"]),
        TestCase(table_name="users", test_name="nulls_test", sql="SELECT 0 as failed_rows", tags=["nulls"]),
    ]

    results = runner.run_tests(tests, include_tags=["freshness"])

    assert len(results) == 1
    assert results[0].test_name == "freshness_test"


def test_run_tests_sql_validation_error():
    mock_bq_client = MagicMock(spec=BQClient)
    runner = TestRunner(mock_bq_client)

    tests = [TestCase(table_name="users", test_name="bad_sql", sql="DELETE FROM users")]
    results = runner.run_tests(tests)

    assert len(results) == 1
    assert results[0].status == "ERROR"
    assert results[0].error_code == "SQL_VALIDATION_ERROR"
