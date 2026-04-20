import { Link, useLocation, useNavigate } from "react-router-dom";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/upload", label: "Upload" },
  { to: "/tax", label: "Tax Optimizer" },
  { to: "/audit", label: "Audit Risk" },
  { to: "/tds", label: "TDS" },
  { to: "/gst", label: "GST ITC" },
  { to: "/deductions", label: "Deductions" },
  { to: "/advance-tax", label: "Advance Tax" },
  { to: "/notifications", label: "Alerts" },
  { to: "/chat", label: "AI Chat" },
];

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("taxflow_token");
    navigate("/");
  };

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between gap-4">
        <Link to="/dashboard" className="text-blue-600 font-bold text-lg tracking-tight flex-shrink-0">
          TaxFlow AI · ₹
        </Link>
        <div className="flex items-center gap-1 overflow-x-auto flex-1 justify-center">
          {links.map(l => {
            const active = location.pathname === l.to;
            const isChat = l.to === "/chat";
            return (
              <Link
                key={l.to}
                to={l.to}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors flex-shrink-0 ${
                  isChat
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : active
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-600 hover:text-blue-600 hover:bg-gray-50"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
        <button
          onClick={handleLogout}
          className="text-xs text-red-500 hover:text-red-700 font-medium flex-shrink-0 px-2 py-1.5 rounded-lg hover:bg-red-50 transition-colors"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
