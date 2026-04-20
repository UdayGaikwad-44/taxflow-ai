import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../services/api.js";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [userType, setUserType] = useState("freelancer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await register(name, email, password, userType);
      if (data?.access_token) {
        localStorage.setItem("taxflow_token", data.access_token);
        navigate("/dashboard");
      } else {
        setError("Registration failed. Please try again.");
      }
    } catch {
      setError("Email already exists or invalid data.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-blue-600">TaxFlow AI · ₹</h1>
        <p className="text-gray-500 mt-2">Create your account to get started.</p>
      </div>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-md">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)}
            placeholder="Your name"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">User Type</label>
          <select value={userType} onChange={e => setUserType(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="freelancer">Freelancer / Consultant</option>
            <option value="director">Director of Company</option>
            <option value="salaried">Salaried + Side Income</option>
          </select>
        </div>
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <button onClick={handleRegister} disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors">
          {loading ? "Creating account..." : "Register"}
        </button>
        <p className="text-center text-sm text-gray-500 mt-4">
          Already have an account? <Link to="/" className="text-blue-600 font-medium hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}
