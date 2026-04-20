import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Upload from "./pages/Upload.jsx";
import TaxOptimizer from "./pages/TaxOptimizer.jsx";
import AuditRisk from "./pages/AuditRisk.jsx";
import TDSTracker from "./pages/TDSTracker.jsx";
import GSTTracker from "./pages/GSTTracker.jsx";
import Deductions from "./pages/Deductions.jsx";
import AdvanceTax from "./pages/AdvanceTax.jsx";
import Notifications from "./pages/Notifications.jsx";
import AIChat from "./pages/AIChat.jsx";

export default function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        {/* Public */}
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
        <Route path="/tax" element={<ProtectedRoute><TaxOptimizer /></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute><AuditRisk /></ProtectedRoute>} />
        <Route path="/tds" element={<ProtectedRoute><TDSTracker /></ProtectedRoute>} />
        <Route path="/gst" element={<ProtectedRoute><GSTTracker /></ProtectedRoute>} />
        <Route path="/deductions" element={<ProtectedRoute><Deductions /></ProtectedRoute>} />
        <Route path="/advance-tax" element={<ProtectedRoute><AdvanceTax /></ProtectedRoute>} />
        <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
        <Route path="/chat" element={<ProtectedRoute><AIChat /></ProtectedRoute>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
