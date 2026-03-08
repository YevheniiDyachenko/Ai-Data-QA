# Architecture Overview

This document describes the architecture of **AI Data QA for BigQuery**.

The system provides automated data quality validation, guarded SQL execution, and AI-assisted failure investigation for BigQuery datasets.

---

## High-Level Architecture

The system consists of seven layers:

1. BigQuery Integration
2. Data Profiling
3. Test Generation
4. SQL Safety Validation
5. Test Execution
6. AI Analysis
7. Reporting + API/UI Delivery

```text
BigQuery
   │
   ▼
Schema Scanner
   │
   ▼
Profiling Engine
   │
   ▼
Test Generator (static + AI)
   │
   ▼
SQL Safety Validator
   │
   ▼
Test Runner
   │
   ▼
Results + Analysis
   │
   ▼
CLI / API / Dashboard
```

Each layer is modular and replaceable.

---

## Core Components

### 1) BigQuery Integration Layer (`ai_data_qa/bigquery/client.py`)

Responsibilities:

- connect to BigQuery
- execute SQL queries
- retrieve query results
- provide schema access helpers

---

### 2) Schema Scanner (`ai_data_qa/bigquery/schema_loader.py`)

Loads metadata for all dataset tables and normalizes it into typed schema models.

---

### 3) Profiling Engine (`ai_data_qa/bigquery/profiler.py`)

Computes baseline metrics per table/column:

- `row_count`
- `null_count`
- `distinct_count`

These stats enrich AI test generation and reporting.

---

### 4) Test Generation Engine (`ai_data_qa/tests_engine/generator.py`)

Generates tests from:

- static templates (e.g., not-null, uniqueness, freshness)
- optional AI-generated tests

#### AI contract hardening

AI output is required to match a strict JSON schema (`tests` array with `sql`, optional metadata). Invalid AI responses are safely ignored with fallback logging.

---

### 5) SQL Safety Validator (`ai_data_qa/tests_engine/sql_validator.py`)

Every query is validated before execution:

- **SELECT-only**
- block dangerous keywords (`DROP`, `DELETE`, `UPDATE`, etc.)
- enforce or inject bounded `LIMIT`

This layer is the main runtime safety guard.

---

### 6) Test Runner (`ai_data_qa/tests_engine/runner.py`)

Executes validated tests, captures duration/failure counts, and emits structured results.

Supports selective execution by tags:

- `freshness`
- `nulls`
- `distribution`

Errors are normalized into taxonomy fields (`category`, `code`, `message`).

---

### 7) Error Taxonomy + Structured Logging (`ai_data_qa/errors.py`, `ai_data_qa/utils/logger.py`)

A single app-level error model (`AppError`) is used across pipeline and API.

Logs are emitted as JSON events for machine-readable observability.

---

### 8) API + Reporting (`ai_data_qa/api/server.py`)

FastAPI exposes CLI workflows and returns consistent operation payloads:

- `status`, `message`, `action`, `dataset`, `error`

Report metadata stores `last_operation` with structured error details when failures occur.

---

## Data Contracts

### Cache/result envelopes

- `schema_cache.json` => `{ "schemas": [...] }`
- `tests_cache.json` => `{ "tests": [...] }`
- `test_results.json` => `{ "results": [...] }`
- `analysis_cache.json` => `{ "analyses": [...] }`

### API action response

```json
{
  "status": "completed | error",
  "message": "...",
  "action": "scan | generate-tests | run-tests | analyze | report",
  "dataset": "analytics",
  "error": null
}
```

---

## Operational Flow

1. `scan` -> schema (+ optional profiling)
2. `generate-tests` -> static (+ optional AI) tests
3. `run-tests` -> SQL safety validation + execution (+ optional tag filter)
4. `analyze` -> AI analysis for failed tests
5. `report` -> markdown/json summaries for API/dashboard

