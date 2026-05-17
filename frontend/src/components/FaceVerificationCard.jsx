import { useState } from "react";
import UploadCard from "./UploadCard.jsx";
import ResultCard from "./ResultCard.jsx";
import { uploadFace } from "../services/api.js";

const FaceVerificationCard = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload a face image first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data = await uploadFace(file);
      setResult(data);
    } catch (err) {
      setError("Face analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="glass-panel rounded-2xl p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-display font-semibold">
            Face Verification
          </h2>
          <p className="text-sm text-slate-400">
            Upload a clear image and verify the identity match score.
          </p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="rounded-full bg-white/10 px-6 py-3 text-sm font-semibold transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Analyzing..." : "Analyze Face"}
        </button>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <UploadCard
          title="Face Capture"
          description="Use a front-facing photo from the smart glasses camera."
          accept="image/*"
          file={file}
          onFileChange={setFile}
          withPanel={false}
        />
        <ResultCard
          subtitle="Face Match Result"
          value={
            result ? (result.same_person ? "Match" : "No Match") : "Awaiting"
          }
          title={
            result
              ? `${(result.face_match_score * 100).toFixed(1)}%`
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

export default FaceVerificationCard;
