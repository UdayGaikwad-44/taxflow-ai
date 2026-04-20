import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getAuditScore } from "../services/api.js";

export default function AuditRisk() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try { setData(await getAuditScore()); }
      catch { setError("Failed to load audit score."); }
      finally { setLoading(false); }
    })();
  }, []);

  const zoneColor = data?.zone === "green" ? "text-green-600 bg-green-50 border-green-200"
    : data?.zone === "orange" ? "text-orange-600 bg-orange-50 border-orange-200"
    : "text-red-600 bg-red-50 border-red-200";

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Audit Risk</h1>
      <p className="text-gray-500 mb-6">Spot patterns that may trigger IT scrutiny — keep receipts tight.</p>
      {loading && <Spinner label="Calculating risk..." />}
      {error && <div className="text-red-500">{error}</div>}
      {data && (
        <div className="space-y-4">
          <div className={`rounded-xl border p-6 flex items-center gap-6 ${zoneColor}`}>
            <div>
              <p className="text-sm font-medium mb-1">Audit Score</p>
              <p className="text-6xl font-bold">{data.score}</p>
            </div>
            <div>
              <span className={`text-lg font-bold px-3 py-1 rounded-full border ${zoneColor}`}>
                {data.zone?.toUpperCase()}
              </span>
              <p className="text-sm mt-2 opacity-70">{data.total_signals_triggered} signal(s) triggered</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="font-semibold text-gray-800 mb-3">⚠ Flagged Items</h2>
              {data.flagged_items?.length === 0
                ? <p className="text-green-600 text-sm">No issues found!</p>
                : data.flagged_items?.map((item, i) => (
                  <div key={i} className="flex items-start gap-2 mb-2">
                    <span className="text-orange-500 mt-0.5">▲</span>
                    <p className="text-sm text-gray-700">{item}</p>
                  </div>
                ))}
            </div>
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="font-semibold text-gray-800 mb-3">✓ Fixes</h2>
              {data.fixes?.map((fix, i) => (
                <div key={i} className="flex items-start gap-2 mb-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <p className="text-sm text-gray-700">{fix}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </ScreenShell>
  );
}
