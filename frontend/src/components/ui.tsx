import type { DataMode, MarketStatus as Status, RangeKey } from "../types";
import { pct, signed, tone } from "../utils/format";

const MODES: Record<DataMode, { label: string; cls: string; hint: string }> = {
  live: { label: "LIVE", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", hint: "Real-time market data" },
  delayed: { label: "DELAYED", cls: "bg-sky-50 text-sky-700 border-sky-200", hint: "Real market data, delayed by the provider (typically ~15 min)" },
  demo: { label: "DEMO DATA", cls: "bg-amber-50 text-amber-800 border-amber-300", hint: "Simulated sample data - NOT real market prices" },
};

export function DataBadge({ mode, provider }: { mode: DataMode; provider?: string }) {
  const m = MODES[mode];
  return (
    <span title={`${m.hint}${provider ? ` — ${provider}` : ""}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold tracking-wide ${m.cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current ${mode === "live" ? "animate-pulse" : ""}`} />
      {m.label}
    </span>
  );
}

export function DemoBanner({ mode }: { mode: DataMode }) {
  if (mode !== "demo") return null;
  return (
    <div role="alert" className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">
      <b>DEMO DATA:</b> prices, charts and financials shown are simulated and are not real NSE market data.
      Add a market-data API key in the backend <code className="rounded bg-amber-100 px-1">.env</code> to switch to real data.
    </div>
  );
}

export function MarketStatusPill({ status }: { status: Status }) {
  const cls = status.state === "open" ? "bg-emerald-50 text-emerald-700" : status.state === "pre_open" ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-600";
  return (
    <span title={`IST ${status.time_ist}. ${status.note}`} className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>
      <span className={`h-2 w-2 rounded-full ${status.state === "open" ? "bg-emerald-500" : status.state === "pre_open" ? "bg-amber-500" : "bg-slate-400"}`} />
      {status.label}
    </span>
  );
}

export function Change({ change, changePct, className = "" }: { change?: number | null; changePct: number | null; className?: string }) {
  const up = (changePct ?? 0) > 0, down = (changePct ?? 0) < 0;
  return (
    <span className={`inline-flex items-center gap-1 font-medium tabular-nums ${tone(changePct)} ${className}`}>
      <span aria-hidden>{up ? "▲" : down ? "▼" : "•"}</span>
      {change !== undefined && <span>{signed(change)}</span>}
      <span>({pct(changePct)})</span>
    </span>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <span>{message}</span>
      {onRetry && <button className="btn-ghost !py-1" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export const Spinner = ({ label = "Loading…" }: { label?: string }) => (
  <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-500">
    <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand" />{label}
  </div>
);

export function RangeTabs({ value, onChange }: { value: RangeKey; onChange: (r: RangeKey) => void }) {
  return (
    <div className="inline-flex rounded-lg bg-slate-100 p-0.5" role="tablist">
      {(["1W", "1M", "3M", "6M", "1Y"] as RangeKey[]).map((r) => (
        <button key={r} role="tab" aria-selected={value === r} onClick={() => onChange(r)}
          className={`rounded-md px-2.5 py-1 text-xs font-semibold transition ${value === r ? "bg-white text-brand shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
          {r}
        </button>
      ))}
    </div>
  );
}

export const Stat = ({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) => (
  <div className="rounded-lg bg-slate-50 px-4 py-3">
    <div className="text-xs font-medium text-slate-500">{label}</div>
    <div className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">{value}</div>
    {sub && <div className="text-xs">{sub}</div>}
  </div>
);
