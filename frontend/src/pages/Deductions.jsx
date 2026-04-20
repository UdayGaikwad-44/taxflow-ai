import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getDeductionsSummary } from "../services/api.js";

function formatINR(n) { return Number(n || 0).toLocaleString("en-IN"); }

function ProgressBar({ value, max, color = "bg-blue-500" }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="w-full bg-gray-100 rounded-full h-2">
      <div className={`${color} h-2 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function Deductions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setData(await getDeductionsSummary()); }
      finally { setLoading(false); }
    })();
  }, []);

  const s80c = data?.summary?.["80C"];
  const s80d = data?.summary?.["80D"];

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Deductions Tracker</h1>
      <p className="text-gray-500 mb-6">Track 80C, 80D, and other tax deductions for FY 2025-26.</p>

      {loading && <Spinner label="Loading deductions..." />}

      {data && (
        <div className="space-y-4">
          {/* Total deductions card */}
          <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl p-6">
            <p className="text-sm opacity-80 mb-1">Total Effective Deductions</p>
            <p className="text-4xl font-bold">₹ {formatINR(data.total_effective_deductions)}</p>
            <p className="text-sm opacity-70 mt-1">FY {data.financial_year}</p>
          </div>

          {/* 80C & 80D cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 80C */}
            {s80c && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="font-bold text-gray-900">Section 80C</h2>
                    <p className="text-xs text-gray-500">PPF · ELSS · LIC · NPS · ELSS</p>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                    s80c.utilization_pct >= 100 ? "bg-green-100 text-green-700" :
                    s80c.utilization_pct >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  }`}>
                    {s80c.utilization_pct}% used
                  </span>
                </div>
                <div className="mb-3">
                  <ProgressBar value={s80c.raw} max={s80c.limit} color={s80c.utilization_pct >= 100 ? "bg-green-500" : "bg-blue-500"} />
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <p className="text-xs text-gray-500">Invested</p>
                    <p className="font-bold text-gray-900 text-sm">₹{formatINR(s80c.raw)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Effective</p>
                    <p className="font-bold text-blue-600 text-sm">₹{formatINR(s80c.effective)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Remaining</p>
                    <p className={`font-bold text-sm ${s80c.remaining > 0 ? "text-red-500" : "text-green-600"}`}>
                      ₹{formatINR(s80c.remaining)}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2 text-center">Limit: ₹1,50,000</p>
              </div>
            )}

            {/* 80D */}
            {s80d && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="font-bold text-gray-900">Section 80D</h2>
                    <p className="text-xs text-gray-500">Health & Medical Insurance Premiums</p>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                    s80d.utilization_pct >= 100 ? "bg-green-100 text-green-700" :
                    s80d.utilization_pct >= 50 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
                  }`}>
                    {s80d.utilization_pct}% used
                  </span>
                </div>
                <div className="mb-3">
                  <ProgressBar value={s80d.raw} max={s80d.limit} color={s80d.utilization_pct >= 100 ? "bg-green-500" : "bg-purple-500"} />
                </div>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <p className="text-xs text-gray-500">Invested</p>
                    <p className="font-bold text-gray-900 text-sm">₹{formatINR(s80d.raw)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Effective</p>
                    <p className="font-bold text-purple-600 text-sm">₹{formatINR(s80d.effective)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Remaining</p>
                    <p className={`font-bold text-sm ${s80d.remaining > 0 ? "text-red-500" : "text-green-600"}`}>
                      ₹{formatINR(s80d.remaining)}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-2 text-center">Limit: ₹25,000</p>
              </div>
            )}
          </div>

          {/* Tips */}
          {data.tips?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-2">
              <p className="text-sm font-semibold text-amber-800">💡 Tips to Maximize Deductions</p>
              {data.tips.map((tip, i) => (
                <p key={i} className="text-sm text-amber-700">• {tip}</p>
              ))}
            </div>
          )}

          {/* All sections breakdown */}
          {data.by_section?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="bg-gray-50 px-5 py-3 border-b border-gray-200">
                <h2 className="font-semibold text-gray-800">All Deductions by Section</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {["Section", "Invested (₹)", "Effective (₹)", "Limit (₹)"].map(h => (
                      <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.by_section.map((sec, i) => (
                    <tr key={sec.section} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="px-5 py-3 font-semibold text-blue-700">{sec.section}</td>
                      <td className="px-5 py-3 text-gray-800">₹ {formatINR(sec.raw_amount)}</td>
                      <td className="px-5 py-3 font-semibold text-green-700">₹ {formatINR(sec.effective_amount)}</td>
                      <td className="px-5 py-3 text-gray-500">{sec.limit ? `₹ ${formatINR(sec.limit)}` : "No cap"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </ScreenShell>
  );
}
