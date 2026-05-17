const Navbar = () => {
  return (
    <header className="glass-panel rounded-2xl px-6 py-4 shadow-glow">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.25em] text-slate-400">
            Smart Glasses Control
          </p>
          <h1 className="text-2xl md:text-3xl font-display font-semibold">
            Real-Time Fraud Detection Smart Glasses
          </h1>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Live Pipeline Simulator
        </div>
      </div>
    </header>
  );
};

export default Navbar;
