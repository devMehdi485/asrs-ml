import React from "react";
import { trendClass } from "../lib";

export function Kpi({ label, value, icon, accent }: {
  label: string; value: React.ReactNode; icon?: React.ReactNode; accent?: boolean;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-line
      bg-gradient-to-br from-surface2 to-surface p-4 shadow-card transition duration-200
      hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-glow">
      <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-accent to-accent2 opacity-70" />
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-accent/10 text-base text-accent">
        {icon}
      </span>
      <div className="mt-3 text-[0.7rem] uppercase tracking-wider text-muted">{label}</div>
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

export function PageHeader({ title, subtitle, right }: {
  title: string; subtitle: string; right?: React.ReactNode;
}) {
  return (
    <div className="mb-7 flex items-end justify-between gap-4 border-b border-line pb-5">
      <div>
        <div className="eyebrow">AeroInsight AI</div>
        <h1 className="mt-1 text-2xl font-extrabold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted">{subtitle}</p>
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

export function Trend({ t }: { t: string }) {
  return <span className={"text-sm font-semibold " + trendClass(t)}>{t}</span>;
}

export function Chip({ children }: { children: React.ReactNode }) {
  return <span className="chip">{children}</span>;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={"skeleton " + className} />;
}
