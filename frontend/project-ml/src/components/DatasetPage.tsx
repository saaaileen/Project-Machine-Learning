import { useState, useEffect, useCallback } from "react";
import {
  getModels,
  getDatasetRows,
  useModel,
  type DatasetRowsData,
} from "../api";
import "./DatasetPage.css";

const PAGE_SIZE = 10;

/** Decide the colour class for a predicted label. */
function labelClass(label: string): string {
  const l = label.toLowerCase();
  if (l === "benign") return "row-benign";
  if (
    l.includes("ddos") ||
    l.includes("attack") ||
    l.includes("dos") ||
    l.includes("bot") ||
    l.includes("brute") ||
    l.includes("infiltration") ||
    l.includes("portscan") ||
    l.includes("web attack")
  )
    return "row-attack";
  return "row-suspicious";
}

interface Props {
  token: string;
  onLogout: () => void;
}

export default function DatasetPage({ token, onLogout }: Props) {
  /* ---- Models list ---- */
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("");

  /* ---- Dataset browsing ---- */
  const [datasetInfo, setDatasetInfo] = useState<DatasetRowsData | null>(null);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ---- Row selection ---- */
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

  /* ---- Prediction results ---- */
  const [results, setResults] = useState<Record<string, unknown>[] | null>(
    null
  );
  const [predicting, setPredicting] = useState(false);

  /* ---------- Fetch models on mount ---------- */
  useEffect(() => {
    getModels(token)
      .then((res) => {
        if (res.data) {
          setModels(res.data);
          if (res.data.length > 0) setSelectedModel(res.data[0]);
        }
      })
      .catch((e) => setError(e.message));
  }, [token]);

  /* ---------- Fetch dataset page ---------- */
  const fetchPage = useCallback(
    async (offset: number) => {
      setLoading(true);
      setError(null);
      try {
        const res = await getDatasetRows(token, PAGE_SIZE, offset);
        setDatasetInfo(res.data);
        setCurrentOffset(offset);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load rows");
      } finally {
        setLoading(false);
      }
    },
    [token]
  );

  useEffect(() => {
    fetchPage(0);
  }, [fetchPage]);

  /* ---------- Selection helpers ---------- */
  function toggleRow(rowIndex: number) {
    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (next.has(rowIndex)) next.delete(rowIndex);
      else next.add(rowIndex);
      return next;
    });
  }

  function toggleAllOnPage() {
    if (!datasetInfo) return;
    const pageIndices = datasetInfo.rows.map(
      (r) => r.row_index as number
    );
    const allSelected = pageIndices.every((i) => selectedRows.has(i));

    setSelectedRows((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        pageIndices.forEach((i) => next.delete(i));
      } else {
        pageIndices.forEach((i) => next.add(i));
      }
      return next;
    });
  }

  /* ---------- Run prediction ---------- */
  async function handlePredict() {
    if (selectedRows.size === 0 || !selectedModel) return;
    setPredicting(true);
    setError(null);
    try {
      const res = await useModel(
        token,
        selectedModel,
        Array.from(selectedRows).sort((a, b) => a - b)
      );
      setResults(res.data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Prediction failed");
    } finally {
      setPredicting(false);
    }
  }

  /* ---------- Derived ---------- */
  const totalRows = datasetInfo?.total_rows ?? 0;
  const totalPages = Math.ceil(totalRows / PAGE_SIZE);
  const currentPage = Math.floor(currentOffset / PAGE_SIZE) + 1;
  const columns = datasetInfo?.columns ?? [];
  const rows = datasetInfo?.rows ?? [];
  const allOnPageSelected =
    rows.length > 0 &&
    rows.every((r) => selectedRows.has(r.row_index as number));

  /* ---- Result columns: put predicted_label first ---- */
  const resultColumns =
    results && results.length > 0
      ? [
          "predicted_label",
          ...Object.keys(results[0]).filter((k) => k !== "predicted_label"),
        ]
      : [];

  /* ========== Render ========== */
  return (
    <div className="dataset-wrapper">
      {/* Header */}
      <header className="dataset-header">
        <h1>🛡️ ML Prediction System</h1>
        <div className="header-actions">
          <span className="selected-count">
            {selectedRows.size} row{selectedRows.size !== 1 ? "s" : ""} selected
          </span>
          <button id="logout-btn" className="logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <div className="dataset-body">
        {error && <div className="error-banner">{error}</div>}

        {/* ===== Dataset browsing ===== */}
        <div className="section-card">
          <div className="section-title">
            <span className="icon"></span> Browse Dataset Rows
          </div>

          {loading ? (
            <div className="spinner-wrapper">
              <div className="spinner" />
            </div>
          ) : (
            <>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>
                        <label className="select-all-label">
                          <input
                            type="checkbox"
                            className="row-checkbox"
                            checked={allOnPageSelected}
                            onChange={toggleAllOnPage}
                          />
                        </label>
                      </th>
                      {columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => {
                      const idx = row.row_index as number;
                      const checked = selectedRows.has(idx);
                      return (
                        <tr
                          key={idx}
                          className={checked ? "selected" : ""}
                          onClick={() => toggleRow(idx)}
                          style={{ cursor: "pointer" }}
                        >
                          <td>
                            <input
                              type="checkbox"
                              className="row-checkbox"
                              checked={checked}
                              onChange={() => toggleRow(idx)}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </td>
                          {columns.map((col) => (
                            <td key={col}>
                              {row[col] != null
                                ? typeof row[col] === "number"
                                  ? (row[col] as number).toFixed
                                    ? Number(
                                        (row[col] as number).toFixed(4)
                                      ).toString()
                                    : String(row[col])
                                  : String(row[col])
                                : "—"}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="pagination-bar">
                <span className="pagination-info">
                  Page {currentPage} of {totalPages} &middot; {totalRows} total
                  rows
                </span>
                <div className="pagination-buttons">
                  <button
                    className="page-btn"
                    disabled={currentOffset === 0}
                    onClick={() => fetchPage(currentOffset - PAGE_SIZE)}
                  >
                    ← Prev
                  </button>
                  <button
                    className="page-btn"
                    disabled={currentOffset + PAGE_SIZE >= totalRows}
                    onClick={() => fetchPage(currentOffset + PAGE_SIZE)}
                  >
                    Next →
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* ===== Action bar ===== */}
        <div className="section-card">
          <div className="section-title">
            <span className="icon"></span> Run Prediction
          </div>

          <div className="action-bar">
            <label htmlFor="model-select">Model:</label>
            <select
              id="model-select"
              className="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>

            <button
              id="predict-btn"
              className="predict-btn"
              disabled={selectedRows.size === 0 || !selectedModel || predicting}
              onClick={handlePredict}
            >
              {predicting
                ? "Predicting…"
                : `Predict ${selectedRows.size} Row${selectedRows.size !== 1 ? "s" : ""}`}
            </button>
          </div>
        </div>

        {/* ===== Results ===== */}
        {results && results.length > 0 && (
          <div className="section-card">
            <div className="section-title">
              <span className="icon"></span> Prediction Results
            </div>

            <div className="table-scroll">
              <table className="data-table result-table">
                <thead>
                  <tr>
                    {resultColumns.map((col) => (
                      <th
                        key={col}
                        className={
                          col === "predicted_label" ? "label-col" : ""
                        }
                      >
                        {col === "predicted_label" ? "PREDICTED LABEL" : col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.map((row, i) => {
                    const label = String(row.predicted_label ?? "");
                    const cls = labelClass(label);
                    return (
                      <tr key={i} className={cls}>
                        {resultColumns.map((col) => (
                          <td key={col}>
                            {col === "predicted_label" ? (
                              <span className="label-cell">{label}</span>
                            ) : row[col] != null ? (
                              typeof row[col] === "number" ? (
                                Number(
                                  (row[col] as number).toFixed(4)
                                ).toString()
                              ) : (
                                String(row[col])
                              )
                            ) : (
                              "—"
                            )}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
