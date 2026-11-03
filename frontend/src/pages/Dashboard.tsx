import { useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import PriceChart from "../components/PriceChart";
import StockTable from "../components/StockTable";
import { Change, DataBadge, DemoBanner, ErrorBox, MarketStatusPill, RangeTabs, Spinner } from "../components/ui";
import { usePolling } from "../hooks/usePolling";
import type { RangeKey } from "../types";
import { num } from "../utils/format";

export default function Dashboard() {
  const [range, setRange] = useState<RangeKey>("1M");
  const [interval, setIntervalMs] = useState(30_000);
  const ov = usePolling(async () => {
    const d = await api.overview();
    setIntervalMs(d.refresh_seconds * 1000);
    return d;
  }, interval);
  const hist = usePolling(() => api.indexHistory(range), 120_000, [range]);
  const d = ov.data;

  if (ov.loading && !d) return <Spinner label="Loading market data…" />;
  if (!d) return <ErrorBox message={ov.error ?? "Unable to load market data"} onRetry={ov.reload} />;

  const idx = d.index;
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Market Dashboard</h1>
          <p className="text-sm text-slate-500">
            NSE · refreshes every {d.refresh_seconds}s{ov.updatedAt && ` · updated ${ov.updatedAt.toLocaleTimeString("en-IN")}`}
          </p>
        </div>
        <div className="flex items-center gap-2"><MarketStatusPill status={d.status} /><DataBadge mode={d.data_mode} provider={d.provider} /></div>
      </div>
      <DemoBanner mode={d.data_mode} />
      {ov.error && <ErrorBox message={`Refresh failed: ${ov.error} (showing last data)`} onRetry={ov.reload} />}

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-slate-500">NIFTY 50{d.data_mode === "demo" && " (simulated)"}</div>
              {idx ? (<>
                <div className="mt-1 text-3xl font-bold tabular-nums text-slate-900">{num(idx.price)}</div>
                <Change change={idx.change} changePct={idx.change_pct} className="text-base" />
                <div className="mt-1 text-xs text-slate-500">Prev close {num(idx.prev_close)}{d.data_mode === "delayed" && " · delayed"}</div>
              </>) : (
                <div className="mt-2 text-sm text-amber-700">{d.index_error ?? "Index value not available"}</div>
              )}
            </div>
            <RangeTabs value={range} onChange={setRange} />
          </div>
          <div className="mt-4">
            {hist.loading && !hist.data ? <Spinner /> : hist.error && !hist.data ? <ErrorBox message={hist.error} onRetry={hist.reload} /> : <PriceChart points={hist.data!.points} label="NIFTY 50" height={280} />}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-slate-900">Market breadth</h3>
          <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-slate-100">
            <div className="bg-gain" style={{ width: `${(d.advancers / Math.max(1, d.advancers + d.decliners)) * 100}%` }} />
            <div className="bg-loss flex-1" />
          </div>
          <div className="mt-2 flex justify-between text-sm">
            <span className="font-medium text-gain">{d.advancers} advancing</span>
            <span className="font-medium text-loss">{d.decliners} declining</span>
          </div>
          <h3 className="mb-1 mt-6 font-semibold text-slate-900">Sector performance</h3>
          <div style={{ height: Math.max(220, d.sectors.length * 26) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={d.sectors} layout="vertical" margin={{ left: 0, right: 12, top: 4, bottom: 0 }}>
                <XAxis type="number" hide domain={["auto", "auto"]} />
                <YAxis type="category" dataKey="sector" width={110} tick={{ fontSize: 11, fill: "#475569" }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: number) => [`${v > 0 ? "+" : ""}${v}%`, "Avg change"]} cursor={{ fill: "#f1f5f9" }} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="change_pct" radius={3} isAnimationActive={false}>
                  {d.sectors.map((s) => <Cell key={s.sector} fill={s.change_pct >= 0 ? "#059669" : "#dc2626"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <StockTable title="Top 5 Gainers" quotes={d.gainers} accent="gain" />
        <StockTable title="Top 5 Losers" quotes={d.losers} accent="loss" />
      </div>
      <p className="text-xs text-slate-500">Gainers/losers are ranked across the NIFTY 50 constituents. Provider: {d.provider}.</p>
    </>
  );
}
