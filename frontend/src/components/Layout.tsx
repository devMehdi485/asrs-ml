import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutGrid, Network, Tags, Calendar, AlertTriangle, TrendingUp, Plane, Sparkles,
} from "lucide-react";
import { useData } from "../context";

const NAV = [
  { to: "/", label: "Dashboard", desc: "Vue d'ensemble", icon: LayoutGrid, end: true },
  { to: "/clusters", label: "Cluster Explorer", desc: "Carte des thèmes", icon: Network },
  { to: "/thematic", label: "Thematic Analysis", desc: "Détail & modèles", icon: Tags },
  { to: "/temporal", label: "Temporal Map", desc: "Évolution dans le temps", icon: Calendar },
  { to: "/weak", label: "Weak Signals", desc: "Cas atypiques", icon: AlertTriangle },
  { to: "/predict", label: "Prédiction", desc: "Tester le modèle", icon: Sparkles },
  { to: "/executive", label: "Executive Intelligence", desc: "Résumé décideurs", icon: TrendingUp },
];

export default function Layout() {
  const { data } = useData();
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-line bg-[#0c1426] p-4">
        <div className="flex items-center gap-3 px-1 pb-5 pt-1">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-accent to-accent2 shadow-glow">
            <Plane size={22} className="text-white" />
          </div>
          <div>
            <div className="text-[1.15rem] font-extrabold leading-none">AeroInsight AI</div>
            <div className="mt-1 text-[0.68rem] tracking-wide text-muted">NASA ASRS Analytics</div>
          </div>
        </div>
        <div className="mb-4 border-b border-line" />

        <nav className="flex flex-col gap-1.5">
          {NAV.map(({ to, label, desc, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                "flex items-center gap-3 rounded-xl px-3 py-2 transition duration-200 " +
                (isActive
                  ? "bg-gradient-to-r from-accent2 to-accent text-white shadow-glow"
                  : "text-muted hover:bg-white/[.04] hover:text-ink")
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} className="shrink-0" />
                  <span className="leading-tight">
                    <span className="block text-sm font-semibold">{label}</span>
                    <span className={"block text-[0.68rem] " + (isActive ? "text-white/80" : "text-muted/70")}>{desc}</span>
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto border-t border-line pt-4 text-[0.72rem] leading-relaxed text-muted">
          {data && (
            <span className="text-ink/80">{data.meta.n_themes} thèmes · {data.meta.model}</span>
          )}
          <div className="mt-1 opacity-70">Last sync: live</div>
          <div className="opacity-70">v1.0 · NASA ASRS</div>
        </div>
      </aside>

      <main className="flex-1 overflow-x-hidden px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
