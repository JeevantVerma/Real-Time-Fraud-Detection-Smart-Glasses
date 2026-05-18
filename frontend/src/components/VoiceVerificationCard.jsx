import { useEffect, useRef, useState } from "react";
import MetricRow from "./MetricRow.jsx";
import StatusPill from "./StatusPill.jsx";
import { uploadVoice } from "../services/api.js";

const statusStyles = {
  genuine: "bg-emerald-500/20 text-emerald-200",
  spoofed: "bg-rose-500/20 text-rose-200",
};

const RECORD_SECONDS = 10;

const encodeWav = (samples, sampleRate) => {
  const numChannels = 1;
  const numFrames = samples.length;
  const bytesPerSample = 2;
  const blockAlign = numChannels * bytesPerSample;
  const buffer = new ArrayBuffer(44 + numFrames * blockAlign);
  const view = new DataView(buffer);

  const writeString = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + numFrames * blockAlign, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, numFrames * blockAlign, true);

  let offset = 44;
  for (let i = 0; i < numFrames; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped * 0x7fff, true);
    offset += 2;
  }

  return buffer;
};

const VoiceVerificationCard = ({ onComplete }) => {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [recording, setRecording] = useState(false);
  const [timeLeft, setTimeLeft] = useState(RECORD_SECONDS);
  const [audioFile, setAudioFile] = useState(null);

  useEffect(() => {
    if (!recording) return;

    if (timeLeft <= 0) {
      mediaRecorderRef.current?.stop();
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft((current) => current - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [recording, timeLeft]);

  const startRecording = async () => {
    setError("");
    setResult(null);
    setAudioFile(null);
    onComplete?.(false);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        try {
          if (!chunksRef.current.length) {
            setError("No audio captured. Please try again.");
            return;
          }

          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const arrayBuffer = await blob.arrayBuffer();
          const audioContext = new AudioContext();
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          const channelCount = audioBuffer.numberOfChannels;
          const length = audioBuffer.length;
          const mixed = new Float32Array(length);

          for (let channel = 0; channel < channelCount; channel += 1) {
            const data = audioBuffer.getChannelData(channel);
            for (let i = 0; i < length; i += 1) {
              mixed[i] += data[i] / channelCount;
            }
          }

          const wavBuffer = encodeWav(mixed, audioBuffer.sampleRate);
          const wavBlob = new Blob([wavBuffer], { type: "audio/wav" });
          const file = new File([wavBlob], `voice-${Date.now()}.wav`, {
            type: "audio/wav",
          });
          setAudioFile(file);
        } catch (err) {
          setError("Could not process the recorded audio.");
        } finally {
          setRecording(false);
          setTimeLeft(RECORD_SECONDS);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      setRecording(true);
      setTimeLeft(RECORD_SECONDS);
      mediaRecorder.start(250);
    } catch (err) {
      setError("Microphone permission denied or unavailable.");
    }
  };

  const analyzeVoice = async () => {
    if (!audioFile) {
      setError("Record a voice sample first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const data = await uploadVoice(audioFile);
      setResult(data);
      onComplete?.(true);
    } catch (err) {
      setError("Voice analysis failed. Please try again.");
      onComplete?.(false);
    } finally {
      setLoading(false);
    }
  };

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
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={startRecording}
            disabled={recording}
            className="rounded-full border border-cyan-400/40 px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-cyan-100 transition hover:bg-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {recording ? `Recording ${timeLeft}s` : "Record Voice"}
          </button>
          <button
            onClick={analyzeVoice}
            disabled={loading || recording || !audioFile}
            className="rounded-full bg-cyan-500/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-cyan-100 transition hover:bg-cyan-500/30 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Analyzing..." : "Analyze Voice"}
          </button>
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
              ? `${(result.voice_similarity * 100).toFixed(1)}%`
              : loading
              ? "Analyzing..."
              : audioFile
              ? "Captured"
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
              : audioFile
              ? "Ready"
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
