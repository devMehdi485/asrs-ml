import React from "react";
import { trendClass } from "../lib";

export function Kpi({ label, value, icon, accent }: {
  label: string; value: React.ReactNode; icon?: React.ReactNode; accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-line bg-gradient-to-br from-surface2 to-surface p-4 shadow-card">
      <div className="text-lg opacity-90">{icon}</div>
      <div className="mt-1 text-[0.7rem] uppercase tracking-wider text-muted">{label}</div>
      <div className={"mt-0.5 text-2xl font-extrabold " +
        (accent
          ? "bg-gradient-to-br from-ink to-accent bg-clip-text text-transparent"
          : "text-ink")}>
        {value}
      </div>
    </div>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={"card " + className}>{children}</div>;
}

export function Section({ children }: { children: React.ReactNode }) {
  return <div className="sec">{children}</div>;
}

export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
      <p className="mt-1 text-sm text-muted">{subtitle}</p>
    </div>
  );
}

export function Trend({ t }: { t: string }) {
  return <span className={"text-sm font-semibold " + trendClass(t)}>{t}</span>;
}

export function Chip({ children }: { children: React.ReactNode }) {
  return <span className="chip">{children}</span>;
}
