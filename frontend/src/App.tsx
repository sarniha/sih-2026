import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { WsStatusProvider } from "./contexts/WsStatusContext";
import { EvidenceViewerProvider } from "./contexts/EvidenceViewerContext";
import { EvidenceViewerModal } from "./components/ui/EvidenceViewerModal";
import { Layout } from "./components/layout/Layout";
import { MapPage } from "./pages/MapPage";
import { TrafficPage } from "./pages/TrafficPage";
import { AnprPage } from "./pages/AnprPage";
import { CasesPage } from "./pages/CasesPage";
import { FleetPage } from "./pages/FleetPage";
import { InsightsPage } from "./pages/InsightsPage";
import { SettingsPage } from "./pages/SettingsPage";

export default function App() {
  return (
    <WsStatusProvider>
      <EvidenceViewerProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<MapPage />} />
              <Route path="traffic" element={<TrafficPage />} />
              <Route path="anpr" element={<AnprPage />} />
              <Route path="cases" element={<CasesPage />} />
              <Route path="fleet" element={<FleetPage />} />
              <Route path="insights" element={<InsightsPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <EvidenceViewerModal />
      </EvidenceViewerProvider>
    </WsStatusProvider>
  );
}
