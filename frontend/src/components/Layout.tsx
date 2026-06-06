import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard, Gauge, Boxes, Layers, Flame, AlertTriangle, Plane,
} from "lucide-react";
import { useData } from "../context";
import { fmt } from "../lib";

const NAV = [
  { to: "/", label: "Executive Intelligence", icon: LayoutDashboard, end: true },
  { to: "/operational", label: "Operational Dashboard", icon: Gauge },
  { to: "/clusters", label: "Cluster Explorer", icon: Boxes },
  { to: "/thematic", label: "Thematic Analysis", icon: Layers },
  { to: "/temporal", label: "Temporal Heatmap", icon: Flame },
  { to: "/weak", label: "Weak Signals", icon: AlertTriangle },
];

export default function Layout() {
  const { data } = useData();
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 shrink-0 border-r border-line bg-gradient-to-b from-[#081020] to-[#0a1730] p-4 flex flex-col">
        <div className="flex items-center gap-3 px-1 pb-6 pt-1">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-accent to-accent2 text-xl shadow-glow">
            <Plane size={20} className="text-[#06121f]" />
          </div>
          <div>
            <div className="text-[1.05rem] font-extrabold leading-tight">AeroInsight AI</div>
            <div className="-mt-0.5 text-[0.68rem] text-muted">NASA ASRS · Safety Intelligence</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition duration-200 " +
                (isActive
                  ? "bg-accent/15 text-accent border border-accent/30 shadow-glow"
                  : "text-muted hover:bg-white/5 hover:text-ink hover:translate-x-0.5 border border-transparent")
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto pt-6 text-[0.75rem] leading-relaxed text-muted">
          {data && (
            <>
              <b className="text-ink">{fmt(data.meta.n_reports)}</b> rapports<br />
              <b className="text-ink">{data.meta.n_themes}</b> thèmes détectés<br />
              Modèle : <b className="text-accent">{data.meta.model}</b>
            </>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-x-hidden px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
