import os
from typing import List
import json
from ai_data_qa.tests_engine.models import TableSchema, TestCase, ProfilingResult
from ai_data_qa.ai.client import AIClient
from ai_data_qa.ai.prompts import TEST_GENERATION_PROMPT
from ai_data_qa.utils.logger import logger, log_event
from ai_data_qa.errors import AIContractError

class TestGenerator:
    def __init__(self, output_dir: str = "tests_generated", ai_client: AIClient = None):
        self.output_dir = output_dir
        self.ai_client = ai_client
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_static_tests(self, project_id: str, dataset_id: str, table_schema: TableSchema) -> List[TestCase]:
        """Generates static SQL tests based on schema."""
        table_name = table_schema.table_name
        full_table_path = f"`{project_id}.{dataset_id}.{table_name}`"
        tests = []

        for column in table_schema.columns:
            # Not Null test
            if not column.is_nullable:
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_not_null",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} IS NULL",
                    description=f"Checks if column {column.name} has null values.",
                    tags=["nulls"]
                ))

            # Uniqueness (placeholder logic - usually applied to ID columns)
            if "id" in column.name.lower():
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_unique",
                    sql=f"SELECT COUNT(*) as failed_rows FROM (SELECT {column.name} FROM {full_table_path} GROUP BY {column.name} HAVING COUNT(*) > 1)",
                    description=f"Checks if column {column.name} is unique.",
                    tags=["distribution"]
                ))

            # Numeric Range (example: values should be positive)
            if column.data_type in ["INT64", "FLOAT64", "NUMERIC", "BIGNUMERIC"] and ("price" in column.name.lower() or "amount" in column.name.lower()):
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_positive",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} < 0",
                    description=f"Checks if column {column.name} is positive.",
                    tags=["distribution"]
                ))

            # Timestamp validation (example: should not be in the future)
            if column.data_type in ["TIMESTAMP", "DATETIME", "DATE"]:
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_not_future",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} > CURRENT_TIMESTAMP()",
                    description=f"Checks if column {column.name} is not in the future.",
                    tags=["freshness"]
                ))

            # Regex validation (example: email format)
            if "email" in column.name.lower() and column.data_type == "STRING":
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_format",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE NOT REGEXP_CONTAINS({column.name}, r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$')",
                    description=f"Checks if column {column.name} has a valid email format.",
                    tags=["distribution"]
                ))

        return tests

    def generate_ai_tests(self, table_schema: TableSchema) -> List[TestCase]:
        """Generates additional SQL tests using AI."""
        if not self.ai_client:
            logger.warning("AI client not provided, skipping AI test generation.")
            return []

        schema_desc = "\n".join([f"{c.name} ({c.data_type})" for c in table_schema.columns])
        profiling_desc = "None"
        if table_schema.profiling_results:
            profiling_desc = "\n".join([
                f"Column: {r.column_name}, Rows: {r.row_count}, Nulls: {r.null_count}, Distinct: {r.distinct_count}"
                for r in table_schema.profiling_results
            ])

        prompt = TEST_GENERATION_PROMPT.format(
            table_name=table_schema.table_name,
            schema_desc=schema_desc,
            profiling_desc=profiling_desc
        )

        try:
            response = self.ai_client.completion(prompt)
            payload = json.loads(response)
            if not isinstance(payload, dict) or "tests" not in payload or not isinstance(payload["tests"], list):
                raise AIContractError("AI response does not match expected JSON contract", response=response)

            ai_tests = []
            for i, test in enumerate(payload["tests"]):
                if not isinstance(test, dict) or not test.get("sql"):
                    raise AIContractError("AI test item missing SQL", item=test)
                ai_tests.append(TestCase(
                    table_name=table_schema.table_name,
                    test_name=test.get("test_name") or f"{table_schema.table_name}_ai_test_{i+1}",
                    sql=test["sql"],
                    description=test.get("description") or "AI-generated data quality test.",
                    tags=test.get("tags") or ["distribution"],
                ))
            return ai_tests
        except AIContractError as contract_error:
            log_event(
                "ai_test_generation_contract_fallback",
                table_name=table_schema.table_name,
                category=contract_error.category,
                code=contract_error.code,
                details=contract_error.details,
            )
            return []
        except Exception as e:
            logger.error(f"Failed to generate AI tests for {table_schema.table_name}: {e}")
            return []

    def save_tests(self, table_name: str, tests: List[TestCase]):
        """Saves generated tests to a SQL file."""
        file_path = os.path.join(self.output_dir, f"{table_name}.sql")
        with open(file_path, "w") as f:
            for test in tests:
                f.write(f"-- Name: {test.test_name}\n")
                f.write(f"-- Description: {test.description}\n")
                f.write(f"{test.sql};\n\n")
        logger.info(f"Saved {len(tests)} tests to {file_path}")
