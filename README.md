# AI Data QA for BigQuery

AI Data QA is a lightweight, AI-powered tool for automated data quality validation in Google BigQuery. It supports a CLI workflow and a web dashboard control panel backed by FastAPI.

## Features

- **Schema Discovery:** scan BigQuery datasets and table schemas.
- **Data Profiling:** collect row counts, null counts, and distinct counts.
- **Automated Testing:** generate and run SQL quality tests.
- **AI Analysis:** optionally analyze failed tests with LLM guidance.
- **Reporting:** produce JSON/Markdown reports and trend history.
- **Dashboard Control Panel:** trigger all QA commands from a Next.js UI.

## Project structure

```text
ai_data_qa/
├── api/
│   └── server.py

dashboard/
├── components/
│   ├── TableSummary.tsx
│   ├── FailedTestsAccordion.tsx
│   ├── ProfilingMetrics.tsx
│   └── TrendChart.tsx
├── pages/
│   └── index.tsx
├── public/reports/
│   ├── data_quality_report.json
│   └── dq_history.json
└── utils/
    └── fetchReports.ts
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

Report read endpoints:

- `GET /report` returns `reports/data_quality_report.json`
- `GET /history` returns `reports/dq_history.json` when available

## Dashboard setup and run

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:3000`.

## Using the Control Panel

1. Start the FastAPI server on port `8000`.
2. Start the dashboard on port `3000`.
3. Enter a dataset name in the dashboard input.
4. Run commands using buttons in this order:
   - `scan`
   - `generate-tests`
   - `run-tests`
   - `analyze`
   - `report`
5. The dashboard automatically refreshes the latest JSON report after each action.
6. While a command runs:
   - loader/spinner appears,
   - command buttons are disabled,
   - status updates to `pending`, then `completed` or `error`.

## CLI quick start (optional)

```bash
ai-data-qa scan
ai-data-qa generate-tests
ai-data-qa run-tests
ai-data-qa analyze
ai-data-qa report
```
