import json
import os
from pathlib import Path
from typing import List, Dict, Optional
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

        tables = sorted(list(set(r.table_name for r in results)))
        for table in tables:
            report += f"### Table: {table}\n\n"
            table_results = [r for r in results if r.table_name == table]

            report += "| Test Name | Status | Failed Rows | Execution Time |\n"
            report += "| --- | --- | --- | --- |\n"
            for r in table_results:
                report += f"| {r.test_name} | {r.status} | {r.failed_rows} | {r.execution_time:.2f}s |\n"
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

    def write_manifest(
        self,
        *,
        run_id: str,
        dataset_id: str,
        started_at: Optional[str],
        finished_at: Optional[str],
        status: str,
        artifact_paths: Dict[str, Optional[str]],
    ) -> str:
        run_dir = Path(self.output_dir) / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = run_dir / "manifest.json"
        existing_payload = {}
        if manifest_path.exists():
            try:
                existing_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing_payload = {}

        normalized_artifacts = {
            key: value
            for key, value in artifact_paths.items()
            if value
        }

        payload = {
            "run_id": run_id,
            "started_at": started_at or existing_payload.get("started_at"),
            "finished_at": finished_at or existing_payload.get("finished_at"),
            "dataset": dataset_id,
            "status": status,
            "artifact_paths": {
                **existing_payload.get("artifact_paths", {}),
                **normalized_artifacts,
            },
        }

        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info(f"Generated run manifest: {manifest_path}")
        return str(manifest_path)
