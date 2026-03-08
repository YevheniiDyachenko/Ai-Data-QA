export interface FailedTest {
  name: string;
  failed_rows: number;
}

export interface Profiling {
  row_count: number;
  null_count: Record<string, number>;
  distinct_count: Record<string, number>;
}

export interface TableReport {
  name: string;
  tests_executed: number;
  tests_passed: number;
  tests_failed: number;
  failed_tests: FailedTest[];
  profiling: Profiling;
  ai_analysis?: string;
}

export interface DataQualityReport {
  dataset: string;
  tables: TableReport[];
}

export interface TrendPoint {
  run_date: string;
  tests_passed: number;
  tests_failed: number;
}

export interface TrendHistory {
  dataset: string;
  history: TrendPoint[];
}
