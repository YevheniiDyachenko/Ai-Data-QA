import { DataQualityReport, TrendHistory } from '../types/report';

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: 'no-store' });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${path}: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchReport(): Promise<DataQualityReport> {
  return fetchJson<DataQualityReport>('/reports/data_quality_report.json');
}

export async function fetchTrendHistory(): Promise<TrendHistory | null> {
  const response = await fetch('/reports/dq_history.json', { cache: 'no-store' });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch /reports/dq_history.json: ${response.status}`);
  }

  return (await response.json()) as TrendHistory;
}
