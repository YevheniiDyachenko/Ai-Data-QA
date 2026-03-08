AI Data QA for BigQuery

Objective

Create an open-source tool that automatically evaluates data quality in Google BigQuery datasets.

The tool should:

- connect to BigQuery
- scan dataset schema
- generate SQL-based data quality tests using AI
- run tests
- analyze results
- produce a data quality report

The system must be lightweight and suitable for a single engineer project.

No UI is required. Interaction must happen via CLI.

---

Core Principles

1. Keep the architecture simple
2. SQL-based deterministic testing
3. AI used only for generation and analysis
4. Modular architecture
5. Easy configuration
6. Minimal dependencies
7. Clear logs and reports

---

Target Users

- Data Engineers
- Analytics Engineers
- Data QA Engineers

Typical use case:

A user runs a command to scan a BigQuery dataset and automatically generate quality checks.

---

Technology Stack

Language:

- Python 3.11+

Libraries:

- google-cloud-bigquery
- typer (CLI)
- pydantic
- pyyaml
- rich (CLI output)
- openai or anthropic API client

Optional:

- pandas (profiling analysis)

---

Repository Structure

ai-data-qa/
│
├── README.md
├── pyproject.toml
├── config.yaml
│
├── ai_data_qa/
│   │
│   ├── cli.py
│   ├── config.py
│   │
│   ├── bigquery/
│   │   ├── client.py
│   │   ├── schema_loader.py
│   │   └── profiler.py
│   │
│   ├── tests_engine/
│   │   ├── generator.py
│   │   ├── runner.py
│   │   └── models.py
│   │
│   ├── ai/
│   │   ├── prompts.py
│   │   ├── client.py
│   │   └── analyzer.py
│   │
│   ├── reports/
│   │   └── report_generator.py
│   │
│   └── utils/
│       └── logger.py
│
└── tests/

---

Configuration File

config.yaml

Example:

project_id: my_project
dataset: analytics

ai:
  provider: anthropic
  model: claude-3-sonnet

tests:
  default_checks:
    - not_null
    - uniqueness
    - regex
    - range

report:
  output_dir: reports

---

CLI Commands

The CLI must be implemented with Typer.

Commands:

ai-data-qa scan
ai-data-qa generate-tests
ai-data-qa run-tests
ai-data-qa analyze
ai-data-qa report

scan

Reads dataset schema from BigQuery.

Output:

- list of tables
- columns
- types

generate-tests

Uses AI to generate SQL quality tests for each table.

Output files:

tests/
   users.sql
   orders.sql

run-tests

Executes SQL queries in BigQuery and stores results.

Output file:

test_results.json

analyze

Uses AI to analyze failures and suggest possible root causes.

report

Generates a Markdown report summarizing data quality.

---

BigQuery Integration

Use google-cloud-bigquery client.

Example query to load schema:

SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM
  `project.dataset.INFORMATION_SCHEMA.COLUMNS`

The tool should convert this into internal Python models.

---

Data Profiling Module

Basic statistics per column:

- row_count
- null_count
- distinct_count
- min
- max

Example query template:

SELECT
COUNT(*) as row_count,
COUNTIF(column IS NULL) as null_count,
COUNT(DISTINCT column) as distinct_count
FROM table

Results stored in memory.

---

Test Generation

Tests must be SQL queries.

Examples:

Not Null

SELECT COUNT(*)
FROM table
WHERE column IS NULL

Uniqueness

SELECT column, COUNT(*)
FROM table
GROUP BY column
HAVING COUNT(*) > 1

Regex

SELECT column
FROM table
WHERE NOT REGEXP_CONTAINS(column, pattern)

Range

SELECT column
FROM table
WHERE column < min OR column > max

AI should generate tests based on:

- column type
- column name
- profiling statistics

---

AI Prompt Design

AI must receive:

- table schema
- column types
- profiling statistics

Prompt example:

You are a data quality engineer.

Given the following table schema:

Table: users

Columns:
user_id INT
email STRING
created_at TIMESTAMP

Generate SQL data quality tests for BigQuery.

Focus on:

- null values
- duplicates
- format validation
- timestamp sanity checks

Return only SQL queries.

---

Test Runner

The runner must:

1. load SQL test files
2. execute queries in BigQuery
3. capture results
4. store results

Result format:

{
  "table": "users",
  "test": "duplicate_user_id",
  "failed_rows": 153
}

---

AI Analysis

If tests fail, AI analyzes possible causes.

Input to AI:

- failed tests
- profiling stats

Expected output:

Possible issue detected.

Duplicate user_id values increased significantly.

Likely causes:
- ingestion retry
- duplicate API events
- upstream pipeline bug

---

Reporting

Generate Markdown report.

Example output:

# Data Quality Report

Dataset: analytics

## Table: users

Tests executed: 5
Passed: 3
Failed: 2

Failed Tests:

duplicate_user_id
null_email

## AI Analysis

Duplicates appear to originate from source_system = legacy_api.

Save to:

reports/data_quality_report.md

---

Logging

Use structured logging.

Log levels:

- INFO
- WARNING
- ERROR

Logs must include:

- executed SQL
- execution time
- failures

---

Error Handling

Handle:

- BigQuery authentication issues
- missing datasets
- invalid SQL
- AI API failures

The tool must fail gracefully.

---

Testing

Include unit tests for:

- schema loader
- SQL generation
- runner logic

Use pytest.

---

Documentation

README.md must include:

- installation instructions
- authentication setup for BigQuery
- CLI examples
- configuration guide

---

Example Workflow

ai-data-qa scan
ai-data-qa generate-tests
ai-data-qa run-tests
ai-data-qa analyze
ai-data-qa report

---

Future Improvements (Do Not Implement Now)

- web dashboard
- scheduling
- Slack alerts
- anomaly detection models
- historical trend tracking

Keep the first version minimal.
