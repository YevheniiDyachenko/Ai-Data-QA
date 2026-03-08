import os
from typing import List, Dict
from ai_data_qa.tests_engine.models import TestResult, AnalysisResult
from ai_data_qa.utils.logger import logger

class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_markdown_report(self, dataset_id: str, results: List[TestResult], analyses: List[AnalysisResult] = None) -> str:
        """Generates a Markdown report from test results and AI analyses."""
        report = f"# Data Quality Report\n\n"
        report += f"**Dataset:** {dataset_id}\n\n"

        # Summary
        total = len(results)
        passed = len([r for r in results if r.status == "PASSED"])
        failed = len([r for r in results if r.status == "FAILED"])
        errors = len([r for r in results if r.status == "ERROR"])

        report += "## Summary\n\n"
        report += f"- **Total Tests:** {total}\n"
        report += f"- **Passed:** {passed}\n"
        report += f"- **Failed:** {failed}\n"
        if errors > 0:
            report += f"- **Errors:** {errors}\n"
        report += "\n"

        # Results by table
        tables = sorted(list(set(r.table_name for r in results)))
        for table in tables:
            report += f"### Table: {table}\n\n"
            table_results = [r for r in results if r.table_name == table]

            report += "| Test Name | Status | Failed Rows | Execution Time |\n"
            report += "| --- | --- | --- | --- |\n"
            for r in table_results:
                report += f"| {r.test_name} | {r.status} | {r.failed_rows} | {r.execution_time:.2f}s |\n"
            report += "\n"

            # AI Analysis for this table
            if analyses:
                table_analyses = [a for a in analyses if a.table_name == table]
                if table_analyses:
                    report += "#### AI Analysis\n\n"
                    for a in table_analyses:
                        report += f"**Test:** {a.test_name}\n\n"
                        report += f"**Findings:**\n{a.findings}\n\n"
                        report += f"**Suggested Investigation:**\n{a.suggested_investigation}\n\n"
                        report += "---\n\n"

        file_path = os.path.join(self.output_dir, "data_quality_report.md")
        with open(file_path, "w") as f:
            f.write(report)

        logger.info(f"Generated Markdown report: {file_path}")
        return file_path
