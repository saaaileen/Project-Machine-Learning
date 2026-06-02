/** Same-origin: no host/port prefix needed when served by FastAPI. */
const API_BASE = "";

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

/** -------- Datasets -------- */

export interface DatasetListData {
  datasets: string[];
  active: string;
}

export async function listDatasets(
  token: string
): Promise<ApiResponse<DatasetListData>> {
  const res = await fetch(`${API_BASE}/api/dataset/list`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to list datasets (${res.status})`);
  return res.json();
}

export async function switchDataset(
  token: string,
  filename: string
): Promise<ApiResponse<null>> {
  const res = await fetch(`${API_BASE}/api/dataset/switch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ filename }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Switch failed (${res.status})`);
  }
  return res.json();
}

export async function uploadDataset(
  token: string,
  file: File
): Promise<ApiResponse<{ filename: string }>> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/dataset/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Upload failed (${res.status})`);
  }
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
