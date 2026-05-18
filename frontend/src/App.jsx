import { useEffect, useRef, useState } from "react";
import Navbar from "./components/Navbar.jsx";
import LiveFeedCard from "./components/LiveFeedCard.jsx";
import AudioMonitoringCard from "./components/AudioMonitoringCard.jsx";
import FaceVerificationCard from "./components/FaceVerificationCard.jsx";
import VoiceVerificationCard from "./components/VoiceVerificationCard.jsx";
import RiskAnalysisCard from "./components/RiskAnalysisCard.jsx";

const dataUrlToFile = (dataUrl, filename) => {
  const [metadata, encoded] = dataUrl.split(",");
  const mime = metadata.match(/:(.*?);/)[1];
  const binary = atob(encoded);
  const array = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i += 1) {
    array[i] = binary.charCodeAt(i);
  }

  return new File([array], filename, { type: mime });
};

const App = () => {
  const webcamRef = useRef(null);
  const [lastCapture, setLastCapture] = useState(null);
  const [monitorTick, setMonitorTick] = useState(0);
  const [faceReady, setFaceReady] = useState(false);
  const [voiceReady, setVoiceReady] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setMonitorTick((current) => current + 1);
    }, 3500);

    return () => clearInterval(interval);
  }, []);

  const captureFace = () => {
    const screenshot = webcamRef.current?.getScreenshot();
    if (!screenshot) {
      return null;
    }

    const file = dataUrlToFile(screenshot, `face-${Date.now()}.jpg`);
    setLastCapture(new Date());
    return file;
  };

  return (
    <div className="relative min-h-screen text-white">
      <div className="gradient-orb absolute -top-32 right-10 h-64 w-64" />
      <div className="gradient-orb absolute bottom-12 left-0 h-72 w-72" />

      <main className="relative mx-auto flex max-w-6xl flex-col gap-6 px-6 py-8">
        <Navbar />

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <LiveFeedCard webcamRef={webcamRef} lastCapture={lastCapture} />
          <div className="flex flex-col gap-6">
            <AudioMonitoringCard tick={monitorTick} />
            <FaceVerificationCard
              onCapture={captureFace}
              onComplete={setFaceReady}
            />
            <VoiceVerificationCard onComplete={setVoiceReady} />
            <RiskAnalysisCard
              canAnalyze={faceReady && voiceReady}
              faceReady={faceReady}
              voiceReady={voiceReady}
            />
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;