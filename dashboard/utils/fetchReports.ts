import { ApiActionResponse, DataQualityReport, TrendHistory } from '../types/report';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { cache: 'no-store', ...init });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchReport(runId?: string): Promise<DataQualityReport> {
  if (runId) {
    return fetchJson<DataQualityReport>(`${API_BASE}/report/${encodeURIComponent(runId)}`);
  }
  return fetchJson<DataQualityReport>(`${API_BASE}/report`);
}

export async function fetchTrendHistory(): Promise<TrendHistory | null> {
  try {
    return await fetchJson<TrendHistory>(`${API_BASE}/history`);
  } catch {
    return null;
  }
}

export async function triggerAction(action: string, dataset: string): Promise<ApiActionResponse> {
  return fetchJson<ApiActionResponse>(`${API_BASE}/${action}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset })
  });
}
