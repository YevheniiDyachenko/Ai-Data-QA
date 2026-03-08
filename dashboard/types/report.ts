export type ActionStatus = 'idle' | 'pending' | 'completed' | 'error';

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

export interface ErrorPayload {
  message: string;
  category?: string;
  code?: string;
  details?: Record<string, unknown>;
}

export interface LastOperation {
  action: string;
  status: ActionStatus;
  message: string;
  timestamp: string;
  error?: ErrorPayload | null;
}

export interface RunManifest {
  run_id: string;
  started_at?: string;
  finished_at?: string;
  dataset: string;
  status: string;
  artifact_paths: Record<string, string>;
}

export interface DataQualityReport {
  dataset: string;
  tables: TableReport[];
  run_id?: string;
  manifest?: RunManifest;
  last_operation?: LastOperation;
}

export interface TrendPoint {
  run_id: string;
  run_date: string;
  tests_passed: number;
  tests_failed: number;
}

export interface TrendHistory {
  dataset: string;
  history: TrendPoint[];
  runs: RunManifest[];
}

export interface ApiActionResponse {
  status: ActionStatus;
  message: string;
  action: string;
  dataset: string;
  error?: ErrorPayload | null;
}
