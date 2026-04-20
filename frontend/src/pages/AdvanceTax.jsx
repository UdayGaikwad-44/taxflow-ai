import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getAdvanceTaxSchedule } from "../services/api.js";

function formatINR(n) { return Number(n || 0).toLocaleString("en-IN"); }

const STATUS = {
  overdue: { bg: "bg-red-50", border: "border-red-300", badge: "bg-red-100 text-red-700", text: "Overdue ⚠" },
  due_soon: { bg: "bg-amber-50", border: "border-amber-300", badge: "bg-amber-100 text-amber-700", text: "Due Soon 🔔" },
  upcoming: { bg: "bg-gray-50", border: "border-gray-200", badge: "bg-gray-100 text-gray-600", text: "Upcoming" },
};

export default function AdvanceTax() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setData(await getAdvanceTaxSchedule()); }
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Advance Tax</h1>
      <p className="text-gray-500 mb-6">Quarterly advance tax schedule computed from your income data.</p>

      {loading && <Spinner label="Calculating advance tax..." />}

      {data && (
        <div className="space-y-4">
          {/* Summary header */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Total Income", value: `₹ ${formatINR(data.total_income)}`, sub: data.financial_year },
              { label: "Tax Liability", value: `₹ ${formatINR(data.total_tax_liability)}`, sub: "After 4% cess" },
              { label: "TDS Deducted", value: `₹ ${formatINR(data.tds_already_deducted)}`, sub: "From Form 26AS" },
              { label: "Net Payable", value: `₹ ${formatINR(data.net_tax_payable)}`, sub: "Advance tax due", highlight: true },
            ].map(c => (
              <div key={c.label} className={`rounded-xl border p-4 ${c.highlight ? "bg-blue-600 border-blue-600 text-white" : "bg-white border-gray-200 shadow-sm"}`}>
                <p className={`text-xs mb-1 ${c.highlight ? "opacity-80" : "text-gray-500"}`}>{c.label}</p>
                <p className={`text-xl font-bold ${c.highlight ? "" : "text-gray-900"}`}>{c.value}</p>
                <p className={`text-xs mt-0.5 ${c.highlight ? "opacity-70" : "text-gray-400"}`}>{c.sub}</p>
              </div>
            ))}
          </div>

          {/* Advance tax not required banner */}
          {!data.advance_tax_required && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-green-800 text-sm">
              ✅ <strong>No advance tax required</strong> — your net tax liability is ≤ ₹10,000. You can pay the full amount at the time of filing.
            </div>
          )}

          {/* Note */}
          {data.advance_tax_required && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-blue-800 text-sm">
              ℹ {data.note}
            </div>
          )}

          {/* Instalment schedule */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="bg-gray-50 px-5 py-3 border-b border-gray-200 flex items-center justify-between">
              <h2 className="font-semibold text-gray-800">Instalment Schedule — FY {data.financial_year}</h2>
              <span className="text-xs text-gray-500">New Tax Regime · Section 211</span>
            </div>
            <div className="divide-y divide-gray-100">
              {(data.schedule || []).map((inst) => {
                const s = STATUS[inst.status] || STATUS.upcoming;
                return (
                  <div key={inst.quarter} className={`${s.bg} px-5 py-4 flex items-center gap-4`}>
                    {/* Quarter badge */}
                    <div className="w-12 h-12 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-gray-700">{inst.quarter}</span>
                    </div>
                    {/* Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <span className="font-semibold text-gray-900 text-sm">{inst.label}</span>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${s.badge}`}>{s.text}</span>
                      </div>
                      <p className="text-xs text-gray-500">
                        Due: {new Date(inst.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                        {inst.days_remaining > 0 && ` · ${inst.days_remaining} days left`}
                      </p>
                    </div>
                    {/* Amounts */}
                    <div className="text-right flex-shrink-0">
                      <p className="font-bold text-gray-900 text-lg">₹ {formatINR(inst.instalment_amount)}</p>
                      <p className="text-xs text-gray-400">{inst.cumulative_pct}% cumulative · ₹{formatINR(inst.cumulative_amount)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Explanation */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs text-gray-500 space-y-1">
            <p>• Calculations use FY 2025-26 new regime slabs + 4% health & education cess.</p>
            <p>• Section 87A rebate applied — income up to ₹12L has zero tax liability.</p>
            <p>• Interest u/s 234B & 234C applies if advance tax is not paid by due dates.</p>
          </div>
        </div>
      )}
    </ScreenShell>
  );
}
