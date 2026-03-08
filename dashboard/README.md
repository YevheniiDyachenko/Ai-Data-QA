# Data Quality Dashboard (Next.js + TypeScript)

Web dashboard for controlling and visualizing the AI Data QA workflow.

## Features

- Control panel to trigger API actions:
  - `scan`
  - `generate-tests`
  - `run-tests`
  - `analyze`
  - `report`
- Live action status (`pending`, `completed`, `error`)
- Loader while actions run
- Buttons disabled while command is in flight
- Auto-refresh of report JSON after each action
- Modular report components:
  - `TableSummary`
  - `FailedTestsAccordion`
  - `ProfilingMetrics`
  - `TrendChart`

## Run locally

```bash
npm install
npm run dev
```

The dashboard expects the FastAPI backend on `http://localhost:8000` by default.

Optional override:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```
