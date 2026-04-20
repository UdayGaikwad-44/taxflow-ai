import { useEffect, useRef, useState } from "react";
import ScreenShell from "../components/ScreenShell.jsx";
import { sendAIChat } from "../services/api.js";

function formatTime() {
  return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

export default function AIChat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hi! I'm your TaxFlow AI assistant. I have access to your financial data (income, deductions, TDS, GST ITC) and can answer tax questions specific to your situation.\n\nTry asking:\n• \"How can I save more tax?\"\n• \"Should I file ITR-3 or ITR-4?\"\n• \"What's my advance tax due next quarter?\"\n• \"How to maximize 80C deductions?\"",
      time: formatTime(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput("");
    setError("");

    const userMsg = { role: "user", content: msg, time: formatTime() };
    const history = messages.filter(m => m.role !== "assistant" || messages.indexOf(m) > 0);
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await sendAIChat(msg, history.map(m => ({ role: m.role, content: m.content })));
      setMessages(prev => [...prev, { role: "assistant", content: res.reply, time: formatTime() }]);
    } catch (e) {
      setError(e.message || "Failed to get response. Check your OpenRouter API key.");
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I couldn't process that. Please try again.", time: formatTime() }]);
    }
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const quickQuestions = [
    "How can I reduce my tax this year?",
    "Should I file ITR-3 or ITR-4?",
    "What is Section 87A rebate?",
    "How to claim home office deduction?",
  ];

  return (
    <ScreenShell>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">AI Tax Assistant</h1>
          <p className="text-gray-500">Powered by AI with your real financial data as context.</p>
        </div>
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-full px-3 py-1">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="text-xs text-green-700 font-medium">AI Online</span>
        </div>
      </div>

      {/* Quick questions */}
      <div className="flex flex-wrap gap-2 mb-4">
        {quickQuestions.map(q => (
          <button
            key={q}
            onClick={() => { setInput(q); }}
            className="text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-full px-3 py-1 hover:bg-blue-100 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat window */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col" style={{ height: "60vh" }}>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0 mt-1">
                  AI
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {msg.content}
                </div>
                <span className="text-xs text-gray-400 px-1">{msg.time}</span>
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 text-xs font-bold ml-2 flex-shrink-0 mt-1">
                  You
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0">
                AI
              </div>
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {error && (
          <div className="mx-4 mb-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">
            {error}
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-gray-100 p-4 flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask a tax question... (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="flex-1 border border-gray-200 rounded-xl px-4 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl px-5 py-2 text-sm font-medium transition-colors self-end"
          >
            Send →
          </button>
        </div>
      </div>
    </ScreenShell>
  );
}
