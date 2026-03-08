# AI Data QA Tool – 3-Month Implementation Roadmap

## Overview

### Goals for the next 3 months
- Make the tool **reliable in production-like usage** (safe execution, better failure handling, traceable runs).
- Improve **data quality detection coverage** beyond current heuristic static checks.
- Upgrade the dashboard from a basic control panel to a **workflow UI for investigation**.
- Add lightweight operations capabilities: **scheduling + notifications**.
- Keep design intentionally simple and maintainable for **one engineer**.

### Key priorities (value vs effort)
1. **Foundation safety and traceability** (rule schema, SQL validation, run metadata).
2. **Coverage and anomaly detection** (accepted values, relationships, freshness, metric drift).
3. **Operational UX** (drill-down views, alerts, scheduled runs).
4. **Incremental platform growth** (auth/RBAC, multi-dataset, connector abstraction).

### Why these priorities (market alignment)
- **Great Expectations / dbt tests** show the value of reusable, typed quality checks and documentation.
- **Soda Core** demonstrates clear checks-as-code and SQL-first transparency.
- **Monte Carlo / Datafold / Bigeye** emphasize anomaly monitoring, alert routing, and incident-oriented workflows.

---

## Phase 0 – Foundation Hardening (Weeks 1–3)

> Objective: reduce failure modes, increase trust, and create core metadata for all future features.

### Task 0.1 – Introduce structured rule schema + storage contract

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/tests_engine/models.py`, `ai_data_qa/tests_engine/generator.py`, `ai_data_qa/tests_engine/runner.py`, `config.yaml`, `ai_data_qa/cli.py` |
| Architecture/code changes | Add `RuleDefinition` model (rule_type, severity, owner, dimensions, sql, enabled). Persist to `tests_cache.json` in versioned schema (`schema_version`). Include backward-compatible loader for legacy caches. |
| Dependencies/libraries | No new dependency required (Pydantic already present). |
| Effort | **Medium** |

**Suggested model sketch**
```python
class RuleDefinition(BaseModel):
    id: str
    table_name: str
    rule_type: Literal[
        "not_null", "unique", "accepted_values", "relationship", "freshness", "custom_sql"
    ]
    severity: Literal["low", "medium", "high"] = "medium"
    owner: str | None = None
    sql: str
    expected_metric: Literal["failed_rows"] = "failed_rows"
    enabled: bool = True
    metadata: dict[str, Any] = {}
```

---

### Task 0.2 – Add SQL safety validator before execution

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/tests_engine/runner.py`, `ai_data_qa/tests_engine/generator.py`, `ai_data_qa/ai/prompts.py` |
| Architecture/code changes | Validate generated SQL is single-statement `SELECT`, no DDL/DML keywords, and returns expected `failed_rows` alias. Skip invalid tests with explicit error classification. |
| Dependencies/libraries | Optional: `sqlglot` for SQL parsing (recommended). |
| Effort | **Low–Medium** |

**Validation rules (minimal):**
- Reject: `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`.
- Require exactly one query statement.
- Require alias `failed_rows` in projection.

---

### Task 0.3 – Persist run metadata in SQLite

| Item | Details |
|---|---|
| Target files/modules | New `ai_data_qa/storage/` module, `ai_data_qa/cli.py`, `ai_data_qa/api/server.py`, `ai_data_qa/reports/report_generator.py` |
| Architecture/code changes | Add local DB (`reports/qa_runs.db`) with tables: `runs`, `run_steps`, `test_results`, `analysis_results`. Assign `run_id` per workflow. Include `dataset`, `started_at`, `completed_at`, status, error class. |
| Dependencies/libraries | Built-in `sqlite3` (no external dependency). |
| Effort | **Medium** |

**Schema starter**
```sql
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  dataset TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  triggered_by TEXT DEFAULT 'cli'
);
```

---

### Task 0.4 – Standardize error taxonomy + structured logging

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/utils/logger.py`, `ai_data_qa/api/server.py`, `ai_data_qa/cli.py`, `ai_data_qa/bigquery/client.py`, `ai_data_qa/ai/client.py` |
| Architecture/code changes | Define error codes (`CONFIG_ERROR`, `BQ_AUTH_ERROR`, `SQL_VALIDATION_ERROR`, `AI_PROVIDER_ERROR`, `TEST_RUNTIME_ERROR`) and return them in API payload + report metadata. Add JSON-style logs with `run_id`, `stage`, `table`, `test_name`. |
| Dependencies/libraries | Optional `structlog`; otherwise standard `logging` JSON formatter. |
| Effort | **Low** |

---

### Task 0.5 – API and report payload consistency pass

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/api/server.py`, `dashboard/types/report.ts`, `dashboard/utils/fetchReports.ts` |
| Architecture/code changes | Normalize API responses with stable fields (`status`, `code`, `message`, `run_id`). Ensure `/report` and `/history` include dataset and generated timestamp. |
| Dependencies/libraries | None |
| Effort | **Low** |

---

## Phase 1 – Detection & Coverage (Weeks 4–7)

> Objective: catch more real-world quality issues while keeping SQL-first transparency.

### Task 1.1 – Expand static rule library

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/tests_engine/generator.py`, `ai_data_qa/tests_engine/models.py`, `config.yaml` |
| Architecture/code changes | Add native rule generators for `accepted_values`, `relationships` (FK-like), `freshness`, `row_count_change`, `null_rate_threshold`. Enable via config defaults + per-table overrides. |
| Dependencies/libraries | None mandatory |
| Effort | **Medium** |

**Reference justification:** aligns with dbt-style canonical tests and Great Expectations-style expectation breadth.

---

### Task 1.2 – Profile history persistence + trend baselines

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/bigquery/profiler.py`, new `ai_data_qa/metrics/`, `ai_data_qa/reports/report_generator.py` |
| Architecture/code changes | Persist per-column metric history (`row_count`, `null_ratio`, `distinct_ratio`) by run. Compute rolling baseline (e.g., 7-run median). |
| Dependencies/libraries | Optional: `numpy` for robust baseline math. |
| Effort | **Medium** |

---

### Task 1.3 – Lightweight anomaly detection

| Item | Details |
|---|---|
| Target files/modules | new `ai_data_qa/anomaly/detector.py`, `ai_data_qa/cli.py`, `ai_data_qa/api/server.py` |
| Architecture/code changes | Add anomaly checks using z-score/IQR on historical metric series. Emit anomaly events as pseudo-tests (`status=FAILED`, `rule_type=anomaly`). |
| Dependencies/libraries | Optional: `scipy` (not required; can implement manually). |
| Effort | **Medium** |

**Reference justification:** borrows observability-platform behavior (Monte Carlo/Bigeye style metric anomaly surfacing).

---

### Task 1.4 – Harden AI test generation contract

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/ai/prompts.py`, `ai_data_qa/tests_engine/generator.py`, `ai_data_qa/ai/analyzer.py` |
| Architecture/code changes | Change AI output format to strict JSON (`[{test_name, sql, rationale, severity}]`), parse deterministically, validate SQL, and fallback to static-only when invalid. |
| Dependencies/libraries | None |
| Effort | **Low–Medium** |

---

### Task 1.5 – Add test tagging and selective execution

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/tests_engine/models.py`, `ai_data_qa/cli.py`, `dashboard/pages/index.tsx` |
| Architecture/code changes | Add tags (`critical`, `schema`, `distribution`, `freshness`) and CLI/API filters (`--tag`, `--table`) for faster focused runs. |
| Dependencies/libraries | None |
| Effort | **Low** |

---

## Phase 2 – UX, Collaboration & Operations (Weeks 8–10)

> Objective: make dashboard a practical operational workspace, not just a command launcher.

### Task 2.1 – Dashboard drill-down and run comparison

| Item | Details |
|---|---|
| Target files/modules | `dashboard/pages/index.tsx`, `dashboard/components/TrendChart.tsx`, `dashboard/components/FailedTestsAccordion.tsx`, new components in `dashboard/components/` |
| Architecture/code changes | Add run selector and compare mode (`current vs previous`). Clicking trend points opens failed tests and SQL details for that run. Add severity badges and table/test filters. |
| Dependencies/libraries | Existing `recharts` is sufficient. |
| Effort | **Medium** |

---

### Task 2.2 – Alerts (Slack + Email/Webhook)

| Item | Details |
|---|---|
| Target files/modules | new `ai_data_qa/alerts/` module, `config.yaml`, `ai_data_qa/cli.py`, `ai_data_qa/api/server.py` |
| Architecture/code changes | Create alert dispatcher with adapters (`slack_webhook`, `email_smtp`, generic webhook). Trigger alerts on high-severity failures/anomalies. Include run link + AI summary snippet. |
| Dependencies/libraries | Optional: `httpx`; SMTP via stdlib `smtplib`. |
| Effort | **Low–Medium** |

**Reference justification:** matches incident-routing expectations from observability tools.

---

### Task 2.3 – Scheduling and retry policy

| Item | Details |
|---|---|
| Target files/modules | new `ai_data_qa/scheduler/`, `ai_data_qa/cli.py`, API endpoint additions in `ai_data_qa/api/server.py` |
| Architecture/code changes | Add lightweight scheduler config (`interval`, `dataset`, `enabled`) and background worker process. Implement retry/backoff for transient BigQuery failures. |
| Dependencies/libraries | Optional: `APScheduler` (simple + lightweight). |
| Effort | **Medium** |

---

### Task 2.4 – Report versioning and artifact links

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/reports/report_generator.py`, `dashboard/utils/fetchReports.ts`, `dashboard/types/report.ts` |
| Architecture/code changes | Store reports by run (`reports/runs/<run_id>/...`) and keep an index manifest for quick retrieval. UI shows downloadable artifacts and timestamps. |
| Dependencies/libraries | None |
| Effort | **Low** |

---

## Phase 3 – Multi-user & Platform Growth (Weeks 11–12)

> Objective: introduce minimal multi-user capabilities and prep architecture for future expansion.

### Task 3.1 – Authentication and RBAC-lite

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/api/server.py`, new `ai_data_qa/auth/`, dashboard login/session pages |
| Architecture/code changes | Add token-based auth + roles (`viewer`, `operator`, `admin`). Restrict mutating actions (`scan/generate/run/analyze/report`) to operator/admin. |
| Dependencies/libraries | FastAPI OAuth/JWT stack (`python-jose`, `passlib`) optional. |
| Effort | **Medium–High** |

---

### Task 3.2 – Multi-dataset workspace support

| Item | Details |
|---|---|
| Target files/modules | `config.yaml`, `ai_data_qa/config.py`, `dashboard/pages/index.tsx`, storage layer |
| Architecture/code changes | Replace single dataset config with named workspace list. Add workspace selector in dashboard and isolate runs/history per workspace. |
| Dependencies/libraries | None |
| Effort | **Medium** |

---

### Task 3.3 – Warehouse connector abstraction

| Item | Details |
|---|---|
| Target files/modules | `ai_data_qa/bigquery/client.py`, new `ai_data_qa/warehouse/base.py`, adapter packages |
| Architecture/code changes | Define `WarehouseClient` interface (`execute_query`, `get_schema`, `profile_table`) and migrate BigQuery to adapter implementation. |
| Dependencies/libraries | Later adapters: Snowflake, Redshift, Databricks SDKs (future). |
| Effort | **High** |

---

## Quick Wins (<1 week)

1. **SQL validator gate before runner execution** (high trust gain, low code).
2. **Error code + run_id in API responses** to improve support/debug loops.
3. **Add severity labels to failed tests in dashboard** for triage.
4. **Expose last successful run timestamp + duration on home page**.
5. **Improve AI parsing to JSON-first with strict fallback** (avoid broken SQL/test entries).
6. **Add tiny report manifest file** listing latest run artifacts.
7. **Add CLI `--table` filter** for targeted runs during incident response.

---

## Notes for Future Scaling (post 3 months)

- **Incident workflow layer:** acknowledge/assign/resolve with notes and SLA timers.
- **Audit trail:** immutable logs of who triggered runs and changed rules.
- **Data catalog integration:** connect rule ownership and glossary context.
- **Cross-warehouse lineage-aware checks:** tie quality alerts to upstream model changes.
- **Advanced ML anomaly models:** seasonality-aware detection and false-positive suppression.
- **Team collaboration primitives:** comments, runbook links, escalation policies.

---

## Suggested execution order (single-maintainer cadence)

- **Month 1:** Phase 0 + quick wins.
- **Month 2:** Phase 1 core tasks (rule expansion + metric baselines + AI hardening).
- **Month 3:** Phase 2 essentials (drill-down + alerts + scheduling), then Phase 3 starter (auth + workspace groundwork).

This sequence maximizes reliability first, then detection quality, then operational usability—matching patterns validated by Great Expectations, Soda Core, dbt tests, and observability platforms while preserving a lightweight architecture.
