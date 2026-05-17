import Navbar from "./components/Navbar.jsx";
import FaceVerificationCard from "./components/FaceVerificationCard.jsx";
import VoiceVerificationCard from "./components/VoiceVerificationCard.jsx";
import RiskAnalysisCard from "./components/RiskAnalysisCard.jsx";

const App = () => {
  return (
    <div className="relative min-h-screen text-white">
      <div className="gradient-orb absolute -top-32 right-10 h-64 w-64" />
      <div className="gradient-orb absolute bottom-12 left-0 h-72 w-72" />

      <main className="relative mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10">
        <Navbar />
        <FaceVerificationCard />
        <VoiceVerificationCard />
        <RiskAnalysisCard />
      </main>
    </div>
  );
};

export default App;