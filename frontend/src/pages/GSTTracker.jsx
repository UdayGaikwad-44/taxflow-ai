import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getGSTSummary } from "../services/api.js";

function formatINR(n) { return Number(n || 0).toLocaleString("en-IN"); }

export default function GSTTracker() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try { setData(await getGSTSummary()); }
      catch { setError("Failed to load GST data."); }
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">GST ITC Tracker</h1>
      <p className="text-gray-500 mb-6">Track unclaimed GST Input Tax Credits from your receipts.</p>
      {loading && <Spinner label="Loading GST data..." />}
      {error && <div className="text-red-500">{error}</div>}
      {data && (
        <div className="space-y-4">
          {data.total_itc_available > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-amber-800 text-sm font-medium">
              ⚠ {data.alert}
            </div>
          )}
          {data.total_itc_available === 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-blue-700 text-sm">
              {data.alert}
            </div>
          )}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Total ITC Available</p>
              <p className="text-2xl font-bold text-green-600">₹ {formatINR(data.total_itc_available)}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Receipts with GST</p>
              <p className="text-2xl font-bold text-gray-900">{data.receipts_with_gst}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Total Receipts</p>
              <p className="text-2xl font-bold text-gray-900">{data.total_receipts}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">ITC by Rate</p>
              <div className="text-xs text-gray-600 mt-1 space-y-0.5">
                {Object.entries(data.by_rate || {}).filter(([,v]) => v > 0).map(([rate, amt]) => (
                  <div key={rate} className="flex justify-between">
                    <span>{rate}</span>
                    <span className="font-medium">₹{formatINR(amt)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {data.entries?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h2 className="font-semibold text-gray-800">Receipts with GST</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {["Merchant","Category","Amount (₹)","GST Amount (₹)","GSTIN","Date"].map(h => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.entries.map((e, i) => (
                    <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="px-4 py-3 text-gray-800 font-medium">{e.merchant}</td>
                      <td className="px-4 py-3 text-gray-600">{e.category}</td>
                      <td className="px-4 py-3 text-gray-900">₹ {formatINR(e.amount)}</td>
                      <td className="px-4 py-3 text-green-600 font-semibold">₹ {formatINR(e.gst_amount)}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{e.gstin || "—"}</td>
                      <td className="px-4 py-3 text-gray-500">{e.date || "—"}</td>
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
