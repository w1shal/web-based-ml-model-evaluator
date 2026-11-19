import { useCallback, useEffect, useState } from "react";
import { ApiError, apiRequest } from "../api/client";
import type { HistoryListItem, HistoryListResponse } from "../types/workflow";

interface HistoryPageProps {
  token: string;
  onOpen: (runId: string) => void;
  onClose: () => void;
}

function dateLabel(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function percent(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? (value * 100).toFixed(1) + "%" : "N/A";
}

export default function HistoryPage({ token, onOpen, onClose }: HistoryPageProps) {
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteCandidate, setDeleteCandidate] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiRequest<HistoryListResponse>("/history?limit=50&offset=0", { token });
      setItems(Array.isArray(result.items) ? result.items : []);
      setTotal(result.total ?? 0);
    } catch (loadError) {
      setError(loadError instanceof ApiError ? loadError.message : loadError instanceof Error ? loadError.message : "Unable to load evaluation history.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  async function deleteRun(runId: string) {
    setBusyId(runId);
    setError("");
    try {
      await apiRequest<{ message: string }>("/history/" + encodeURIComponent(runId), {
        method: "DELETE",
        token,
      });
      setDeleteCandidate(null);
      await loadHistory();
    } catch (deleteError) {
      setError(deleteError instanceof ApiError ? deleteError.message : deleteError instanceof Error ? deleteError.message : "Unable to delete this history entry.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="workflow-page history-page">
      <div className="history-heading">
        <div><span className="eyebrow">YOUR ACCOUNT</span><h2>Evaluation history</h2><p>Your saved evaluations, newest first. Only your own runs are returned by the backend.</p></div>
        <div className="workflow-actions compact">
          <button type="button" className="button button-outline" onClick={() => void loadHistory()} disabled={loading}>Refresh</button>
          <button type="button" className="button button-dark" onClick={onClose}>Close</button>
        </div>
      </div>

      {error && <div className="workflow-alert error" role="alert">{error}</div>}
      {loading && <p className="workflow-status" role="status">Loading saved evaluations…</p>}
      {!loading && !error && items.length === 0 && <div className="empty-history"><h3>No saved evaluations yet</h3><p>Run an evaluation while signed in and it will appear here.</p></div>}
      {!loading && items.length > 0 && (
        <>
          <p className="history-count">{total} saved evaluation(s)</p>
          <div className="history-list">
            {items.map((item) => (
              <article className="history-item" key={item.run_id}>
                <div className="history-item-main">
                  <div className="history-item-title"><h3>{item.dataset_name}</h3><span className={"run-status " + item.status}>{item.status}</span></div>
                  <p>{dateLabel(item.timestamp)}</p>
                  <div className="history-metrics">
                    {item.metrics.slice(0, 3).map((metric) => <span key={metric.algorithm}>{metric.algorithm.replaceAll("_", " ")} · {percent(metric.accuracy)}</span>)}
                  </div>
                  <small className="run-id">{item.run_id}</small>
                </div>
                <div className="history-item-actions">
                  <button type="button" className="button button-outline" onClick={() => onOpen(item.run_id)}>View results</button>
                  {deleteCandidate === item.run_id ? (
                    <div className="delete-confirm">
                      <span>Delete this run?</span>
                      <button type="button" className="button button-danger" disabled={busyId === item.run_id} onClick={() => void deleteRun(item.run_id)}>{busyId === item.run_id ? "Deleting…" : "Confirm delete"}</button>
                      <button type="button" className="text-button" disabled={busyId === item.run_id} onClick={() => setDeleteCandidate(null)}>Cancel</button>
                    </div>
                  ) : (
                    <button type="button" className="button button-quiet-danger" onClick={() => setDeleteCandidate(item.run_id)}>Delete</button>
                  )}
                </div>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
