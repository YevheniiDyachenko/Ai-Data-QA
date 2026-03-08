import pytest

from ai_data_qa.errors import SQLValidationError
from ai_data_qa.tests_engine.sql_validator import validate_select_query


def test_validate_select_query_adds_limit():
    sql = "SELECT COUNT(*) as failed_rows FROM table_a"
    validated = validate_select_query(sql, max_limit=50)
    assert validated.endswith("LIMIT 50")


def test_validate_select_query_blocks_non_select():
    with pytest.raises(SQLValidationError):
        validate_select_query("UPDATE table_a SET value = 1")


def test_validate_select_query_blocks_limit_overflow():
    with pytest.raises(SQLValidationError):
        validate_select_query("SELECT * FROM table_a LIMIT 10001", max_limit=10000)
