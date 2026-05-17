import { useState } from "react";
import UploadCard from "./UploadCard.jsx";
import ResultCard from "./ResultCard.jsx";
import { uploadVoice } from "../services/api.js";

const VoiceVerificationCard = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload an audio file first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data = await uploadVoice(file);
      setResult(data);
    } catch (err) {
      setError("Voice analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="glass-panel rounded-2xl p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-display font-semibold">
            Voice Verification
          </h2>
          <p className="text-sm text-slate-400">
            Upload an audio clip to check for spoofing or authenticity.
          </p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded-full bg-white/10 px-6 py-3 text-sm font-semibold transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Analyzing..." : "Analyze Voice"}
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <UploadCard
          title="Voice Capture"
          description="Use a short phrase recorded by the smart glasses mic."
          accept="audio/*"
          file={file}
          onFileChange={setFile}
          withPanel={false}
        />
        <ResultCard
          subtitle="Voice Authenticity"
          value={
            result ? (result.spoof_detected ? "Spoof" : "Authentic") : "Awaiting"
          }
          title={
            result
              ? `${(result.voice_real_score * 100).toFixed(1)}%`
              : "--"
          }
          withPanel={false}
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
