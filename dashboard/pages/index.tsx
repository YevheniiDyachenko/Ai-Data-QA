import Head from 'next/head';
import { useEffect, useMemo, useState } from 'react';
import FailedTestsAccordion from '../components/FailedTestsAccordion';
import ProfilingMetrics from '../components/ProfilingMetrics';
import TableSummary from '../components/TableSummary';
import TrendChart from '../components/TrendChart';
import { fetchReport, fetchTrendHistory } from '../utils/fetchReports';
import { DataQualityReport, TableReport, TrendHistory } from '../types/report';

type FilterMode = 'all' | 'pass' | 'fail';

export default function HomePage() {
  const [report, setReport] = useState<DataQualityReport | null>(null);
  const [trendHistory, setTrendHistory] = useState<TrendHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterMode, setFilterMode] = useState<FilterMode>('all');

  const loadReports = async () => {
    setLoading(true);
    setError(null);

    try {
      const [qualityReport, history] = await Promise.all([fetchReport(), fetchTrendHistory()]);
      setReport(qualityReport);
      setTrendHistory(history);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReports();
  }, []);

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
        <title>Data Quality Dashboard</title>
        <meta name="description" content="Local dashboard for BigQuery data quality reports" />
      </Head>

      <main className="container">
        <header className="page-header">
          <div>
            <h1>Data Quality Dashboard</h1>
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
            <button onClick={() => void loadReports()} disabled={loading}>
              {loading ? 'Refreshing…' : 'Refresh'}
            </button>
          </div>
        </header>

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
