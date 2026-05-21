const API_BASE = "http://127.0.0.1:8000";

/** Generic wrapper for the backend HttpResponse shape. */
export interface ApiResponse<T = unknown> {
  code: number;
  status: string;
  messages: string;
  data: T;
  error_message: string | null;
}

/** -------- Auth -------- */

export interface LoginData {
  access_token: string;
  token_type: string;
}

export async function login(password: string): Promise<ApiResponse<LoginData>> {
  const res = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Login failed (${res.status})`);
  }
  return res.json();
}

/** -------- Models -------- */

export async function getModels(token: string): Promise<ApiResponse<string[]>> {
  const res = await fetch(`${API_BASE}/api/models/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to fetch models (${res.status})`);
  return res.json();
}

/** -------- Dataset Rows -------- */

export interface DatasetRowsData {
  total_rows: number;
  offset: number;
  limit: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export async function getDatasetRows(
  token: string,
  limit: number,
  offset: number
): Promise<ApiResponse<DatasetRowsData>> {
  const res = await fetch(
    `${API_BASE}/api/dataset/rows?limit=${limit}&offset=${offset}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!res.ok) throw new Error(`Failed to fetch rows (${res.status})`);
  return res.json();
}

/** -------- Use Model -------- */

export async function useModel(
  token: string,
  modelName: string,
  rowIndices: number[]
): Promise<ApiResponse<Record<string, unknown>[]>> {
  const res = await fetch(`${API_BASE}/api/models/use`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ model_name: modelName, row_indices: rowIndices }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Prediction failed (${res.status})`);
  }
  return res.json();
}
