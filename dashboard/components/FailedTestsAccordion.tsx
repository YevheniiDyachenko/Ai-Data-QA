import { TableReport } from '../types/report';

interface FailedTestsAccordionProps {
  table: TableReport;
  criticalThreshold?: number;
}

export default function FailedTestsAccordion({
  table,
  criticalThreshold = 100
}: FailedTestsAccordionProps) {
  return (
    <details className="card accordion" open={table.tests_failed > 0}>
      <summary>
        Failed tests for <strong>{table.name}</strong> ({table.tests_failed})
      </summary>

      {table.tests_failed === 0 ? (
        <p className="muted">No failed tests for this table.</p>
      ) : (
        <ul className="failed-list">
          {table.failed_tests.map((failedTest) => {
            const isCritical = failedTest.failed_rows > criticalThreshold;

            return (
              <li key={failedTest.name} className={isCritical ? 'critical' : ''}>
                <div className="failed-item-title">
                  <span>{failedTest.name}</span>
                  <span>{failedTest.failed_rows.toLocaleString()} failed rows</span>
                </div>
                {isCritical && (
                  <p className="critical-note">
                    Critical failure: failed rows exceed {criticalThreshold}.
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {table.ai_analysis && (
        <div className="analysis-box">
          <h4>AI analysis</h4>
          <p>{table.ai_analysis}</p>
        </div>
      )}
    </details>
  );
}
