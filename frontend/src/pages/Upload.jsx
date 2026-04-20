import { useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import { uploadBankStatement, uploadReceipt } from "../services/api.js";

export default function Upload() {
  const [tab, setTab] = useState("bank"); // "bank" | "receipt"
  const [file, setFile] = useState(null);
  const [fy, setFy] = useState("FY2025-26");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    setError("");
    try {
      const res = tab === "bank"
        ? await uploadBankStatement(file, fy)
        : await uploadReceipt(file, fy);
      setResult(res);
      setFile(null);
    } catch (e) {
      setError(e.message);
    }
    setUploading(false);
  };

  const validBankTypes = [".csv"];
  const validReceiptTypes = ["image/jpeg", "image/png", "image/webp", "image/jpg"];

  const isValidFile = file && (
    tab === "bank"
      ? file.name.endsWith(".csv")
      : validReceiptTypes.includes(file.type)
  );

  return (
    <ScreenShell>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Upload</h1>
      <p className="text-gray-500 mb-6">Import bank statements or scan receipts with AI.</p>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {[
          { key: "bank", label: "📊 Bank Statement (CSV)", desc: "HDFC, SBI, ICICI, Axis, Kotak..." },
          { key: "receipt", label: "🧾 Receipt (Image)", desc: "AI OCR extracts GST, 80C, 80D" },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setFile(null); setResult(null); setError(""); }}
            className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        {/* FY selector */}
        <div className="mb-5">
          <label className="text-sm font-medium text-gray-700 block mb-1">Financial Year</label>
          <select
            value={fy}
            onChange={e => setFy(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="FY2025-26">FY 2025-26</option>
            <option value="FY2024-25">FY 2024-25</option>
            <option value="FY2023-24">FY 2023-24</option>
          </select>
        </div>

        {/* Drop zone */}
        <label className="block cursor-pointer">
          <div className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
            file ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-blue-50"
          }`}>
            {file ? (
              <>
                <p className="text-2xl mb-2">{tab === "bank" ? "📊" : "🧾"}</p>
                <p className="font-semibold text-blue-700">{file.name}</p>
                <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
              </>
            ) : (
              <>
                <p className="text-3xl mb-2">{tab === "bank" ? "📂" : "📷"}</p>
                <p className="font-medium text-gray-700">
                  {tab === "bank" ? "Drop CSV file here or click to browse" : "Drop receipt image or click to browse"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {tab === "bank" ? "Accepts: .csv (HDFC, SBI, ICICI, Axis, Kotak, Yes Bank, IndusInd)" : "Accepts: JPG, PNG, WEBP"}
                </p>
              </>
            )}
          </div>
          <input
            type="file"
            accept={tab === "bank" ? ".csv" : "image/*"}
            onChange={e => { setFile(e.target.files?.[0] || null); setResult(null); setError(""); }}
            className="hidden"
          />
        </label>

        {/* Info boxes */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {tab === "bank" ? (
            <>
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
                <p className="font-semibold text-gray-800 mb-1">Supported Banks</p>
                <p>HDFC · SBI · ICICI · Axis · Kotak · Yes Bank · IndusInd · Generic CSV</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700">
                <p className="font-semibold mb-1">What happens?</p>
                <p>Transactions are auto-categorized (meals, travel, 80C, 80D...) and saved in the background. Refresh in a few seconds.</p>
              </div>
            </>
          ) : (
            <>
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
                <p className="font-semibold text-gray-800 mb-1">AI extracts from receipt</p>
                <p>Merchant · Amount · Date · GSTIN · GST Amount · 80C/80D flags</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 text-xs text-purple-700">
                <p className="font-semibold mb-1">Uses OpenRouter Vision AI</p>
                <p>Powered by Qwen 2.5 VL 72B — extracts structured data from any receipt image.</p>
              </div>
            </>
          )}
        </div>

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={!isValidFile || uploading}
          className="mt-5 w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl py-3 font-semibold text-sm transition-colors"
        >
          {uploading
            ? (tab === "bank" ? "Parsing CSV in background..." : "AI reading receipt...")
            : (tab === "bank" ? "Upload & Parse Bank Statement" : "Upload & Extract Receipt")}
        </button>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-xl px-5 py-4">
            <p className="font-semibold text-green-800 mb-2">✅ Upload successful!</p>
            {tab === "bank" ? (
              <div className="grid grid-cols-2 gap-3 text-sm text-green-700">
                <div><span className="text-gray-500">Job ID:</span> <span className="font-mono text-xs">{result.job_id}</span></div>
                <div><span className="text-gray-500">File:</span> {result.filename}</div>
                <div><span className="text-gray-500">Financial Year:</span> {result.financial_year}</div>
              </div>
            ) : (
              <p className="text-sm text-green-700">Receipt queued for AI OCR. Check receipts after a few seconds.</p>
            )}
            <p className="text-xs text-green-600 mt-2">{result.message || result.tip}</p>
          </div>
        )}
      </div>
    </ScreenShell>
  );
}
