import { FormEvent, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import StockSearch from "../components/StockSearch";
import { DataBadge, ErrorBox, Spinner } from "../components/ui";
import { useNotifications } from "../hooks/notifications";
import { usePolling } from "../hooks/usePolling";
import type { Alert, Condition } from "../types";
import { dateTime, inr } from "../utils/format";

function status(a: Alert) {
  if (a.triggered_at) return { label: "Triggered", cls: "bg-blue-50 text-blue-700" };
  return a.enabled ? { label: "Active", cls: "bg-emerald-50 text-emerald-700" } : { label: "Disabled", cls: "bg-slate-100 text-slate-600" };
}

export default function Alerts() {
  const [params, setParams] = useSearchParams();
  const alerts = usePolling(() => api.alerts(), 15_000);
  const { items: notes, refresh: refreshNotes, remove } = useNotifications();
  const meta = usePolling(() => api.overview(), 0);

  const [symbol, setSymbol] = useState(params.get("symbol")?.toUpperCase() ?? "");
  const [condition, setCondition] = useState<Condition>("ABOVE");
  const [target, setTarget] = useState("");
  const [formErr, setFormErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [eCond, setECond] = useState<Condition>("ABOVE");
  const [eTarget, setETarget] = useState("");
  const [actionErr, setActionErr] = useState<string | null>(null);

  const cur = usePolling(async () => (symbol ? (await api.stock(symbol)).quote : null), 15_000, [symbol]);
  useEffect(() => { if (params.get("symbol")) setParams({}, { replace: true }); }, []); // eslint-disable-line

  async function create(e: FormEvent) {
    e.preventDefault();
    setFormErr(null);
    const price = Number(target);
    if (!symbol) return setFormErr("Select a stock first.");
    if (!Number.isFinite(price) || price <= 0) return setFormErr("Enter a target price greater than 0.");
    setSaving(true);
    try { await api.createAlert(symbol, condition, price); setTarget(""); await alerts.reload(); }
    catch (err) { setFormErr(err instanceof Error ? err.message : "Could not create alert"); }
    finally { setSaving(false); }
  }

  async function act(fn: () => Promise<unknown>) {
    setActionErr(null);
    try { await fn(); await alerts.reload(); await refreshNotes(); }
    catch (e) { setActionErr(e instanceof Error ? e.message : "Action failed"); }
  }

  async function saveEdit(a: Alert) {
    const price = Number(eTarget);
    if (!Number.isFinite(price) || price <= 0) return setActionErr("Target price must be greater than 0.");
    await act(() => api.updateAlert(a.id, { condition: eCond, target_price: price }));
    setEditing(null);
  }

  const list = alerts.data ?? [];
  const triggered = list.filter((a) => a.triggered_at);

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-xl font-bold text-slate-900">Price Alerts</h1><p className="text-sm text-slate-500">Get an in-app notification when a stock crosses your target.</p></div>
        {meta.data && <DataBadge mode={meta.data.data_mode} provider={meta.data.provider} />}
      </div>
      {meta.data?.data_mode === "demo" && (
        <div role="alert" className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-2.5 text-sm text-amber-900">
          Alerts are currently evaluated against <b>DEMO (simulated) prices</b>; notifications will be marked as demo.
        </div>
      )}

      <form onSubmit={create} className="card space-y-4 p-5">
        <h2 className="font-semibold text-slate-900">Create alert</h2>
        <div className="grid gap-4 md:grid-cols-[1.5fr_1fr_1fr_auto] md:items-end">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Stock</label>
            {symbol ? (
              <div className="flex items-center justify-between rounded-lg border border-slate-300 bg-slate-50 px-3 py-2">
                <span className="text-sm"><b>{symbol}</b>{cur.data && <span className="ml-2 text-slate-500">now {inr(cur.data.price)}</span>}</span>
                <button type="button" className="text-xs font-medium text-brand" onClick={() => setSymbol("")}>Change</button>
              </div>
            ) : <StockSearch onSelect={(s) => setSymbol(s.symbol)} placeholder="Search stock…" />}
          </div>
          <div>
            <label htmlFor="cond" className="mb-1 block text-xs font-medium text-slate-600">Condition</label>
            <select id="cond" className="input" value={condition} onChange={(e) => setCondition(e.target.value as Condition)}>
              <option value="ABOVE">Price rises above</option><option value="BELOW">Price falls below</option>
            </select>
          </div>
          <div>
            <label htmlFor="target" className="mb-1 block text-xs font-medium text-slate-600">Target price (₹)</label>
            <input id="target" className="input" inputMode="decimal" placeholder="e.g. 1500" value={target} onChange={(e) => setTarget(e.target.value)} />
          </div>
          <button className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create alert"}</button>
        </div>
        {formErr && <p role="alert" className="text-sm text-loss">{formErr}</p>}
      </form>

      {actionErr && <ErrorBox message={actionErr} />}

      <div className="card overflow-hidden">
        <div className="border-b border-slate-100 px-5 py-3 font-semibold text-slate-900">Your alerts</div>
        {alerts.loading && !alerts.data ? <Spinner /> : !alerts.data ? <div className="p-4"><ErrorBox message={alerts.error ?? "Failed to load"} onRetry={alerts.reload} /></div> : list.length === 0 ? (
          <div className="p-10 text-center text-slate-500">No alerts yet. Create one above.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px]">
              <thead className="bg-slate-50"><tr>
                <th className="th">Stock</th><th className="th">Condition</th><th className="th text-right">Target</th><th className="th text-right">Current</th><th className="th">Status</th><th className="th text-right">Actions</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {list.map((a) => {
                  const s = status(a);
                  const isEdit = editing === a.id;
                  return (
                    <tr key={a.id}>
                      <td className="td"><div className="font-semibold">{a.symbol}</div><div className="text-xs text-slate-500">{a.name}</div></td>
                      <td className="td">
                        {isEdit ? (
                          <select className="input !py-1" value={eCond} onChange={(e) => setECond(e.target.value as Condition)} aria-label="Edit condition">
                            <option value="ABOVE">Rises above</option><option value="BELOW">Falls below</option>
                          </select>
                        ) : a.condition === "ABOVE" ? "Rises above" : "Falls below"}
                      </td>
                      <td className="td text-right tabular-nums">
                        {isEdit ? <input className="input !py-1 text-right" value={eTarget} onChange={(e) => setETarget(e.target.value)} aria-label="Edit target price" /> : inr(a.target_price)}
                      </td>
                      <td className="td text-right tabular-nums">{inr(a.current_price)}</td>
                      <td className="td">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${s.cls}`}>{s.label}</span>
                        {a.triggered_at && <div className="mt-1 text-xs text-slate-500">{dateTime(a.triggered_at)} @ {inr(a.triggered_price)}</div>}
                      </td>
                      <td className="td">
                        <div className="flex justify-end gap-2">
                          {isEdit ? (<>
                            <button className="btn-primary !py-1" onClick={() => saveEdit(a)}>Save</button>
                            <button className="btn-ghost !py-1" onClick={() => setEditing(null)}>Cancel</button>
                          </>) : (<>
                            <button className="btn-ghost !py-1" onClick={() => act(() => api.updateAlert(a.id, { enabled: !a.enabled }))}>
                              {a.triggered_at ? "Re-arm" : a.enabled ? "Disable" : "Enable"}
                            </button>
                            <button className="btn-ghost !py-1" onClick={() => { setEditing(a.id); setECond(a.condition); setETarget(String(a.target_price)); }}>Edit</button>
                            <button className="btn-danger !py-1" onClick={() => window.confirm(`Delete the ${a.symbol} alert?`) && act(() => api.deleteAlert(a.id))}>Delete</button>
                          </>)}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <span className="font-semibold text-slate-900">Triggered alerts & notifications</span>
          <span className="text-xs text-slate-500">{triggered.length} triggered</span>
        </div>
        {notes.length === 0 ? <div className="p-8 text-center text-sm text-slate-500">Nothing has triggered yet.</div> : (
          <ul className="divide-y divide-slate-100">
            {notes.map((n) => (
              <li key={n.id} className="flex items-start justify-between gap-3 px-5 py-3">
                <div>
                  <div className="text-sm text-slate-800">{n.message}</div>
                  <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">{dateTime(n.created_at)}<DataBadge mode={n.data_mode} /></div>
                </div>
                <button className="text-xs text-slate-400 hover:text-loss" onClick={() => remove(n.id)} aria-label="Delete notification">Dismiss</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
