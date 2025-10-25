export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center max-w-4xl px-8">
        <h1 className="text-6xl md:text-7xl font-playfair font-black mb-6 bg-gradient-to-r from-primary-950 to-primary-700 bg-clip-text text-transparent">
          TrialSentinel
        </h1>
        <p className="text-xl font-extralight text-neutral-700 mb-12 leading-relaxed">
          Real-time computer vision monitoring for clinical trial safety
        </p>
        <a 
          href="/dashboard" 
          className="border-2 border-neutral-950 px-8 py-3 font-normal text-xs uppercase tracking-widest hover:bg-neutral-950 hover:text-white transition-all inline-block"
        >
          Launch Dashboard
        </a>
      </div>
    </div>
  );
}

