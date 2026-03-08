import os
from typing import List, Dict, Optional
import json
from ai_data_qa.tests_engine.models import TableSchema, TestCase
from ai_data_qa.ai.client import AIClient
from ai_data_qa.ai.prompts import TEST_GENERATION_PROMPT
from ai_data_qa.utils.logger import logger, log_event
from ai_data_qa.errors import AIContractError
from ai_data_qa.config import ChecksConfig


class TestGenerator:
    def __init__(self, output_dir: str = "tests_generated", ai_client: AIClient = None):
        self.output_dir = output_dir
        self.ai_client = ai_client
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_static_tests(
        self,
        project_id: str,
        dataset_id: str,
        table_schema: TableSchema,
        checks: Optional[ChecksConfig] = None,
    ) -> List[TestCase]:
        """Generates static SQL tests based on schema and configured checks."""
        checks = checks or ChecksConfig()
        table_name = table_schema.table_name
        full_table_path = f"`{project_id}.{dataset_id}.{table_name}`"
        tests = []

        for column in table_schema.columns:
            if not column.is_nullable:
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_not_null",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} IS NULL",
                    description=f"Checks if column {column.name} has null values.",
                    tags=["nulls"],
                    quality_dimension="completeness",
                ))

            if "id" in column.name.lower():
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_unique",
                    sql=f"SELECT COUNT(*) as failed_rows FROM (SELECT {column.name} FROM {full_table_path} GROUP BY {column.name} HAVING COUNT(*) > 1)",
                    description=f"Checks if column {column.name} is unique.",
                    tags=["distribution"],
                    quality_dimension="validity",
                ))

            if column.data_type in ["INT64", "FLOAT64", "NUMERIC", "BIGNUMERIC"] and (
                "price" in column.name.lower() or "amount" in column.name.lower()
            ):
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_positive",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} < 0",
                    description=f"Checks if column {column.name} is positive.",
                    tags=["distribution"],
                    quality_dimension="validity",
                ))

            if column.data_type in ["TIMESTAMP", "DATETIME", "DATE"]:
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_not_future",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE {column.name} > CURRENT_TIMESTAMP()",
                    description=f"Checks if column {column.name} is not in the future.",
                    tags=["freshness"],
                    quality_dimension="freshness",
                ))

            if "email" in column.name.lower() and column.data_type == "STRING":
                tests.append(TestCase(
                    table_name=table_name,
                    test_name=f"{table_name}_{column.name}_format",
                    sql=f"SELECT COUNT(*) as failed_rows FROM {full_table_path} WHERE NOT REGEXP_CONTAINS({column.name}, r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$')",
                    description=f"Checks if column {column.name} has a valid email format.",
                    tags=["distribution"],
                    quality_dimension="validity",
                ))

        tests.extend(self._generate_accepted_values_tests(table_name, full_table_path, table_schema, checks))
        tests.extend(self._generate_relationship_tests(project_id, dataset_id, table_name, full_table_path, table_schema, checks))
        tests.extend(self._generate_freshness_sla_tests(table_name, full_table_path, table_schema, checks))
        tests.extend(self._generate_row_count_drift_tests(project_id, dataset_id, table_name, full_table_path, checks))
        tests.extend(self._generate_schema_drift_tests(project_id, dataset_id, table_name, table_schema, checks))

        return tests

    def _generate_accepted_values_tests(self, table_name: str, full_table_path: str, table_schema: TableSchema, checks: ChecksConfig) -> List[TestCase]:
        if not checks.accepted_values.enabled:
            return []

        accepted_map: Dict[str, List[str]] = {
            "status": ["active", "inactive", "pending", "cancelled"],
            "state": ["new", "processing", "done", "failed"],
            "type": ["standard", "premium", "trial"],
        }
        tests = []
        for column in table_schema.columns:
            if column.data_type != "STRING":
                continue
            rule_values = next((vals for key, vals in accepted_map.items() if key in column.name.lower()), None)
            if not rule_values:
                continue
            accepted_sql = ", ".join([f"'{v}'" for v in rule_values])
            tests.append(TestCase(
                table_name=table_name,
                test_name=f"{table_name}_{column.name}_accepted_values",
                sql=(
                    f"SELECT COUNT(*) as failed_rows FROM {full_table_path} "
                    f"WHERE {column.name} IS NOT NULL AND LOWER({column.name}) NOT IN ({accepted_sql})"
                ),
                description=f"Checks accepted values for {column.name}: {', '.join(rule_values)}.",
                tags=["accepted_values", "validity"],
                quality_dimension="validity",
                threshold_value=checks.accepted_values.threshold,
                threshold_operator="<=",
            ))
        return tests

    def _generate_relationship_tests(
        self,
        project_id: str,
        dataset_id: str,
        table_name: str,
        full_table_path: str,
        table_schema: TableSchema,
        checks: ChecksConfig,
    ) -> List[TestCase]:
        if not checks.relationship.enabled:
            return []

        tests = []
        for column in table_schema.columns:
            column_lower = column.name.lower()
            if not column_lower.endswith("_id") or column_lower == "id":
                continue

            ref_table = f"{column_lower[:-3]}s"
            ref_path = f"`{project_id}.{dataset_id}.{ref_table}`"
            tests.append(TestCase(
                table_name=table_name,
                test_name=f"{table_name}_{column.name}_relationship",
                sql=(
                    "SELECT COUNT(*) as failed_rows "
                    f"FROM {full_table_path} src "
                    f"WHERE {column.name} IS NOT NULL "
                    f"AND NOT EXISTS (SELECT 1 FROM {ref_path} ref WHERE ref.id = src.{column.name})"
                ),
                description=f"Checks FK-like relationship of {column.name} to {ref_table}.id.",
                tags=["relationship", "consistency"],
                quality_dimension="consistency",
                threshold_value=checks.relationship.threshold,
                threshold_operator="<=",
            ))
        return tests

    def _generate_freshness_sla_tests(self, table_name: str, full_table_path: str, table_schema: TableSchema, checks: ChecksConfig) -> List[TestCase]:
        if not checks.freshness_sla.enabled:
            return []

        tests = []
        for column in table_schema.columns:
            if column.data_type not in ["TIMESTAMP", "DATETIME", "DATE"]:
                continue
            tests.append(TestCase(
                table_name=table_name,
                test_name=f"{table_name}_{column.name}_freshness_sla",
                sql=(
                    "SELECT "
                    f"TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(CAST({column.name} AS TIMESTAMP)), HOUR) AS staleness_hours, "
                    "0 AS failed_rows "
                    f"FROM {full_table_path}"
                ),
                description=f"Checks if {column.name} is updated within {checks.freshness_sla.threshold} hours.",
                tags=["freshness", "sla"],
                quality_dimension="freshness",
                threshold_field="staleness_hours",
                threshold_operator="<=",
                threshold_value=checks.freshness_sla.threshold,
            ))
        return tests

    def _generate_row_count_drift_tests(
        self,
        project_id: str,
        dataset_id: str,
        table_name: str,
        full_table_path: str,
        checks: ChecksConfig,
    ) -> List[TestCase]:
        if not checks.row_count_drift.enabled:
            return []

        sql = (
            "WITH daily AS ("
            f"SELECT DATE(_PARTITIONTIME) AS ds, COUNT(*) AS cnt FROM {full_table_path} "
            "WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 DAY) "
            "GROUP BY 1"
            "), baseline AS ("
            "SELECT AVG(cnt) AS avg_cnt FROM daily WHERE ds < CURRENT_DATE()"
            "), current_day AS ("
            "SELECT IFNULL(MAX(cnt), 0) AS curr_cnt FROM daily WHERE ds = CURRENT_DATE()"
            ") "
            "SELECT SAFE_DIVIDE(ABS(curr_cnt - avg_cnt), NULLIF(avg_cnt, 0)) AS drift_pct, 0 AS failed_rows "
            "FROM baseline CROSS JOIN current_day"
        )

        return [
            TestCase(
                table_name=table_name,
                test_name=f"{table_name}_row_count_drift",
                sql=sql,
                description=(
                    f"Checks row-count drift vs 7-day baseline (threshold {checks.row_count_drift.threshold:.2f})."
                ),
                tags=["row_count", "drift", "freshness"],
                quality_dimension="freshness",
                threshold_field="drift_pct",
                threshold_operator="<=",
                threshold_value=checks.row_count_drift.threshold,
            )
        ]

    def _generate_schema_drift_tests(
        self,
        project_id: str,
        dataset_id: str,
        table_name: str,
        table_schema: TableSchema,
        checks: ChecksConfig,
    ) -> List[TestCase]:
        if not checks.schema_drift.enabled:
            return []

        expected_columns = len(table_schema.columns)
        sql = (
            "WITH current_schema AS ("
            f"SELECT COUNT(*) AS current_columns FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS` "
            f"WHERE table_name = '{table_name}'"
            ") "
            f"SELECT ABS(current_columns - {expected_columns}) AS schema_drift_columns, 0 AS failed_rows FROM current_schema"
        )

        return [
            TestCase(
                table_name=table_name,
                test_name=f"{table_name}_schema_drift",
                sql=sql,
                description="Checks schema drift by comparing current and expected column count.",
                tags=["schema", "drift", "consistency"],
                quality_dimension="consistency",
                threshold_field="schema_drift_columns",
                threshold_operator="<=",
                threshold_value=checks.schema_drift.threshold,
            )
        ]

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
                    quality_dimension=test.get("quality_dimension"),
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
