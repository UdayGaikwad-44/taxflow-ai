import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getTaxOptimize } from "../services/api.js";

function formatINR(n) { return Number(n || 0).toLocaleString("en-IN"); }

export default function TaxOptimizer() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try { setData(await getTaxOptimize()); }
      catch { setError("Failed to load tax data."); }
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Tax Optimizer</h1>
      <p className="text-gray-500 mb-6">Compare ITR-3 vs ITR-4 and find your best filing strategy.</p>
      {loading && <Spinner label="Calculating..." />}
      {error && <div className="text-red-500">{error}</div>}
      {data && (
        <div className="space-y-4">
          <div className="bg-blue-600 text-white rounded-xl p-5 text-center">
            <p className="text-sm opacity-80 mb-1">Recommendation</p>
            <p className="text-2xl font-bold">FILE {data.recommendation} — Save ₹{formatINR(data.savings)}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-bold text-gray-900 text-lg">ITR-4</h2>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">Presumptive (50% of income)</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Taxable Income</p>
                  <p className="text-xl font-bold text-gray-900">₹ {formatINR(data.itr4?.taxable_income)}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Tax Amount</p>
                  <p className="text-xl font-bold text-gray-900">₹ {formatINR(data.itr4?.tax)}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-blue-200 shadow-sm p-5">
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-bold text-blue-700 text-lg">ITR-3</h2>
                <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">Actual expenses</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-500">Taxable Income</p>
                  <p className="text-xl font-bold text-blue-700">₹ {formatINR(data.itr3?.taxable_income)}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-500">Tax Amount</p>
                  <p className="text-xl font-bold text-blue-700">₹ {formatINR(data.itr3?.tax)}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total Income", value: data.total_income },
              { label: "Total Expenses", value: data.total_expenses },
              { label: "80C Deduction", value: data.deduction_80c },
              { label: "80D Deduction", value: data.deduction_80d },
            ].map(item => (
              <div key={item.label} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                <p className="text-xl font-bold text-gray-900">₹ {formatINR(item.value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </ScreenShell>
  );
}
