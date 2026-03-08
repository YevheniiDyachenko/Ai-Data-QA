import Head from 'next/head';
import { useCallback, useEffect, useMemo, useState } from 'react';
import FailedTestsAccordion from '../components/FailedTestsAccordion';
import ProfilingMetrics from '../components/ProfilingMetrics';
import TableSummary from '../components/TableSummary';
import TrendChart from '../components/TrendChart';
import { fetchReport, fetchTrendHistory, triggerAction } from '../utils/fetchReports';
import { ActionStatus, DataQualityReport, TableReport, TrendHistory } from '../types/report';

type FilterMode = 'all' | 'pass' | 'fail';
const ACTIONS = ['scan', 'generate-tests', 'run-tests', 'analyze', 'report'];

export default function HomePage() {
  const [report, setReport] = useState<DataQualityReport | null>(null);
  const [trendHistory, setTrendHistory] = useState<TrendHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dataset, setDataset] = useState('analytics');
  const [filterMode, setFilterMode] = useState<FilterMode>('all');
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [actionStatus, setActionStatus] = useState<ActionStatus>('idle');

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [qualityReport, history] = await Promise.all([fetchReport(), fetchTrendHistory()]);
      setReport(qualityReport);
      setDataset(qualityReport.dataset || dataset);
      setTrendHistory(history);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [dataset]);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  const handleAction = async (action: string) => {
    setActiveAction(action);
    setActionStatus('pending');
    setError(null);

    try {
      await triggerAction(action, dataset);
      await loadReports();
      setActionStatus('completed');
    } catch (actionError) {
      setActionStatus('error');
      setError(actionError instanceof Error ? actionError.message : 'Unknown error');
    } finally {
      setActiveAction(null);
    }
  };

  const filteredTables = useMemo(() => {
    if (!report) {
      return [];
    }

    return report.tables.filter((table) => {
      if (filterMode === 'pass') {
        return table.tests_failed === 0;
      }
      if (filterMode === 'fail') {
        return table.tests_failed > 0;
      }
      return true;
    });
  }, [filterMode, report]);

  return (
    <>
      <Head>
        <title>Data QA Control Panel</title>
        <meta name="description" content="Control and monitor BigQuery data quality workflows" />
      </Head>

      <main className="container">
        <header className="page-header">
          <div>
            <h1>Data QA Control Panel</h1>
            <p className="muted">Dataset: {report?.dataset ?? '-'}</p>
          </div>

          <div className="header-actions">
            <select
              value={filterMode}
              onChange={(event) => setFilterMode(event.target.value as FilterMode)}
              aria-label="Filter tables by status"
            >
              <option value="all">All tables</option>
              <option value="pass">Passing only</option>
              <option value="fail">Failing only</option>
            </select>
            <button onClick={() => void loadReports()} disabled={loading || actionStatus === 'pending'}>
              {loading ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>
        </header>

        <section className="card control-panel">
          <h2>Run QA workflow</h2>
          <div className="dataset-row">
            <label htmlFor="dataset">Dataset</label>
            <input
              id="dataset"
              type="text"
              value={dataset}
              onChange={(event) => setDataset(event.target.value)}
              disabled={actionStatus === 'pending'}
            />
          </div>

          <div className="action-grid">
            {ACTIONS.map((action) => (
              <button
                key={action}
                onClick={() => void handleAction(action)}
                disabled={actionStatus === 'pending' || !dataset.trim()}
              >
                {activeAction === action && actionStatus === 'pending' ? (
                  <span className="button-loader" aria-label="Loading" />
                ) : null}
                {action}
              </button>
            ))}
          </div>

          <p className={`status-text status-${actionStatus}`}>
            Status: <strong>{actionStatus}</strong>
          </p>
        </section>

        {error && <p className="error">Unable to load report: {error}</p>}

        {!loading && !error && report && (
          <>
            {trendHistory?.history?.length ? <TrendChart history={trendHistory.history} /> : null}

            {filteredTables.length === 0 ? (
              <p className="muted">No tables match the selected filter.</p>
            ) : (
              filteredTables.map((table: TableReport) => (
                <section key={table.name} className="table-stack">
                  <TableSummary table={table} />
                  <FailedTestsAccordion table={table} />
                  <ProfilingMetrics table={table} />
                </section>
              ))
            )}
          </>
        )}
      </main>
    </>
  );
}
