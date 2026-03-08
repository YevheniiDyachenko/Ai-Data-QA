import os
from typing import List, Dict
from ai_data_qa.tests_engine.models import TestResult, AnalysisResult
from ai_data_qa.utils.logger import logger


class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _dimension_summary(self, results: List[TestResult]) -> Dict[str, Dict[str, int]]:
        dimensions = ["completeness", "validity", "freshness", "consistency"]
        summary = {d: {"total": 0, "passed": 0, "failed": 0, "errors": 0} for d in dimensions}
        for result in results:
            dimension = result.quality_dimension
            if dimension not in summary:
                continue
            summary[dimension]["total"] += 1
            if result.status == "PASSED":
                summary[dimension]["passed"] += 1
            elif result.status == "FAILED":
                summary[dimension]["failed"] += 1
            elif result.status == "ERROR":
                summary[dimension]["errors"] += 1
        return summary

    def generate_markdown_report(self, dataset_id: str, results: List[TestResult], analyses: List[AnalysisResult] = None) -> str:
        """Generates a Markdown report from test results and AI analyses."""
        report = f"# Data Quality Report\n\n"
        report += f"**Dataset:** {dataset_id}\n\n"

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

        report += "## Quality Dimensions\n\n"
        report += "| Dimension | Total | Passed | Failed | Errors |\n"
        report += "| --- | --- | --- | --- | --- |\n"
        for dimension, stats in self._dimension_summary(results).items():
            report += (
                f"| {dimension.title()} | {stats['total']} | {stats['passed']} "
                f"| {stats['failed']} | {stats['errors']} |\n"
            )
        report += "\n"

        tables = sorted(list(set(r.table_name for r in results)))
        for table in tables:
            report += f"### Table: {table}\n\n"
            table_results = [r for r in results if r.table_name == table]

            report += "| Test Name | Dimension | Status | Metric | Failed Rows | Execution Time |\n"
            report += "| --- | --- | --- | --- | --- | --- |\n"
            for r in table_results:
                metric_view = (
                    f"{r.evaluated_metric or 'failed_rows'} {r.threshold_operator or '=='} {r.threshold_value} "
                    f"(actual: {r.metric_value if r.metric_value is not None else r.failed_rows})"
                )
                report += (
                    f"| {r.test_name} | {r.quality_dimension or '-'} | {r.status} | {metric_view} "
                    f"| {r.failed_rows} | {r.execution_time:.2f}s |\n"
                )
            report += "\n"

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
