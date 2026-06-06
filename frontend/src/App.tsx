import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import { Skeleton } from "./components/ui";
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
      <div className="min-h-screen p-8">
        <Skeleton className="mb-7 h-16 w-80" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-5">
          <Skeleton className="h-80 lg:col-span-3" />
          <Skeleton className="h-80 lg:col-span-2" />
        </div>
        <div className="mt-6 text-sm text-muted">Chargement des données ASRS…</div>
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
