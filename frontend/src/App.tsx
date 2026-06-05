import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import { useData } from "./context";
import ExecutiveIntelligence from "./pages/ExecutiveIntelligence";
import OperationalDashboard from "./pages/OperationalDashboard";
import ClusterExplorer from "./pages/ClusterExplorer";
import ThematicAnalysis from "./pages/ThematicAnalysis";
import TemporalHeatmap from "./pages/TemporalHeatmap";
import WeakSignals from "./pages/WeakSignals";

export default function App() {
  const { data, error } = useData();

  if (error)
    return (
      <div className="grid min-h-screen place-items-center p-8 text-center">
        <div className="card max-w-lg">
          <div className="text-lg font-bold text-down">Données introuvables</div>
          <p className="mt-2 text-sm text-muted">
            Impossible de charger <code>public/data/asrs.json</code> ({error}).<br />
            Lance d'abord : <code>python notebooks_assets/export_json.py</code>
          </p>
        </div>
      </div>
    );

  if (!data)
    return (
      <div className="grid min-h-screen place-items-center">
        <div className="animate-pulse text-muted">Chargement des données ASRS…</div>
      </div>
    );

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<ExecutiveIntelligence />} />
        <Route path="operational" element={<OperationalDashboard />} />
        <Route path="clusters" element={<ClusterExplorer />} />
        <Route path="thematic" element={<ThematicAnalysis />} />
        <Route path="temporal" element={<TemporalHeatmap />} />
        <Route path="weak" element={<WeakSignals />} />
      </Route>
    </Routes>
  );
}
