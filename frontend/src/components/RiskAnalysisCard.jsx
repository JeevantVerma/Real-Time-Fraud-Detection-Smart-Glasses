import { useEffect, useState } from "react";
import MetricRow from "./MetricRow.jsx";
import StatusPill from "./StatusPill.jsx";
import { fetchRiskScore } from "../services/api.js";

const statusStyles = {
  SAFE: "bg-emerald-500/20 text-emerald-300",
  SUSPICIOUS: "bg-amber-500/20 text-amber-300",
  FRAUD: "bg-rose-500/20 text-rose-300",
};

const RiskAnalysisCard = ({ analysisId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!analysisId) return;

    const runAnalysis = async () => {
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

    runAnalysis();
  }, [analysisId]);

  return (
    <section className="glass-panel rounded-3xl p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-400">
            Unified Fraud Risk
          </p>
          <h3 className="text-lg font-display font-semibold">Threat Level</h3>
        </div>
        {result && (
          <StatusPill
            label={result.risk_level}
            className={statusStyles[result.risk_level]}
          />
        )}
      </div>

      <div className="mt-5 space-y-3">
        <MetricRow
          label="Risk Score"
          value={
            result
              ? `${(result.risk_score * 100).toFixed(1)}%`
              : loading
              ? "Analyzing..."
              : "Awaiting"
          }
          emphasize
          loading={loading}
        />
        <MetricRow
          label="Recommendation"
          value={
            result
              ? result.recommendation
              : loading
              ? "Compiling"
              : "--"
          }
          loading={loading}
        />
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
