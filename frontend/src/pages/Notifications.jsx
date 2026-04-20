import { useEffect, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import Spinner from "../components/Spinner.jsx";
import { getNotifications } from "../services/api.js";

const STATUS_STYLES = {
  overdue: { bg: "bg-red-50", border: "border-red-200", badge: "bg-red-100 text-red-700", dot: "bg-red-500", label: "Overdue" },
  due_soon: { bg: "bg-amber-50", border: "border-amber-200", badge: "bg-amber-100 text-amber-700", dot: "bg-amber-500", label: "Due Soon" },
  action_needed: { bg: "bg-blue-50", border: "border-blue-200", badge: "bg-blue-100 text-blue-700", dot: "bg-blue-500", label: "Action Needed" },
  upcoming: { bg: "bg-gray-50", border: "border-gray-200", badge: "bg-gray-100 text-gray-600", dot: "bg-gray-400", label: "Upcoming" },
};

const CATEGORY_ICONS = {
  advance_tax: "📅",
  itr: "📋",
  gst: "🧾",
  tds: "📄",
  audit: "🔍",
  deduction: "💰",
  onboarding: "🚀",
};

export default function Notifications() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setData(await getNotifications()); }
      finally { setLoading(false); }
    })();
  }, []);

  const notifications = data?.notifications || [];

  const countByStatus = (status) => notifications.filter(n => n.status === status).length;

  return (
    <ScreenShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Notifications</h1>
          <p className="text-gray-500">Tax deadlines, alerts, and action items.</p>
        </div>
        {data && (
          <div className="flex gap-3">
            {countByStatus("overdue") > 0 && (
              <span className="bg-red-100 text-red-700 text-xs font-semibold px-3 py-1 rounded-full">
                {countByStatus("overdue")} Overdue
              </span>
            )}
            {countByStatus("due_soon") > 0 && (
              <span className="bg-amber-100 text-amber-700 text-xs font-semibold px-3 py-1 rounded-full">
                {countByStatus("due_soon")} Due Soon
              </span>
            )}
            {countByStatus("action_needed") > 0 && (
              <span className="bg-blue-100 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full">
                {countByStatus("action_needed")} Action Needed
              </span>
            )}
          </div>
        )}
      </div>

      {loading && <Spinner label="Loading notifications..." />}

      {!loading && notifications.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-4xl mb-3">✅</p>
          <p className="font-semibold text-gray-700">All clear!</p>
          <p className="text-sm text-gray-500 mt-1">No pending notifications. Upload your bank statement to get started.</p>
        </div>
      )}

      {notifications.length > 0 && (
        <div className="space-y-3">
          {notifications.map((n) => {
            const style = STATUS_STYLES[n.status] || STATUS_STYLES.upcoming;
            const icon = CATEGORY_ICONS[n.category] || "📌";
            return (
              <div
                key={n.id}
                className={`${style.bg} border ${style.border} rounded-xl p-4 flex items-start gap-4`}
              >
                <div className="text-2xl flex-shrink-0 mt-0.5">{icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-semibold text-gray-900 text-sm">{n.title}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${style.badge}`}>
                      {style.label}
                    </span>
                    {n.priority === "high" && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-600">
                        High Priority
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{n.message}</p>
                  {n.due_date && (
                    <p className="text-xs text-gray-400 mt-1">
                      Due: {new Date(n.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                      {n.days_remaining > 0 && ` (${n.days_remaining} days remaining)`}
                    </p>
                  )}
                </div>
                <div className={`w-2 h-2 rounded-full flex-shrink-0 mt-2 ${style.dot}`}></div>
              </div>
            );
          })}
        </div>
      )}
    </ScreenShell>
  );
}
