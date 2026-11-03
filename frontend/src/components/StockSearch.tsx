import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { SearchResult } from "../types";
import { Change } from "./ui";
import { inr } from "../utils/format";

interface Props {
  onSelect: (s: SearchResult) => void;
  placeholder?: string;
  isSelected?: (symbol: string) => boolean;
  actionLabel?: (symbol: string) => string;
}

export default function StockSearch({ onSelect, placeholder = "Search by company name or NSE symbol…", isSelected, actionLabel }: Props) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const term = q.trim();
    if (!term) { setResults([]); setErr(null); return; }
    setBusy(true);
    const t = setTimeout(async () => {
      try { setResults((await api.search(term)).results); setErr(null); }
      catch (e) { setErr(e instanceof Error ? e.message : "Search failed"); setResults([]); }
      finally { setBusy(false); }
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const close = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div ref={box} className="relative">
      <input className="input" value={q} placeholder={placeholder} aria-label="Search stocks"
        onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)} />
      {open && q.trim() && (
        <div className="absolute z-30 mt-1 max-h-80 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-lg">
          {busy && <div className="px-4 py-3 text-sm text-slate-500">Searching…</div>}
          {err && <div className="px-4 py-3 text-sm text-red-600">{err}</div>}
          {!busy && !err && results.length === 0 && <div className="px-4 py-3 text-sm text-slate-500">No NIFTY 50 stock matches “{q}”.</div>}
          {results.map((r) => (
            <button key={r.symbol} type="button" onClick={() => { onSelect(r); setOpen(false); setQ(""); }}
              className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-slate-50">
              <span className="min-w-0">
                <span className="block font-semibold text-slate-900">{r.symbol}</span>
                <span className="block truncate text-xs text-slate-500">{r.name} · {r.sector}</span>
              </span>
              <span className="shrink-0 text-right text-sm">
                <span className="block tabular-nums">{inr(r.price)}</span>
                <Change changePct={r.change_pct} className="text-xs" />
              </span>
              {actionLabel && (
                <span className={`shrink-0 rounded-md px-2 py-1 text-xs font-semibold ${isSelected?.(r.symbol) ? "bg-slate-100 text-slate-500" : "bg-brand-soft text-brand"}`}>
                  {actionLabel(r.symbol)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
