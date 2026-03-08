Architecture Overview

This document describes the architecture of the AI Data QA for BigQuery system.

The goal of the project is to provide a lightweight tool for automated data quality validation and AI-assisted investigation of data issues in BigQuery datasets.

The architecture is intentionally simple so that the system can be maintained by a single engineer.

---

High-Level Architecture

The system consists of five core layers:

1. BigQuery Integration
2. Data Profiling
3. Test Generation
4. Test Execution
5. AI Analysis and Reporting

Data Warehouse (BigQuery)
        │
        ▼
Schema Scanner
        │
        ▼
Profiling Engine
        │
        ▼
Test Generator
        │
        ▼
Test Runner
        │
        ▼
Results Storage
        │
        ▼
AI Analysis
        │
        ▼
Reports / CLI / UI

Each layer is independent and modular.

---

Core System Components

1. BigQuery Integration Layer

Responsible for interacting with BigQuery.

Main responsibilities:

- connect to BigQuery
- load dataset metadata
- execute SQL queries
- retrieve query results

Main module:

bigquery/
    client.py

Key functionality:

- schema discovery
- query execution
- error handling

Example query used for schema discovery:

SELECT
  table_name,
  column_name,
  data_type,
  is_nullable
FROM
  `project.dataset.INFORMATION_SCHEMA.COLUMNS`

---

2. Schema Scanner

The schema scanner loads metadata for all tables in a dataset.

Output example:

users
  user_id INT
  email STRING
  created_at TIMESTAMP

orders
  order_id INT
  user_id INT
  amount FLOAT

The schema scanner produces structured models used by the rest of the system.

Schema models should include:

- table_name
- column_name
- column_type
- nullable

---

3. Data Profiling Engine

The profiling engine computes basic statistics for tables and columns.

Profiling metrics include:

- row_count
- null_count
- distinct_count
- min_value
- max_value

Example SQL:

SELECT
  COUNT(*) as row_count,
  COUNTIF(column IS NULL) as null_count,
  COUNT(DISTINCT column) as distinct_count
FROM table

Profiling results are used by the AI test generator.

---

4. Test Generation Engine

The test generation engine produces SQL-based data quality tests.

Tests are generated using two sources:

1. predefined templates
2. AI-generated tests

Example templates:

- not_null
- uniqueness
- regex_validation
- numeric_range
- timestamp_validation

Example generated test:

SELECT COUNT(*)
FROM users
WHERE email IS NULL

Generated tests are saved to files:

tests/
  users.sql
  orders.sql

Each file contains multiple SQL queries.

---

5. Test Runner

The test runner executes SQL tests against BigQuery.

Responsibilities:

- load SQL tests
- execute queries
- capture results
- detect failures

Example result format:

{
  "table": "users",
  "test": "duplicate_user_id",
  "failed_rows": 153
}

Results are stored in memory or JSON files.

---

6. AI Analysis Layer

The AI module analyzes failed tests and attempts to identify potential causes.

AI inputs:

- failed test results
- profiling statistics
- table schema

AI outputs:

- explanation of the issue
- possible root cause
- suggested investigation queries

Example output:

Duplicate user_id values detected.

Most duplicates originate from source_system = legacy_api.

Possible cause:
event ingestion retry producing duplicate records.

The AI module does not execute database queries directly.

Instead, it generates investigation SQL that the system can execute.

---

7. Reporting Layer

The reporting module generates human-readable summaries.

Supported formats:

- Markdown
- CLI output

Example report:

Data Quality Report

Dataset: analytics

Table: users

Tests executed: 6
Passed: 4
Failed: 2

Failed tests:

duplicate_user_id
null_email

AI analysis:

Duplicates originate from legacy_api ingestion.

Reports are stored in:

reports/

---

CLI Architecture

The CLI is the primary interface for the system.

Commands:

ai-data-qa scan
ai-data-qa generate-tests
ai-data-qa run-tests
ai-data-qa analyze
ai-data-qa report

Each command calls a specific module.

Example flow:

scan
→ schema_loader

generate-tests
→ test_generator

run-tests
→ test_runner

analyze
→ ai_analyzer

---

Data Flow

The full workflow is:

1 load dataset schema
2 profile tables
3 generate tests
4 run tests
5 collect failures
6 run AI analysis
7 generate report

---

Design Principles

The system follows several important principles.

SQL-first approach

All validations must ultimately compile to SQL queries executed in BigQuery.

This ensures scalability and transparency.

---

Deterministic testing

Test execution must always be deterministic.

AI is used only for:

- test generation
- investigation
- analysis

AI must never decide whether a test passes or fails.

---

Modular design

Each module should be independent and replaceable.

Example:

AI provider can be replaced without modifying the rest of the system.

---

Minimal dependencies

The project should avoid heavy frameworks.

Preferred libraries:

- google-cloud-bigquery
- typer
- pydantic
- pyyaml
- rich

---

Future Architecture Extensions

Possible future improvements include:

- scheduling
- historical quality trends
- anomaly detection
- Slack alerts
- web dashboard

These features should not be implemented in the first version.

The first version should focus on simplicity and reliability.
