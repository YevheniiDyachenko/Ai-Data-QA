import typer
import json
import os
import tempfile
from typing import Optional, List
from rich.console import Console
from rich.table import Table
import yaml

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
from ai_data_qa.utils.logger import log_event
from ai_data_qa.scheduler import SchedulerJob, SchedulerStore

app = typer.Typer(help="AI-powered Data Quality tool for BigQuery")
schedule_app = typer.Typer(help="Manage scheduler jobs")
app.add_typer(schedule_app, name="schedule")
console = Console()



def _config_for_dataset(config_path: str, dataset: str) -> str:
    config = load_config(config_path)
    config.dataset = dataset
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
        yaml.safe_dump(config.model_dump(), tmp_file, sort_keys=False)
        return tmp_file.name

def _split_tags(tags: Optional[str]) -> Optional[List[str]]:
    if not tags:
        return None
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


@app.command()
def scan(
    config_path: str = "config.yaml",
    profile: bool = typer.Option(True, "--profile/--no-profile"),
):
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
                log_event("profiling_table", table_name=schema.table_name)
                schema.profiling_results = profiler.profile_table(config.project_id, config.dataset, schema)

    table = Table(title=f"Schema for {config.dataset}")
    table.add_column("Table", style="cyan")
    table.add_column("Columns", style="magenta")
    table.add_column("Profiled", style="green")

    for schema in schemas:
        profiled_status = "Yes" if schema.profiling_results else "No"
        table.add_row(schema.table_name, ", ".join([c.name for c in schema.columns]), profiled_status)

    console.print(table)

    with open("schema_cache.json", "w") as f:
        json.dump({"schemas": [s.model_dump() for s in schemas]}, f, indent=2)


@app.command()
def generate_tests(
    config_path: str = "config.yaml",
    use_ai: bool = typer.Option(False, "--use-ai/--no-use-ai"),
):
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
    raw_schemas = schema_data["schemas"] if isinstance(schema_data, dict) else schema_data
    schemas = [TableSchema(**s) for s in raw_schemas]

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

    with open("tests_cache.json", "w") as f:
        json.dump({"tests": [t.model_dump() for t in all_tests]}, f, indent=2)


@app.command()
def run_tests(config_path: str = "config.yaml", tags: Optional[str] = typer.Option(None, help="Comma-separated test tags")):
    """Executes SQL queries in BigQuery and stores results."""
    config = load_config(config_path)
    bq_client = BQClient(config.project_id, config.location)
    runner = TestRunner(bq_client)

    if not os.path.exists("tests_cache.json"):
        console.print("[red]Tests cache not found. Please run 'generate-tests' first.[/red]")
        raise typer.Exit(1)

    with open("tests_cache.json", "r") as f:
        test_data = json.load(f)

    raw_tests = test_data["tests"] if isinstance(test_data, dict) else test_data
    tests = [TestCase(**t) for t in raw_tests]

    with console.status("[bold green]Running tests..."):
        results = runner.run_tests(tests, include_tags=_split_tags(tags))
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
        results_payload = json.load(f)

    from ai_data_qa.tests_engine.models import TestResult, TableSchema
    raw_results = results_payload["results"] if isinstance(results_payload, dict) else results_payload
    results = [TestResult(**r) for r in raw_results]
    failed_results = [r for r in results if r.status == "FAILED"]

    if not failed_results:
        console.print("[bold green]No failed tests to analyze![/bold green]")
        return

    if not os.path.exists("schema_cache.json"):
        console.print("[red]Schema cache not found. Please run 'scan' first.[/red]")
        raise typer.Exit(1)

    with open("schema_cache.json", "r") as f:
        schema_data = json.load(f)
    raw_schemas = schema_data["schemas"] if isinstance(schema_data, dict) else schema_data
    schemas = {s["table_name"]: TableSchema(**s) for s in raw_schemas}

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

    with open("analysis_cache.json", "w") as f:
        json.dump({"analyses": [a.model_dump() for a in analyses]}, f, indent=2)


@app.command()
def report(config_path: str = "config.yaml"):
    """Generates a Markdown report summarizing data quality."""
    config = load_config(config_path)
    reporter = ReportGenerator(config.report.output_dir)

    if not os.path.exists("test_results.json"):
        console.print("[red]Test results not found. Please run 'run-tests' first.[/red]")
        raise typer.Exit(1)

    with open("test_results.json", "r") as f:
        results_payload = json.load(f)

    from ai_data_qa.tests_engine.models import TestResult, AnalysisResult
    raw_results = results_payload["results"] if isinstance(results_payload, dict) else results_payload
    results = [TestResult(**r) for r in raw_results]

    analyses = None
    if os.path.exists("analysis_cache.json"):
        with open("analysis_cache.json", "r") as f:
            analysis_payload = json.load(f)
        raw_analyses = analysis_payload["analyses"] if isinstance(analysis_payload, dict) else analysis_payload
        analyses = [AnalysisResult(**a) for a in raw_analyses]

    report_path = reporter.generate_markdown_report(config.dataset, results, analyses)
    console.print(f"[bold green]Report generated at: {report_path}[/bold green]")


@schedule_app.command("list")
def schedule_list(store_path: str = "reports/scheduler_jobs.json"):
    """Lists configured scheduler jobs."""
    store = SchedulerStore(store_path)
    jobs = store.list_jobs()

    table = Table(title="Scheduler Jobs")
    table.add_column("ID", style="cyan")
    table.add_column("Dataset", style="magenta")
    table.add_column("Schedule", style="green")
    table.add_column("Enabled")
    table.add_column("Retry")
    table.add_column("Backoff(s)")

    for job in jobs:
        schedule = f"cron: {job.cron}" if job.cron else f"interval: {job.interval_seconds}s"
        table.add_row(job.id, job.dataset, schedule, str(job.enabled), str(job.retry_count), str(job.backoff_seconds))

    console.print(table)


@schedule_app.command("add")
def schedule_add(
    dataset: str,
    cron: Optional[str] = typer.Option(None, help="Cron expression"),
    interval: Optional[int] = typer.Option(None, help="Interval in seconds"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable job"),
    retry_count: int = typer.Option(3, help="Retry attempts for transient errors"),
    backoff: float = typer.Option(2.0, help="Backoff in seconds"),
    store_path: str = "reports/scheduler_jobs.json",
):
    """Adds a scheduler job."""
    job = SchedulerJob(
        dataset=dataset,
        cron=cron,
        interval_seconds=interval,
        enabled=enabled,
        retry_count=retry_count,
        backoff_seconds=backoff,
    )
    store = SchedulerStore(store_path)
    created = store.create_job(job)
    console.print(f"[bold green]Added scheduler job {created.id}[/bold green]")


@schedule_app.command("remove")
def schedule_remove(job_id: str, store_path: str = "reports/scheduler_jobs.json"):
    """Removes a scheduler job by id."""
    store = SchedulerStore(store_path)
    store.delete_job(job_id)
    console.print(f"[bold green]Removed scheduler job {job_id}[/bold green]")


@schedule_app.command("run-now")
def schedule_run_now(job_id: str, config_path: str = "config.yaml", store_path: str = "reports/scheduler_jobs.json"):
    """Runs scheduler job execution pipeline immediately."""
    store = SchedulerStore(store_path)
    job = store.get_job(job_id)
    if not job.enabled:
        console.print(f"[yellow]Scheduler job {job_id} is disabled.[/yellow]")
        raise typer.Exit(1)

    temp_config_path = _config_for_dataset(config_path, job.dataset)
    try:
        scan(config_path=temp_config_path, profile=True)
        generate_tests(config_path=temp_config_path, use_ai=False)

        config = load_config(temp_config_path)
        bq_client = BQClient(config.project_id, config.location)
        runner = TestRunner(bq_client, retry_count=job.retry_count, backoff_seconds=job.backoff_seconds)

        if not os.path.exists("tests_cache.json"):
            console.print("[red]Tests cache not found. Please run 'generate-tests' first.[/red]")
            raise typer.Exit(1)

        with open("tests_cache.json", "r") as f:
            test_data = json.load(f)

        raw_tests = test_data["tests"] if isinstance(test_data, dict) else test_data
        tests = [TestCase(**t) for t in raw_tests]
        results = runner.run_tests(tests)
        runner.save_results(results)
        store.mark_run(job_id)
        console.print(f"[bold green]Executed scheduler job {job_id}[/bold green]")
    finally:
        os.unlink(temp_config_path)


if __name__ == "__main__":
    app()
