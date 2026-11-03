import { Link } from "react-router-dom";
import type { Quote } from "../types";
import { Change } from "./ui";
import { inr } from "../utils/format";

export default function StockTable({ quotes, title, accent }: { quotes: Quote[]; title: string; accent: "gain" | "loss" }) {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <span className={`h-2.5 w-2.5 rounded-full ${accent === "gain" ? "bg-gain" : "bg-loss"}`} />
        <h3 className="font-semibold text-slate-900">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[420px]">
          <thead className="bg-slate-50"><tr>
            <th className="th">Stock</th><th className="th text-right">Price</th><th className="th text-right">Change</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {quotes.map((q) => (
              <tr key={q.symbol} className="hover:bg-slate-50">
                <td className="td">
                  <Link to={`/stock/${encodeURIComponent(q.symbol)}`} className="block">
                    <div className="font-semibold text-slate-900">{q.symbol}</div>
                    <div className="max-w-[200px] truncate text-xs text-slate-500">{q.name}</div>
                  </Link>
                </td>
                <td className="td text-right font-medium tabular-nums">{inr(q.price)}</td>
                <td className="td text-right"><Change change={q.change} changePct={q.change_pct} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
