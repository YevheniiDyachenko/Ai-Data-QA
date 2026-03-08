import pytest
from ai_data_qa.tests_engine.generator import TestGenerator
from ai_data_qa.tests_engine.models import TableSchema, ColumnSchema

def test_generate_static_tests():
    generator = TestGenerator(output_dir="tests_generated_test")
    schema = TableSchema(
        table_name="users",
        columns=[
            ColumnSchema(name="user_id", data_type="INT64", is_nullable=False),
            ColumnSchema(name="email", data_type="STRING", is_nullable=True),
        ]
    )

    tests = generator.generate_static_tests("project", "dataset", schema)

    assert len(tests) >= 2
    # Check for not null test on user_id
    assert any(t.test_name == "users_user_id_not_null" for t in tests)
    # Check for uniqueness test on user_id
    assert any(t.test_name == "users_user_id_unique" for t in tests)

    # Verify SQL content for not null
    not_null_test = next(t for t in tests if t.test_name == "users_user_id_not_null")
    assert "user_id IS NULL" in not_null_test.sql
    assert "failed_rows" in not_null_test.sql


def test_generate_ai_tests_invalid_contract_fallback():
    class BadClient:
        def completion(self, prompt: str) -> str:
            return "not-json"

    generator = TestGenerator(output_dir="tests_generated_test", ai_client=BadClient())
    schema = TableSchema(
        table_name="users",
        columns=[ColumnSchema(name="user_id", data_type="INT64", is_nullable=False)]
    )

    tests = generator.generate_ai_tests(schema)
    assert tests == []
