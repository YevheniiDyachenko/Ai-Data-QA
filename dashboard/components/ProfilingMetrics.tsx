import { TableReport } from '../types/report';

interface ProfilingMetricsProps {
  table: TableReport;
}

function MetricMap({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);

  return (
    <div>
      <h4>{title}</h4>
      {entries.length === 0 ? (
        <p className="muted">No metrics reported.</p>
      ) : (
        <div className="mini-grid">
          {entries.map(([column, count]) => (
            <div key={column} className="mini-card">
              <span>{column}</span>
              <strong>{count.toLocaleString()}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProfilingMetrics({ table }: ProfilingMetricsProps) {
  return (
    <section className="card">
      <h3>Profiling metrics: {table.name}</h3>
      <p className="label">Row count</p>
      <p className="value">{table.profiling.row_count.toLocaleString()}</p>

      <div className="profiling-grid">
        <MetricMap title="Null count" data={table.profiling.null_count} />
        <MetricMap title="Distinct count" data={table.profiling.distinct_count} />
      </div>
    </section>
  );
}
