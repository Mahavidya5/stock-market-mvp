import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import StockSearch from "../components/StockSearch";
import { Change, DataBadge, DemoBanner, ErrorBox, Spinner } from "../components/ui";
import { usePolling } from "../hooks/usePolling";
import { inr } from "../utils/format";

export default function Watchlist() {
  const wl = usePolling(() => api.watchlist(), 30_000);
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const d = wl.data;
  const has = (s: string) => !!d?.items.some((i) => i.symbol === s);

  async function add(symbol: string) {
    if (has(symbol)) { setMsg({ type: "err", text: `${symbol} is already in your watchlist.` }); return; }
    try { await api.addWatch(symbol); setMsg({ type: "ok", text: `${symbol} added to watchlist.` }); await wl.reload(); }
    catch (e) { setMsg({ type: "err", text: e instanceof Error ? e.message : "Could not add stock" }); }
  }
  async function remove(symbol: string) {
    try { await api.removeWatch(symbol); setMsg({ type: "ok", text: `${symbol} removed.` }); await wl.reload(); }
    catch (e) { setMsg({ type: "err", text: e instanceof Error ? e.message : "Could not remove stock" }); }
  }

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-xl font-bold text-slate-900">Watchlist</h1><p className="text-sm text-slate-500">Search NIFTY 50 stocks and track them here.</p></div>
        {d && <DataBadge mode={d.data_mode} provider={d.provider} />}
      </div>
      {d && <DemoBanner mode={d.data_mode} />}

      <div className="card p-4">
        <StockSearch onSelect={(s) => add(s.symbol)} isSelected={has} actionLabel={(s) => (has(s) ? "In watchlist" : "+ Add")} />
        {msg && <p role="status" className={`mt-2 text-sm ${msg.type === "ok" ? "text-gain" : "text-loss"}`}>{msg.text}</p>}
      </div>

      {wl.loading && !d ? <Spinner /> : !d ? <ErrorBox message={wl.error ?? "Failed to load watchlist"} onRetry={wl.reload} /> : (
        <>
          {wl.error && <ErrorBox message={`Refresh failed: ${wl.error}`} onRetry={wl.reload} />}
          {d.items.length === 0 ? (
            <div className="card p-10 text-center text-slate-500">Your watchlist is empty. Search above to add your first stock.</div>
          ) : (
            <div className="card overflow-x-auto">
              <table className="w-full min-w-[560px]">
                <thead className="bg-slate-50"><tr>
                  <th className="th">Stock</th><th className="th text-right">Price</th><th className="th text-right">Day change</th><th className="th text-right">Actions</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {d.items.map((i) => (
                    <tr key={i.symbol} className="hover:bg-slate-50">
                      <td className="td">
                        <Link to={`/stock/${encodeURIComponent(i.symbol)}`} className="block">
                          <div className="font-semibold text-slate-900">{i.symbol}</div><div className="text-xs text-slate-500">{i.name}</div>
                        </Link>
                      </td>
                      <td className="td text-right font-medium tabular-nums">{i.quote ? inr(i.quote.price) : "—"}</td>
                      <td className="td text-right">{i.quote ? <Change change={i.quote.change} changePct={i.quote.change_pct} /> : <span className="text-xs text-slate-400">Quote unavailable</span>}</td>
                      <td className="td">
                        <div className="flex justify-end gap-2">
                          <Link className="btn-ghost !py-1" to={`/stock/${encodeURIComponent(i.symbol)}`}>Details</Link>
                          <Link className="btn-ghost !py-1" to={`/alerts?symbol=${encodeURIComponent(i.symbol)}`}>Alert</Link>
                          <button className="btn-danger !py-1" onClick={() => remove(i.symbol)} aria-label={`Remove ${i.symbol}`}>Remove</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </>
  );
}
