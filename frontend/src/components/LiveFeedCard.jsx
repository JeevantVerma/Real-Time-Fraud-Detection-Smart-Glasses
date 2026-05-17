import Webcam from "react-webcam";

const LiveFeedCard = ({ webcamRef, lastCapture, isCapturing }) => {
  return (
    <section className="glass-panel relative h-full overflow-hidden rounded-3xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-400">
            Smart Glasses Live Feed
          </p>
          <h2 className="text-xl font-display font-semibold">
            Vision Stream
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.6)]" />
          LIVE
        </div>
      </div>

      <div className="relative overflow-hidden rounded-2xl border border-slate-800">
        <Webcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          className="aspect-video w-full object-cover"
          videoConstraints={{ facingMode: "user" }}
        />
        <div className="scan-line" />
        {isCapturing && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50">
            <div className="rounded-full border border-cyan-400/60 bg-cyan-500/10 px-4 py-2 text-xs uppercase tracking-[0.3em] text-cyan-200">
              Capturing
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
        <span>Resolution: 1280 x 720</span>
        <span>
          {lastCapture
            ? `Last capture: ${lastCapture.toLocaleTimeString()}`
            : "Awaiting analysis"}
        </span>
      </div>
    </section>
  );
};

export default LiveFeedCard;
