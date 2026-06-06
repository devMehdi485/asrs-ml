import React from "react";
import { trendClass } from "../lib";

const TINT: Record<string, string> = {
  accent: "bg-accent/12 text-accent",
  up: "bg-up/12 text-up",
  down: "bg-down/12 text-down",
  warn: "bg-warn/12 text-warn",
};

export function Kpi({ label, value, icon, delta, deltaUp, tint = "accent" }: {
  label: string; value: React.ReactNode; icon?: React.ReactNode;
  delta?: string; deltaUp?: boolean; tint?: keyof typeof TINT;
}) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-card transition duration-200 hover:-translate-y-0.5 hover:border-accent/40">
      <div className="flex items-start justify-between">
        <div className="text-sm font-medium text-muted">{label}</div>
        {icon && (
          <span className={"grid h-10 w-10 place-items-center rounded-xl " + TINT[tint]}>
            {icon}
          </span>
        )}
      </div>
      <div className="mt-3 text-3xl font-extrabold tracking-tight text-ink">{value}</div>
      {delta && (
        <div className={"mt-1 text-sm font-semibold " + (deltaUp ? "text-up" : "text-down")}>
          {delta}
        </div>
      )}
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
    <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight">{title}</h1>
        <p className="mt-1.5 text-[0.95rem] text-muted">{subtitle}</p>
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
