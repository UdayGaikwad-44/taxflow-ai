import ScreenShell from "../components/ScreenShell.jsx";

export default function ReportExport() {
  return (
    <ScreenShell
      title="Report Export"
      subtitle="Export your FY summary and supporting schedules (₹)."
    >
      <div className="space-y-3 text-sm text-slate-200">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3">
          Export placeholders: JSON/CSV, accountant pack, and ITR-ready summary.
        </div>
      </div>
    </ScreenShell>
  );
}

