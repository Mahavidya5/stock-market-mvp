export const inr = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const num = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : n.toLocaleString("en-IN", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const signed = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : (n > 0 ? "+" : "") + num(n, digits);

export const pct = (n: number | null | undefined) => (n == null ? "—" : `${n > 0 ? "+" : ""}${n.toFixed(2)}%`);

/** Values are in INR crore. */
export function crore(n: number | null | undefined): string {
  if (n == null) return "—";
  const a = Math.abs(n);
  if (a >= 1e5) return `₹${(n / 1e5).toFixed(2)} lakh Cr`;
  return `₹${Math.round(n).toLocaleString("en-IN")} Cr`;
}

export const volume = (n: number | null | undefined) => (n == null ? "—" : n.toLocaleString("en-IN"));

export const tone = (n: number | null | undefined) =>
  n == null || n === 0 ? "text-slate-500" : n > 0 ? "text-gain" : "text-loss";

export const shortDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short" });

export const dateTime = (iso: string) =>
  new Date(iso).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
