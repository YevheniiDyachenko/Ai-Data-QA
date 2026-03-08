# AI Data QA for BigQuery

AI Data QA is a lightweight, AI-powered tool for automated data quality validation in Google BigQuery. It helps data engineers scan schemas, profile tables, generate tests, and analyze failures using Large Language Models.

## Features

- **Schema Discovery:** Automatically scans BigQuery datasets to understand table structures.
- **Data Profiling:** Computes row counts, null counts, and distinct counts for table columns.
- **Automated Testing:** Generates SQL-based data quality tests including:
  - Not Null checks
  - Uniqueness checks
  - Regex-based format validation
  - Numeric range checks
  - Timestamp sanity checks
- **AI-Powered Analysis:** Uses LLMs (OpenAI/Anthropic) to analyze test failures and suggest root causes.
- **Markdown Reporting:** Generates comprehensive reports of data quality status.

## Quick Start

```bash
# Install the package in editable mode
pip install -e .

# Scan the dataset schema and profile tables
ai-data-qa scan

# Generate SQL data quality tests
ai-data-qa generate-tests

# Run the generated tests in BigQuery
ai-data-qa run-tests

# Analyze failures with AI
ai-data-qa analyze

# Generate a Markdown report
ai-data-qa report
```

## Installation

```bash
git clone https://github.com/your-repo/ai-data-qa.git
cd ai-data-qa
pip install .
```

## BigQuery Authentication

The tool uses the official Google Cloud BigQuery client. To authenticate:

1. Create a Service Account in the Google Cloud Console.
2. Download the JSON key file.
3. Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
```

## Configuration

Create a `config.yaml` file in the project root:

```yaml
project_id: "example_project"
dataset: "analytics"
location: "US"

ai:
  provider: "openai"  # or "anthropic"
  model: "gpt-4o-mini"
  api_key_env_var: "OPENAI_API_KEY"

tests:
  output_dir: "tests_generated"
  default_checks:
    - "not_null"
    - "uniqueness"
    - "regex"
    - "range"

report:
  output_dir: "reports"
```

## Example Report Output

The generated Markdown report (`reports/data_quality_report.md`) looks like this:

# Data Quality Report

**Dataset:** analytics

## Summary

- **Total Tests:** 12
- **Passed:** 10
- **Failed:** 2

### Table: users

| Test Name | Status | Failed Rows | Execution Time |
| --- | --- | --- | --- |
| users_user_id_unique | FAILED | 153 | 1.45s |
| users_email_not_null | PASSED | 0 | 1.12s |

#### AI Analysis

**Test:** users_user_id_unique

**Findings:**
Duplicates appear to originate from legacy_api ingestion.

**Suggested Investigation:**
SELECT user_id, count(*) FROM users GROUP BY 1 HAVING count(*) > 1;
```
