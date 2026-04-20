import ScreenShell from "../components/ScreenShell.jsx";

export default function Onboarding() {
  return (
    <ScreenShell
      title="Onboarding"
      subtitle="Set up your freelancer profile, FY, and sources (₹)."
    >
      <div className="space-y-3 text-sm text-slate-200">
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3">
          Profile, PAN/GST (optional), and preferred tax regime will live here.
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3">
          Connect bank feeds / upload statements, then upload receipts for matching.
        </div>
      </div>
    </ScreenShell>
  );
}

