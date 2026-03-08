import typer
import json
import os
from typing import Optional
from rich.console import Console
from rich.table import Table

from ai_data_qa.config import load_config
from ai_data_qa.bigquery.client import BQClient
from ai_data_qa.bigquery.schema_loader import SchemaLoader
from ai_data_qa.bigquery.profiler import Profiler
from ai_data_qa.tests_engine.generator import TestGenerator
from ai_data_qa.tests_engine.runner import TestRunner
from ai_data_qa.tests_engine.models import TestCase
from ai_data_qa.ai.client import get_ai_client
from ai_data_qa.ai.analyzer import AIAnalyzer
from ai_data_qa.reports.report_generator import ReportGenerator
from ai_data_qa.utils.logger import logger

app = typer.Typer(help="AI-powered Data Quality tool for BigQuery")
console = Console()

@app.command()
def scan(config_path: str = "config.yaml", profile: bool = True):
    """Reads dataset schema from BigQuery and optionally profiles tables."""
    config = load_config(config_path)
    bq_client = BQClient(config.project_id, config.location)
    loader = SchemaLoader(bq_client)
    profiler = Profiler(bq_client)

    with console.status("[bold green]Scanning dataset schema..."):
        schemas = loader.load_dataset_schema(config.project_id, config.dataset)

    if profile:
        with console.status("[bold green]Profiling tables..."):
            for schema in schemas:
                logger.info(f"Profiling table: {schema.table_name}")
                schema.profiling_results = profiler.profile_table(config.project_id, config.dataset, schema)

    table = Table(title=f"Schema for {config.dataset}")
    table.add_column("Table", style="cyan")
    table.add_column("Columns", style="magenta")
    table.add_column("Profiled", style="green")

    for schema in schemas:
        profiled_status = "Yes" if schema.profiling_results else "No"
        table.add_row(schema.table_name, ", ".join([c.name for c in schema.columns]), profiled_status)

    console.print(table)

    # Save schema for later use
    with open("schema_cache.json", "w") as f:
        json.dump([s.model_dump() for s in schemas], f, indent=2)

@app.command()
def generate_tests(config_path: str = "config.yaml", use_ai: bool = False):
    """Generates SQL quality tests for each table."""
    config = load_config(config_path)

    ai_client = None
    if use_ai:
        ai_client = get_ai_client(config.ai.provider, config.ai.model, config.ai.api_key_env_var)

    generator = TestGenerator(config.tests.output_dir, ai_client=ai_client)

    if not os.path.exists("schema_cache.json"):
        console.print("[red]Schema cache not found. Please run 'scan' first.[/red]")
        raise typer.Exit(1)

    with open("schema_cache.json", "r") as f:
        schema_data = json.load(f)

    from ai_data_qa.tests_engine.models import TableSchema
    schemas = [TableSchema(**s) for s in schema_data]

    all_tests = []
    for schema in schemas:
        tests = generator.generate_static_tests(config.project_id, config.dataset, schema)
        if use_ai:
            with console.status(f"[bold green]Generating AI tests for {schema.table_name}..."):
                ai_tests = generator.generate_ai_tests(schema)
                tests.extend(ai_tests)

        generator.save_tests(schema.table_name, tests)
        all_tests.extend(tests)

    console.print(f"[bold green]Generated {len(all_tests)} tests for {len(schemas)} tables.[/bold green]")

    # Save tests for runner
    with open("tests_cache.json", "w") as f:
        json.dump([t.model_dump() for t in all_tests], f, indent=2)

@app.command()
def run_tests(config_path: str = "config.yaml"):
    """Executes SQL queries in BigQuery and stores results."""
    config = load_config(config_path)
    bq_client = BQClient(config.project_id, config.location)
    runner = TestRunner(bq_client)

    if not os.path.exists("tests_cache.json"):
        console.print("[red]Tests cache not found. Please run 'generate-tests' first.[/red]")
        raise typer.Exit(1)

    with open("tests_cache.json", "r") as f:
        test_data = json.load(f)

    tests = [TestCase(**t) for t in test_data]

    with console.status("[bold green]Running tests..."):
        results = runner.run_tests(tests)
        runner.save_results(results)

    table = Table(title="Test Results")
    table.add_column("Table", style="cyan")
    table.add_column("Test", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Failed Rows", justify="right")

    for r in results:
        status_style = "green" if r.status == "PASSED" else "red"
        table.add_row(r.table_name, r.test_name, f"[{status_style}]{r.status}[/{status_style}]", str(r.failed_rows))

    console.print(table)

@app.command()
def analyze(config_path: str = "config.yaml"):
    """Uses AI to analyze failures and suggest root causes."""
    config = load_config(config_path)
    ai_client = get_ai_client(config.ai.provider, config.ai.model, config.ai.api_key_env_var)
    analyzer = AIAnalyzer(ai_client)

    if not os.path.exists("test_results.json"):
        console.print("[red]Test results not found. Please run 'run-tests' first.[/red]")
        raise typer.Exit(1)

    with open("test_results.json", "r") as f:
        results_data = json.load(f)

    from ai_data_qa.tests_engine.models import TestResult, TableSchema
    results = [TestResult(**r) for r in results_data]
    failed_results = [r for r in results if r.status == "FAILED"]

    if not failed_results:
        console.print("[bold green]No failed tests to analyze![/bold green]")
        return

    if not os.path.exists("schema_cache.json"):
        console.print("[red]Schema cache not found. Please run 'scan' first.[/red]")
        raise typer.Exit(1)

    with open("schema_cache.json", "r") as f:
        schema_data = json.load(f)
    schemas = {s["table_name"]: TableSchema(**s) for s in schema_data}

    analyses = []
    with console.status("[bold green]Analyzing failures with AI..."):
        for r in failed_results:
            schema = schemas.get(r.table_name)
            if schema:
                analysis = analyzer.analyze_failure(r, schema)
                analyses.append(analysis)
                console.print(f"[bold yellow]Analysis for {r.test_name}:[/bold yellow]")
                console.print(analysis.findings)
                console.print("-" * 20)

    # Save analyses for report
    with open("analysis_cache.json", "w") as f:
        json.dump([a.model_dump() for a in analyses], f, indent=2)

@app.command()
def report(config_path: str = "config.yaml"):
    """Generates a Markdown report summarizing data quality."""
    config = load_config(config_path)
    reporter = ReportGenerator(config.report.output_dir)

    if not os.path.exists("test_results.json"):
        console.print("[red]Test results not found. Please run 'run-tests' first.[/red]")
        raise typer.Exit(1)

    with open("test_results.json", "r") as f:
        results_data = json.load(f)

    from ai_data_qa.tests_engine.models import TestResult, AnalysisResult
    results = [TestResult(**r) for r in results_data]

    analyses = None
    if os.path.exists("analysis_cache.json"):
        with open("analysis_cache.json", "r") as f:
            analysis_data = json.load(f)
        analyses = [AnalysisResult(**a) for a in analysis_data]

    report_path = reporter.generate_markdown_report(config.dataset, results, analyses)
    console.print(f"[bold green]Report generated at: {report_path}[/bold green]")

if __name__ == "__main__":
    app()
