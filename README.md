# AI Data QA for BigQuery

AI Data QA is a lightweight, AI-powered tool for automated data quality validation in Google BigQuery. It supports a CLI workflow and a web dashboard control panel backed by FastAPI.

## Features

- **Schema Discovery:** scan BigQuery datasets and table schemas.
- **Data Profiling:** collect row counts, null counts, and distinct counts.
- **Automated Testing:** generate and run SQL quality tests.
- **SQL Safety Validator:** enforce `SELECT`-only execution, block dangerous keywords, and cap query `LIMIT` before test execution.
- **Test Tagging + Selective Run:** classify tests with tags (`freshness`, `nulls`, `distribution`) and run filtered subsets from CLI.
- **Error Taxonomy + Structured Logging:** unified app errors (`category` + `code`) and JSON-formatted log events across pipeline steps.
- **AI Contract Hardening:** strict JSON contract for AI-generated tests with safe fallback when response is invalid.
- **Reporting:** produce JSON/Markdown reports and trend history.
- **Dashboard Control Panel:** trigger all QA commands from a Next.js UI.

## Project structure

```text
ai_data_qa/
├── api/
│   └── server.py
├── errors.py
├── tests_engine/
│   ├── generator.py
│   ├── runner.py
│   └── sql_validator.py
└── utils/
    └── logger.py

dashboard/
├── components/
├── pages/
└── types/
```

## Python API setup and run

```bash
pip install -e .
uvicorn ai_data_qa.api.server:app --reload --port 8000
```

Available command endpoints:

- `POST /scan`
- `POST /generate-tests`
- `POST /run-tests`
- `POST /analyze`
- `POST /report`

Each endpoint accepts JSON with at least:

```json
{
  "dataset": "analytics"
}
```

### Operation response payload

All action endpoints return a unified payload:

```json
{
  "status": "completed",
  "message": "Test execution completed",
  "action": "run-tests",
  "dataset": "analytics",
  "error": null
}
```

If operation fails, `error` contains a structured object:

```json
{
  "message": "Only SELECT queries are allowed",
  "category": "sql_validation",
  "code": "SQL_VALIDATION_ERROR",
  "details": {
    "sql": "DELETE FROM ..."
  }
}
```

Report read endpoints:

- `GET /report` returns `reports/data_quality_report.json`
- `GET /history` returns `reports/dq_history.json` when available

## CLI quick start

```bash
ai-data-qa scan
ai-data-qa generate-tests
ai-data-qa run-tests
ai-data-qa analyze
ai-data-qa report
```

### Selective test execution by tags

```bash
ai-data-qa run-tests --tags freshness
ai-data-qa run-tests --tags freshness,nulls
```

### Cache/result payload envelopes

The CLI now stores cached artifacts in envelope format for consistency:

- `schema_cache.json` -> `{ "schemas": [...] }`
- `tests_cache.json` -> `{ "tests": [...] }`
- `test_results.json` -> `{ "results": [...] }`
- `analysis_cache.json` -> `{ "analyses": [...] }`

## Dashboard setup and run

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:3000`.
