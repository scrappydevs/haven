export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">TrialSentinel AI</h1>
        <p className="text-slate-400 mb-8">Clinical Trial Monitoring System</p>
        <a 
          href="/dashboard" 
          className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-block"
        >
          Go to Dashboard
        </a>
      </div>
    </div>
  );
}

