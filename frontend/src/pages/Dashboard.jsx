import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getTransactions, downloadReport, getHealthScore } from "../services/api.js";
import HealthGauge from "../components/HealthGauge.jsx";

function Card({ label, value }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function formatINR(n) {
  return Number(n || 0).toLocaleString("en-IN");
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [health, setHealth] = useState(null);

  const handleDownloadReport = async () => {
    try { await downloadReport(); } catch (e) { alert("Failed to download report"); }
  };

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const res = await getTransactions();
        const h = await getHealthScore();
        if (!alive) return;
        setData(res);
        setHealth(h);
      } catch (err) {
        if (!alive) return;
        setError("Failed to load data.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const kpis = useMemo(() => {
    if (!data?.items) return { totalIncome: 0, totalDeductions: 0, count: 0, fy: "FY2025-26" };
    const items = data.items;
    const totalIncome = items.filter(t => t.direction === "in").reduce((s, t) => s + Math.abs(t.amount), 0);
    const totalDeductions = items.filter(t => t.deductible).reduce((s, t) => s + Math.abs(t.amount), 0);
    const fy = items[0]?.financial_year || "FY2025-26";
    return { totalIncome, totalDeductions, count: items.length, fy };
  }, [data]);

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Dashboard</h1>
      <p className="text-gray-500 mb-6">Your tax snapshot in ₹.</p>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-500">Amounts shown in <span className="font-medium text-gray-800">₹ INR</span></p>
          <div className="flex gap-3">
            <Link to="/upload" className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:border-gray-400 font-medium">
              Upload CSV
            </Link>
            <button onClick={handleDownloadReport}
              className="rounded-lg border border-green-600 bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700 font-medium">
              Download Report PDF
            </button>
          </div>
        </div>

        <HealthGauge data={health} />

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Card label="Total Income" value={`₹ ${formatINR(kpis.totalIncome)}`} />
          <Card label="Total Deductions" value={`₹ ${formatINR(kpis.totalDeductions)}`} />
          <Card label="Transactions" value={kpis.count} />
          <Card label="Financial Year" value={kpis.fy} />
        </div>

        {loading ? <Spinner label="Fetching transactions..." /> : null}
        {error ? <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">{error}</div> : null}

        {data?.items?.length > 0 && (
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h2 className="font-semibold text-gray-800">Transactions</h2>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {["Date","Narration","Amount (₹)","Category","Deductible","Section"].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.items.map((t, i) => (
                  <tr key={t.id} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                    <td className="px-4 py-3 text-gray-600">{t.date}</td>
                    <td className="px-4 py-3 text-gray-800 font-medium">{t.narration}</td>
                    <td className={`px-4 py-3 font-semibold ${t.amount < 0 ? "text-red-600" : "text-green-600"}`}>
                      {t.amount < 0 ? `-₹ ${formatINR(Math.abs(t.amount))}` : `₹ ${formatINR(t.amount)}`}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{t.category}</td>
                    <td className={`px-4 py-3 font-medium ${t.deductible ? "text-green-600" : "text-red-500"}`}>
                      {t.deductible ? "Yes" : "No"}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{t.section || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </ScreenShell>
  );
}
