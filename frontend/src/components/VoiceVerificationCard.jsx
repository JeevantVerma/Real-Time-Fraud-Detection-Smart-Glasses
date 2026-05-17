import { useEffect, useState } from "react";
import MetricRow from "./MetricRow.jsx";
import StatusPill from "./StatusPill.jsx";
import { uploadVoice } from "../services/api.js";

const statusStyles = {
  genuine: "bg-emerald-500/20 text-emerald-200",
  spoofed: "bg-rose-500/20 text-rose-200",
};

const createFakeAudioFile = () => {
  const data = new Uint8Array(6000);
  if (window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(data);
  } else {
    data.forEach((_, index) => {
      data[index] = Math.floor(Math.random() * 255);
    });
  }

  return new File([data], `voice-${Date.now()}.wav`, { type: "audio/wav" });
};

const VoiceVerificationCard = ({ analysisId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!analysisId) return;

    const runAnalysis = async () => {
      setError("");
      setLoading(true);

      try {
        const fakeAudio = createFakeAudioFile();
        const data = await uploadVoice(fakeAudio);
        setResult(data);
      } catch (err) {
        setError("Voice analysis failed. Please try again.");
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
            Voice Verification
          </p>
          <h3 className="text-lg font-display font-semibold">
            Authenticity Scan
          </h3>
        </div>
        {result && (
          <StatusPill
            label={result.spoof_detected ? "Spoofed" : "Genuine"}
            className={
              result.spoof_detected ? statusStyles.spoofed : statusStyles.genuine
            }
          />
        )}
      </div>

      <div className="mt-5 space-y-3">
        <MetricRow
          label="Voice Authenticity Score"
          value={
            result
              ? `${(result.voice_real_score * 100).toFixed(1)}%`
              : loading
              ? "Analyzing..."
              : "Awaiting"
          }
          emphasize
          loading={loading}
        />
        <MetricRow
          label="Spoof Detection"
          value={
            result
              ? result.spoof_detected
                ? "Spoof Detected"
                : "Clean Signal"
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

export default VoiceVerificationCard;
