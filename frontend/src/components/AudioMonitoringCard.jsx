import { useEffect, useMemo, useState } from "react";

const AudioMonitoringCard = ({ tick }) => {
  const [levels, setLevels] = useState(() => Array.from({ length: 14 }, () => 0.4));

  useEffect(() => {
    const interval = setInterval(() => {
      setLevels((current) =>
        current.map(() => 0.2 + Math.random() * 0.9)
      );
    }, 450);

    return () => clearInterval(interval);
  }, []);

  const bars = useMemo(
    () =>
      levels.map((level, index) => (
        <span
          key={`${tick}-${index}`}
          className="wave-bar"
          style={{ height: `${level * 60}px`, animationDelay: `${index * 0.08}s` }}
        />
      )),
    [levels, tick]
  );

  return (
    <section className="glass-panel rounded-3xl p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-400">
            Audio Monitoring
          </p>
          <h3 className="text-lg font-display font-semibold">Listening...</h3>
        </div>
        <div className="relative flex items-center gap-2 text-xs text-slate-400">
          <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.7)]" />
          Mic Active
        </div>
      </div>

      <div className="mt-5 flex items-end justify-between gap-2 rounded-2xl border border-slate-800 bg-inkSoft/70 px-4 py-6">
        {bars}
      </div>

      <p className="mt-4 text-xs text-slate-400">
        Real-time waveform visualization for ambient voice analysis.
      </p>
    </section>
  );
};

export default AudioMonitoringCard;
