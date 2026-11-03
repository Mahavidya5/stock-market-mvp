import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Point } from "../types";
import { num, shortDate } from "../utils/format";

export default function PriceChart({ points, height = 260, label = "Close" }: { points: Point[]; height?: number; label?: string }) {
  if (points.length < 2) return <div className="py-10 text-center text-sm text-slate-500">Not enough data to chart.</div>;
  const up = points[points.length - 1].close >= points[0].close;
  const color = up ? "#059669" : "#dc2626";
  const id = `grad-${up ? "up" : "down"}`;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.25} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="date" tickFormatter={shortDate} tick={{ fontSize: 11, fill: "#64748b" }} minTickGap={32} axisLine={false} tickLine={false} />
        <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#64748b" }} width={64} tickFormatter={(v: number) => num(v, 0)} axisLine={false} tickLine={false} />
        <Tooltip formatter={(v: number) => [num(v), label]} labelFormatter={(d: string) => new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }} />
        <Area type="monotone" dataKey="close" stroke={color} strokeWidth={2} fill={`url(#${id})`} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
