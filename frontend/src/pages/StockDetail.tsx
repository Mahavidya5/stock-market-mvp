import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import PriceChart from "../components/PriceChart";
import { Change, DataBadge, DemoBanner, ErrorBox, RangeTabs, Spinner, Stat } from "../components/ui";
import { usePolling } from "../hooks/usePolling";
import type { FinRow, RangeKey } from "../types";
import { crore, inr, num, pct, tone, volume } from "../utils/format";

export default function StockDetail() {
  const { symbol = "" } = useParams();
  const [range, setRange] = useState<RangeKey>("6M");
  const [period, setPeriod] = useState<"annual" | "quarterly">("annual");
  const [wlMsg, setWlMsg] = useState<string | null>(null);

  const stock = usePolling(() => api.stock(symbol), 30_000, [symbol]);
  const hist = usePolling(() => api.history(symbol, range), 0, [symbol, range]);
  const fund = usePolling(() => api.fundamentals(symbol), 0, [symbol]);
  const wl = usePolling(() => api.watchlist(), 0, []);
  const inWl = !!wl.data?.items.some((i) => i.symbol === symbol.toUpperCase());

  async function toggleWatch() {
    try {
      if (inWl) await api.removeWatch(symbol); else await api.addWatch(symbol);
      await wl.reload();
      setWlMsg(inWl ? "Removed from watchlist" : "Added to watchlist");
    } catch (e) { setWlMsg(e instanceof Error ? e.message : "Failed"); }
  }

  if (stock.loading && !stock.data) return <Spinner />;
  if (!stock.data) return <ErrorBox message={stock.error ?? "Stock not found"} onRetry={stock.reload} />;
  const { quote: q, profile, data_mode, provider } = stock.data;
  const f = fund.data;
  const rows: FinRow[] = (f && f.available ? (period === "annual" ? f.annual : f.quarterly) : []) ?? [];
  const latest = f?.annual?.[f.annual.length - 1];

  return (
    <>
      <Link to="/watchlist" className="text-sm text-slate-500 hover:text-brand">← Back</Link>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{profile.name}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate-500">
            <span className="rounded bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">NSE: {q.symbol}</span>
            {profile.sector && <span>{profile.sector}</span>}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <DataBadge mode={data_mode} provider={provider} />
          <button className={inWl ? "btn-ghost" : "btn-primary"} onClick={toggleWatch}>{inWl ? "★ In watchlist" : "☆ Add to watchlist"}</button>
          <Link className="btn-ghost" to={`/alerts?symbol=${encodeURIComponent(q.symbol)}`}>Set price alert</Link>
        </div>
      </div>
      {wlMsg && <p role="status" className="text-sm text-slate-600">{wlMsg}</p>}
      <DemoBanner mode={data_mode} />

      <div className="card p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-3xl font-bold tabular-nums text-slate-900">{inr(q.price)}</div>
            <Change change={q.change} changePct={q.change_pct} className="text-base" />
          </div>
          <RangeTabs value={range} onChange={setRange} />
        </div>
        <div className="mt-4">
          {hist.loading && !hist.data ? <Spinner /> : hist.data ? <PriceChart points={hist.data.points} label={q.symbol} height={300} /> : <ErrorBox message={hist.error ?? "No chart data"} onRetry={hist.reload} />}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
          <Stat label="Prev close" value={inr(q.prev_close)} />
          <Stat label="Open" value={inr(q.open)} />
          <Stat label="Day high" value={inr(q.high)} />
          <Stat label="Day low" value={inr(q.low)} />
          <Stat label="Volume" value={volume(q.volume)} />
        </div>
      </div>

      <div className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Company fundamentals</h2>
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5">
            {(["annual", "quarterly"] as const).map((p) => (
              <button key={p} onClick={() => setPeriod(p)} className={`rounded-md px-3 py-1 text-xs font-semibold capitalize ${period === p ? "bg-white text-brand shadow-sm" : "text-slate-500"}`}>{p}</button>
            ))}
          </div>
        </div>
        {fund.loading && !f ? <Spinner /> : !f ? <div className="mt-3"><ErrorBox message={fund.error ?? "Failed to load fundamentals"} onRetry={fund.reload} /></div> : !f.available ? (
          <p className="mt-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">{f.message}</p>
        ) : (
          <>
            {f.data_mode === "demo" && <p className="mt-2 text-xs font-semibold text-amber-700">DEMO: financials below are simulated.</p>}
            <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Stat label="Market capitalization" value={crore(f.market_cap)} />
              <Stat label={`Revenue (${latest?.period ?? "latest FY"})`} value={crore(latest?.revenue)}
                sub={latest && <span className={tone(latest.revenue_growth_pct)}>{pct(latest.revenue_growth_pct)} YoY</span>} />
              <Stat label={`Net profit (${latest?.period ?? "latest FY"})`} value={crore(latest?.net_profit)}
                sub={latest && <span className={tone(latest.profit_growth_pct)}>{pct(latest.profit_growth_pct)} YoY</span>} />
              <Stat label="P/E ratio" value={f.pe_ratio != null ? num(f.pe_ratio, 1) : "—"} />
            </div>

            {rows.length > 0 ? (
              <>
                <div className="mt-6 h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                      <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: "#64748b" }} width={56} tickFormatter={(v: number) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(v))} axisLine={false} tickLine={false} />
                      <Tooltip formatter={(v: number) => `₹${v.toLocaleString("en-IN")} Cr`} contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="revenue" name="Revenue (₹ Cr)" fill="#2563eb" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      <Bar dataKey="net_profit" name="Net profit (₹ Cr)" fill="#059669" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full min-w-[520px]">
                    <thead className="bg-slate-50"><tr>
                      <th className="th">Period</th><th className="th text-right">Revenue (₹ Cr)</th><th className="th text-right">Growth</th><th className="th text-right">Net profit (₹ Cr)</th><th className="th text-right">Growth</th>
                    </tr></thead>
                    <tbody className="divide-y divide-slate-100">
                      {[...rows].reverse().map((r) => (
                        <tr key={r.period}>
                          <td className="td font-medium">{r.period}</td>
                          <td className="td text-right tabular-nums">{r.revenue.toLocaleString("en-IN")}</td>
                          <td className={`td text-right tabular-nums ${tone(r.revenue_growth_pct)}`}>{pct(r.revenue_growth_pct)}</td>
                          <td className="td text-right tabular-nums">{r.net_profit.toLocaleString("en-IN")}</td>
                          <td className={`td text-right tabular-nums ${tone(r.profit_growth_pct)}`}>{pct(r.profit_growth_pct)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : <p className="mt-4 text-sm text-slate-500">No {period} statements available.</p>}
          </>
        )}
      </div>

      <div className="card p-5">
        <h2 className="text-lg font-semibold text-slate-900">About {profile.name}</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">{profile.description ?? "No company description available from the data provider."}</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          {[["Exchange", profile.exchange], ["Sector", profile.sector], ["CEO", profile.ceo], ["Employees", profile.employees?.toLocaleString("en-IN")]].map(([k, v]) => (
            <div key={k as string}><dt className="text-xs text-slate-500">{k}</dt><dd className="font-medium text-slate-800">{v || "—"}</dd></div>
          ))}
        </dl>
        {profile.website && <a className="mt-3 inline-block text-sm text-brand hover:underline" href={profile.website} target="_blank" rel="noreferrer">{profile.website}</a>}
      </div>
    </>
  );
}
