import { useEffect, useState } from "react";
import MetricRow from "./MetricRow.jsx";
import StatusPill from "./StatusPill.jsx";
import { uploadFace } from "../services/api.js";

const statusStyles = {
  match: "bg-emerald-500/20 text-emerald-200",
  mismatch: "bg-rose-500/20 text-rose-200",
};

const FaceVerificationCard = ({ analysisId, faceFile }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!analysisId) return;

    const runAnalysis = async () => {
      if (!faceFile) {
        setError("No camera frame captured yet.");
        return;
      }

      setError("");
      setLoading(true);

      try {
        const data = await uploadFace(faceFile);
        setResult(data);
      } catch (err) {
        setError("Face analysis failed. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    runAnalysis();
  }, [analysisId, faceFile]);

  return (
    <section className="glass-panel rounded-3xl p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-400">
            Face Verification
          </p>
          <h3 className="text-lg font-display font-semibold">Identity Match</h3>
        </div>
        {result && (
          <StatusPill
            label={result.same_person ? "Match" : "Mismatch"}
            className={
              result.same_person ? statusStyles.match : statusStyles.mismatch
            }
          />
        )}
      </div>

      <div className="mt-5 space-y-3">
        <MetricRow
          label="Face Match Score"
          value={
            result
              ? `${(result.face_match_score * 100).toFixed(1)}%`
              : loading
              ? "Analyzing..."
              : "Awaiting"
          }
          emphasize
          loading={loading}
        />
        <MetricRow
          label="Detected Persona"
          value={
            result
              ? result.same_person
                ? "Same Person"
                : "Mismatch"
              : loading
              ? "Scanning"
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

export default FaceVerificationCard;
