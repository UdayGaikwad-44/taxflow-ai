export default function HealthGauge({ data }) {
  if (!data) return null;
  const score = data.score || 0;
  const zone = data.zone || "orange";
  const tip = data.tip || "";
  const components = data.components || {};

  const color = zone === "green" ? "#16a34a" : zone === "orange" ? "#ea580c" : "#dc2626";
  const bgColor = zone === "green" ? "border-green-200 bg-green-50" : zone === "orange" ? "border-orange-200 bg-orange-50" : "border-red-200 bg-red-50";
  const badgeColor = zone === "green" ? "bg-green-100 text-green-700" : zone === "orange" ? "bg-orange-100 text-orange-700" : "bg-red-100 text-red-700";

  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const dash = (score / 100) * circumference;

  const compItems = [
    { label: "Deduction Coverage", value: components.deduction_coverage || 0, max: 30 },
    { label: "Audit Risk", value: components.audit_risk_inverted || 0, max: 25 },
    { label: "80C Utilization", value: components["80c_utilization"] || 0, max: 20 },
    { label: "Advance Tax", value: components.advance_tax_compliance || 0, max: 15 },
    { label: "GST ITC", value: components.gst_itc || 0, max: 10 },
  ];

  return (
    <div className={`rounded-xl border p-5 mb-4 ${bgColor}`}>
      <div className="flex items-center gap-6">
        <div className="relative flex-shrink-0">
          <svg width="130" height="130" viewBox="0 0 130 130">
            <circle cx="65" cy="65" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="10"/>
            <circle cx="65" cy="65" r={radius} fill="none" stroke={color} strokeWidth="10"
              strokeDasharray={`${dash} ${circumference}`}
              strokeLinecap="round"
              transform="rotate(-90 65 65)"
              style={{transition: "stroke-dasharray 0.5s ease"}}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-gray-900">{score}</span>
            <span className="text-xs text-gray-500">/ 100</span>
          </div>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-gray-900 font-semibold text-lg">Financial Health</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${badgeColor}`}>{zone.toUpperCase()}</span>
          </div>
          <p className="text-gray-600 text-sm mb-3">{tip}</p>
          <div className="space-y-1.5">
            {compItems.map(c => (
              <div key={c.label} className="flex items-center gap-2">
                <span className="text-gray-500 text-xs w-32">{c.label}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                  <div className="h-1.5 rounded-full" style={{width: `${(c.value/c.max)*100}%`, backgroundColor: color}}/>
                </div>
                <span className="text-gray-500 text-xs w-8 text-right">{c.value.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
