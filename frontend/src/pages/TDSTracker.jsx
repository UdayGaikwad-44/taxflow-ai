import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getTDSEntries, addTDSEntry } from "../services/api.js";

function formatINR(n) { return Number(n || 0).toLocaleString("en-IN"); }

export default function TDSTracker() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ deductor_name: "", deductor_tan: "", amount: "", section: "194J", quarter: "Q1" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try { setData(await getTDSEntries()); }
    catch { setError("Failed to load TDS data."); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!form.deductor_name || !form.amount) return;
    setSaving(true);
    try {
      await addTDSEntry(form.deductor_name, form.deductor_tan, parseFloat(form.amount), form.section, form.quarter);
      setForm({ deductor_name: "", deductor_tan: "", amount: "", section: "194J", quarter: "Q1" });
      await load();
    } catch { setError("Failed to add entry."); }
    setSaving(false);
  };

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">TDS Tracker</h1>
      <p className="text-gray-500 mb-6">Track Tax Deducted at Source from your clients.</p>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
        <h2 className="font-semibold text-gray-800 mb-4">Add TDS Entry</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
          <input placeholder="Deductor Name" value={form.deductor_name}
            onChange={e => setForm({...form, deductor_name: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input placeholder="TAN Number" value={form.deductor_tan}
            onChange={e => setForm({...form, deductor_tan: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input placeholder="Amount (₹)" type="number" value={form.amount}
            onChange={e => setForm({...form, amount: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <select value={form.section} onChange={e => setForm({...form, section: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="194J">194J — Professional</option>
            <option value="194C">194C — Contractor</option>
            <option value="192">192 — Salary</option>
          </select>
          <select value={form.quarter} onChange={e => setForm({...form, quarter: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="Q1">Q1 (Apr-Jun)</option>
            <option value="Q2">Q2 (Jul-Sep)</option>
            <option value="Q3">Q3 (Oct-Dec)</option>
            <option value="Q4">Q4 (Jan-Mar)</option>
          </select>
          <button onClick={handleAdd} disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50">
            {saving ? "Saving..." : "Add Entry"}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>

      {loading && <Spinner label="Loading TDS data..." />}
      {data && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Total TDS Deducted</p>
              <p className="text-2xl font-bold text-gray-900">₹ {formatINR(data.total_tds_deducted)}</p>
            </div>
            {Object.entries(data.by_section || {}).map(([section, amount]) => (
              <div key={section} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <p className="text-xs text-gray-500 mb-1">Section {section}</p>
                <p className="text-2xl font-bold text-blue-600">₹ {formatINR(amount)}</p>
              </div>
            ))}
          </div>
          {data.entries?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h2 className="font-semibold text-gray-800">TDS Entries</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {["Deductor","TAN","Amount (₹)","Section","Quarter","Date"].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.entries.map((e, i) => (
                    <tr key={e.id} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="px-4 py-3 text-gray-800 font-medium">{e.deductor_name}</td>
                      <td className="px-4 py-3 text-gray-600">{e.deductor_tan}</td>
                      <td className="px-4 py-3 text-blue-600 font-semibold">₹ {formatINR(e.amount)}</td>
                      <td className="px-4 py-3 text-gray-600">{e.section}</td>
                      <td className="px-4 py-3 text-gray-600">{e.quarter}</td>
                      <td className="px-4 py-3 text-gray-500">{e.created_at?.split("T")[0]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </ScreenShell>
  );
}
