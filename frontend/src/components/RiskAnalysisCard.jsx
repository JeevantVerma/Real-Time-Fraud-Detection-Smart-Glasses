import { useState } from "react";
import ResultCard from "./ResultCard.jsx";
import { fetchRiskScore } from "../services/api.js";

const statusStyles = {
  SAFE: "bg-emerald-500/20 text-emerald-300",
  SUSPICIOUS: "bg-amber-500/20 text-amber-300",
  FRAUD: "bg-rose-500/20 text-rose-300",
};

const RiskAnalysisCard = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    setError("");
    setLoading(true);

    try {
      const data = await fetchRiskScore();
      setResult(data);
    } catch (err) {
      setError("Risk analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="glass-panel rounded-2xl p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-display font-semibold">
            Unified Risk Analysis
          </h2>
          <p className="text-sm text-slate-400">
            Generate a unified fraud risk score and recommendation.
          </p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded-full bg-white/10 px-6 py-3 text-sm font-semibold transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Analyzing..." : "Generate Risk Score"}
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <ResultCard
          subtitle="Unified Risk"
          value={
            result ? `${(result.risk_score * 100).toFixed(1)}%` : "Awaiting"
          }
          title={result ? result.risk_level : "--"}
          badgeText={result ? result.risk_level : ""}
          badgeClass={result ? statusStyles[result.risk_level] : ""}
          withPanel={false}
        />
        <div className="flex flex-col justify-center gap-3 rounded-2xl border border-slate-800 bg-inkSoft/60 px-6 py-6">
          <p className="text-xs uppercase tracking-[0.25em] text-slate-400">
            Recommendation
          </p>
          <p className="text-lg font-display font-semibold">
            {result ? result.recommendation : "Run analysis to view guidance."}
          </p>
          <p className="text-sm text-slate-400">
            The recommendation updates each time you generate a new risk score.
          </p>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      )}
    </section>
  );
};

export default RiskAnalysisCard;
