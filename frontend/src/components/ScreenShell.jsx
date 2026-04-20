import NavBar from "./NavBar.jsx";

export default function ScreenShell({ children }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        {children}
      </main>
    </div>
  );
}
