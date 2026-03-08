from typing import List
from ai_data_qa.ai.client import AIClient
from ai_data_qa.ai.prompts import FAILURE_ANALYSIS_PROMPT
from ai_data_qa.tests_engine.models import TestResult, TableSchema, AnalysisResult

class AIAnalyzer:
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def analyze_failure(self, test_result: TestResult, table_schema: TableSchema) -> AnalysisResult:
        """Analyzes a failed test using AI."""
        schema_desc = "\n".join([f"{c.name} {c.data_type}" for c in table_schema.columns])

        prompt = FAILURE_ANALYSIS_PROMPT.format(
            table_name=test_result.table_name,
            test_name=test_result.test_name,
            failed_rows=test_result.failed_rows,
            sql=test_result.sql,
            schema_desc=schema_desc
        )

        response = self.ai_client.completion(prompt)

        # Improved parsing logic
        findings = ""
        investigation = ""

        if "Findings:" in response:
            parts = response.split("Findings:")
            if "Suggested Investigation:" in parts[1]:
                sub_parts = parts[1].split("Suggested Investigation:")
                findings = sub_parts[0].strip()
                investigation = sub_parts[1].strip()
            else:
                findings = parts[1].strip()
        elif "Suggested Investigation:" in response:
            parts = response.split("Suggested Investigation:")
            findings = parts[0].strip()
            investigation = parts[1].strip()
        else:
            findings = response.strip()

        if not findings:
            findings = "Findings not clearly identified."
        if not investigation:
            investigation = "Investigation steps not clearly identified."

        return AnalysisResult(
            test_name=test_result.test_name,
            table_name=test_result.table_name,
            findings=findings,
            suggested_investigation=investigation
        )
