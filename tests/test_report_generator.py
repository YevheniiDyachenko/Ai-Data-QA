from ai_data_qa.reports.report_generator import ReportGenerator
from ai_data_qa.tests_engine.models import TestResult


def test_report_includes_quality_dimensions(tmp_path):
    reporter = ReportGenerator(output_dir=str(tmp_path))
    results = [
        TestResult(table_name="users", test_name="t1", sql="SELECT 1", failed_rows=0, execution_time=0.1, status="PASSED", quality_dimension="completeness"),
        TestResult(table_name="users", test_name="t2", sql="SELECT 1", failed_rows=2, execution_time=0.2, status="FAILED", quality_dimension="validity"),
    ]

    path = reporter.generate_markdown_report("analytics", results)
    content = open(path).read()

    assert "## Quality Dimensions" in content
    assert "Completeness" in content
    assert "Validity" in content
