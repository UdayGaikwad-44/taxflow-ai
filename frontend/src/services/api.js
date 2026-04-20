import axios from "axios";

// Use empty baseURL so all /api/* calls go through Vite's server-side proxy.
// The proxy is configured in vite.config.js to forward /api → http://backend:8000
// This works correctly in both Docker and local development.
const API_BASE_URL = "";
const TOKEN_KEY = "taxflow_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  if (!token) localStorage.removeItem(TOKEN_KEY);
  else localStorage.setItem(TOKEN_KEY, token);
}

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function errorMessage(err) {
  return err?.response?.data?.detail || err?.response?.data?.message || err?.message || "Request failed";
}

/* ── Auth ───────────────────────────────────────────────────────── */
export async function login(email, password) {
  try {
    const { data } = await api.post("/api/auth/login", { email, password });
    if (data?.access_token) setToken(data.access_token);
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function register(name, email, password, user_type) {
  try {
    const { data } = await api.post("/api/auth/register", { name, email, password, user_type });
    if (data?.access_token) setToken(data.access_token);
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

/* ── Transactions ────────────────────────────────────────────────── */
export async function getTransactions(params = {}) {
  try {
    const { data } = await api.get("/api/transactions", { params });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function createTransaction(payload) {
  try {
    const { data } = await api.post("/api/transactions", payload);
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function deleteTransaction(id) {
  try {
    await api.delete(`/api/transactions/${id}`);
  } catch (err) { throw new Error(errorMessage(err)); }
}

/* ── Receipts ────────────────────────────────────────────────────── */
export async function getReceipts(params = {}) {
  try {
    const { data } = await api.get("/api/receipts", { params });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function deleteReceipt(id) {
  try {
    await api.delete(`/api/receipts/${id}`);
  } catch (err) { throw new Error(errorMessage(err)); }
}

/* ── Upload ──────────────────────────────────────────────────────── */
export async function uploadBankStatement(file, financial_year = "FY2025-26") {
  try {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post(`/api/upload/bank-statement?financial_year=${financial_year}`, form, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function uploadReceipt(file, financial_year = "FY2025-26") {
  try {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post(`/api/upload/receipt?financial_year=${financial_year}`, form, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

/* ── Tax ─────────────────────────────────────────────────────────── */
export async function getTaxOptimize() {
  try { const { data } = await api.get("/api/tax/optimize"); return data; }
  catch (err) { throw new Error(errorMessage(err)); }
}

export async function getAuditScore() {
  try { const { data } = await api.get("/api/tax/audit-score"); return data; }
  catch (err) { throw new Error(errorMessage(err)); }
}

export async function getHealthScore() {
  try { const { data } = await api.get("/api/tax/health-score"); return data; }
  catch (e) { return null; }
}

/* ── TDS ─────────────────────────────────────────────────────────── */
export async function addTDSEntry(deductor_name, deductor_tan, amount, section, quarter) {
  try {
    const { data } = await api.post("/api/tds/entry", { deductor_name, deductor_tan, amount, section, quarter });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

export async function getTDSEntries() {
  try { const { data } = await api.get("/api/tds/summary"); return data; }
  catch (err) { throw new Error(errorMessage(err)); }
}

export async function deleteTDSEntry(id) {
  try { await api.delete(`/api/tds/${id}`); }
  catch (err) { throw new Error(errorMessage(err)); }
}

/* ── GST ─────────────────────────────────────────────────────────── */
export async function getGSTSummary() {
  try { const { data } = await api.get("/api/gst/itc-summary"); return data; }
  catch (e) { return null; }
}

/* ── Deductions ──────────────────────────────────────────────────── */
export async function getDeductionsSummary(financial_year = "FY2025-26") {
  try {
    const { data } = await api.get("/api/deductions/summary", { params: { financial_year } });
    return data;
  } catch (e) { return null; }
}

/* ── Advance Tax ─────────────────────────────────────────────────── */
export async function getAdvanceTaxSchedule(financial_year = "FY2025-26") {
  try {
    const { data } = await api.get("/api/advance-tax/schedule", { params: { financial_year } });
    return data;
  } catch (e) { return null; }
}

/* ── Matches ─────────────────────────────────────────────────────── */
export async function getMatches() {
  try { const { data } = await api.get("/api/matches/auto"); return data; }
  catch (e) { return null; }
}

/* ── Notifications ───────────────────────────────────────────────── */
export async function getNotifications() {
  try { const { data } = await api.get("/api/notifications"); return data; }
  catch (e) { return null; }
}

/* ── AI Chat ─────────────────────────────────────────────────────── */
export async function sendAIChat(message, history = []) {
  try {
    const { data } = await api.post("/api/ai/chat", { message, history });
    return data;
  } catch (err) { throw new Error(errorMessage(err)); }
}

/* ── Report ──────────────────────────────────────────────────────── */
export async function downloadReport() {
  const token = localStorage.getItem("taxflow_token");
  const response = await fetch(`${API_BASE_URL}/api/report/generate`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "taxflow_report.pdf";
  a.click();
  window.URL.revokeObjectURL(url);
}
