import { useState } from "react";
import { AppLayout } from "./layouts/AppLayout";
import { LandingPage } from "./pages/LandingPage";
import { AnalyzerPage } from "./pages/AnalyzerPage";

export default function App() {
  const [inWorkspace, setInWorkspace] = useState(false);

  if (!inWorkspace) {
    return <LandingPage onEnter={() => setInWorkspace(true)} />;
  }

  return (
    <AppLayout onHome={() => setInWorkspace(false)}>
      <AnalyzerPage />
    </AppLayout>
  );
}
