// MLE-F-026 / MLE-F-027 UI. All server data is written with textContent (never innerHTML),
// so dataset names or other user-controlled strings cannot inject markup (TC-SEC-002).
import { api, getToken } from "./auth.js";

const $ = (s) => document.querySelector(s);
const status = $("#status");
const say = (m) => (status.textContent = m);

function el(tag, text, attrs = {}) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
  return n;
}

const pct = (v) => (v === null || v === undefined ? "n/a" : (v * 100).toFixed(1) + "%");
const num = (v) => (v === null || v === undefined ? "n/a" : Number(v).toFixed(3));

function fail(err) {
  if (err.status === 401) {
    say("Your session has expired or you are not logged in. Please log in on the Account page.");
  } else {
    say(err.message);
  }
}

async function load() {
  const body = $("#rows");
  body.replaceChildren();
  $("#detail").hidden = true;
  if (!getToken()) {
    say("Log in to see your saved evaluations (guest runs are not saved).");
    return;
  }
  try {
    const data = await api("/history?limit=50");
    say(data.total === 0 ? "No saved evaluations yet." : `${data.total} saved evaluation(s).`);
    for (const run of data.items) {
      const tr = el("tr");
      const best = Math.max(...run.metrics.map((m) => m.accuracy ?? 0));
      tr.append(
        el("td", new Date(run.timestamp).toLocaleString()),
        el("td", run.dataset_name),
        el("td", run.algorithms.join(", ")),
        el("td", run.metrics.length ? pct(best) : "n/a"),
      );
      const actions = el("td");
      const view = el("button", "View", { type: "button", "aria-label": `View run on ${run.dataset_name}` });
      const del = el("button", "Delete", { type: "button", class: "danger", "aria-label": `Delete run on ${run.dataset_name}` });
      view.onclick = () => showDetail(run.run_id);
      del.onclick = () => remove(run);
      actions.append(view, del);
      tr.append(actions);
      body.append(tr);
    }
  } catch (err) { fail(err); }
}

async function showDetail(runId) {
  try {
    const d = await api(`/history/${encodeURIComponent(runId)}`);
    const box = $("#detail");
    box.replaceChildren(
      el("h2", d.dataset_name),
      el("p", `Target: ${d.target_column} · Features: ${d.feature_columns.join(", ")} · Test size: ${d.split_ratio}`),
    );
    const table = el("table");
    const head = el("tr");
    ["Algorithm", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"].forEach((h) => head.append(el("th", h)));
    table.append(head);
    for (const m of d.metrics) {
      const row = el("tr");
      row.append(el("td", m.algorithm), el("td", num(m.accuracy)), el("td", num(m.precision)),
                 el("td", num(m.recall)), el("td", num(m.f1_score)), el("td", num(m.roc_auc)));
      table.append(row);
    }
    box.append(table);
    for (const [algo, cm] of Object.entries(d.confusion_matrices)) {
      if (!cm) continue;
      box.append(el("h3", `Confusion matrix: ${algo}`), el("pre", cm.map((r) => r.join("\t")).join("\n")));
    }
    box.hidden = false;
    box.scrollIntoView({ behavior: "smooth" });
  } catch (err) { fail(err); }
}

async function remove(run) {
  if (!confirm(`Delete the saved run on "${run.dataset_name}"? This cannot be undone.`)) return;
  try {
    await api(`/history/${encodeURIComponent(run.run_id)}`, { method: "DELETE" });
    await load();
    say("Run deleted.");
  } catch (err) { fail(err); }
}

load();
