import ScreenShell from "../components/ScreenShell.jsx";

export default function Tracker80C() {
  return (
    <ScreenShell title="80C Tracker" subtitle="Track 80C usage and remaining limit (₹).">
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-300">80C used</div>
          <div className="mt-2 text-lg font-semibold">₹ —</div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="text-xs text-slate-300">80C remaining</div>
          <div className="mt-2 text-lg font-semibold">₹ —</div>
        </div>
      </div>
    </ScreenShell>
  );
}

