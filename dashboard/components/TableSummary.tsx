import { TableReport } from '../types/report';

interface TableSummaryProps {
  table: TableReport;
}

export default function TableSummary({ table }: TableSummaryProps) {
  const hasFailures = table.tests_failed > 0;

  return (
    <section className={`card ${hasFailures ? 'card-fail' : 'card-pass'}`}>
      <div className="table-header">
        <h3>{table.name}</h3>
        <span className={`status-pill ${hasFailures ? 'status-fail' : 'status-pass'}`}>
          {hasFailures ? 'Issues found' : 'All tests passed'}
        </span>
      </div>

      <div className="metrics-grid">
        <div>
          <p className="label">Tests executed</p>
          <p className="value">{table.tests_executed}</p>
        </div>
        <div>
          <p className="label">Tests passed</p>
          <p className="value success">{table.tests_passed}</p>
        </div>
        <div>
          <p className="label">Tests failed</p>
          <p className="value danger">{table.tests_failed}</p>
        </div>
      </div>
    </section>
  );
}
