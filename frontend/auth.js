// Unchanged from Sprint 1, except API base URL is now configurable for deployment:
// set  window.API_BASE = ""  (same origin, behind nginx) before loading this module.
export const API = typeof window.API_BASE === "string" ? window.API_BASE : "http://localhost:8000";
export const getToken = () => localStorage.getItem("token");

export async function api(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = getToken();
  if (t) headers.Authorization = `Bearer ${t}`;   // no token = guest, still works
  const res = await fetch(API + path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      data.detail ||
      data.error?.fields?.map((f) => `${f.field}: ${f.message}`).join("; ") ||
      data.error?.message ||
      "Request failed";
    throw Object.assign(new Error(msg), { status: res.status });
  }
  return data;
}

export const register = (b) =>
  api("/auth/register", { method: "POST", body: JSON.stringify(b) });

export async function login(identifier, password) {
  const d = await api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
  localStorage.setItem("token", d.access_token);
  localStorage.setItem("user", JSON.stringify(d.user));
  return d;
}

export async function logout() {
  try {
    await api("/auth/logout", { method: "POST" });
  } finally {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }
}
