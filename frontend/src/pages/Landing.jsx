import { Link } from "react-router-dom";
import ScreenShell from "../components/ScreenShell.jsx";

export default function Landing() {
  return (
    <ScreenShell
      title="TaxFlow AI"
      subtitle="AI-powered tax optimization for Indian freelancers — keep more of your ₹ legally."
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3">
          <p className="text-slate-200">
            Connect income & expenses, track 80C, reconcile TDS, and generate export-ready tax reports.
          </p>
          <div className="flex gap-3">
            <Link
              to="/onboarding"
              className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-900"
            >
              Get started
            </Link>
            <Link
              to="/dashboard"
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-100"
            >
              View dashboard
            </Link>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
          <div className="text-sm text-slate-300">Preview</div>
          <div className="mt-2 grid gap-2 text-sm">
            <div className="flex justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-3">
              <span>Estimated tax (FY)</span>
              <span className="font-semibold">₹ —</span>
            </div>
            <div className="flex justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-3">
              <span>80C remaining</span>
              <span className="font-semibold">₹ —</span>
            </div>
            <div className="flex justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-3">
              <span>TDS credit found</span>
              <span className="font-semibold">₹ —</span>
            </div>
          </div>
        </div>
      </div>
    </ScreenShell>
  );
}

