import type {
  Alert, AppNotification, Condition, Fundamentals, HistoryResp, Overview, RangeKey, SearchResult, StockDetail, WatchItem, Meta,
} from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new ApiError("Cannot reach the backend. Is the API server running?");
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch { /* ignore */ }
    throw new ApiError(detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

const sym = (s: string) => encodeURIComponent(s);
const json = (method: string, body?: unknown): RequestInit => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  overview: () => req<Overview>("/api/market/overview"),
  indexHistory: (range: RangeKey) => req<HistoryResp>(`/api/market/index/history?range=${range}`),
  search: (q: string) => req<Meta & { results: SearchResult[] }>(`/api/stocks/search?q=${encodeURIComponent(q)}`),
  stock: (s: string) => req<StockDetail>(`/api/stocks/${sym(s)}`),
  history: (s: string, range: RangeKey) => req<HistoryResp>(`/api/stocks/${sym(s)}/history?range=${range}`),
  fundamentals: (s: string) => req<Fundamentals>(`/api/stocks/${sym(s)}/fundamentals`),
  watchlist: () => req<Meta & { items: WatchItem[] }>("/api/watchlist"),
  addWatch: (symbol: string) => req<{ symbol: string }>("/api/watchlist", json("POST", { symbol })),
  removeWatch: (s: string) => req<void>(`/api/watchlist/${sym(s)}`, json("DELETE")),
  alerts: () => req<Alert[]>("/api/alerts"),
  createAlert: (symbol: string, condition: Condition, target_price: number) =>
    req<Alert>("/api/alerts", json("POST", { symbol, condition, target_price })),
  updateAlert: (id: number, patch: { condition?: Condition; target_price?: number; enabled?: boolean }) =>
    req<Alert>(`/api/alerts/${id}`, json("PUT", patch)),
  deleteAlert: (id: number) => req<void>(`/api/alerts/${id}`, json("DELETE")),
  notifications: () => req<{ unread: number; items: AppNotification[] }>("/api/notifications"),
  readAll: () => req<void>("/api/notifications/read-all", json("POST")),
  readOne: (id: number) => req<void>(`/api/notifications/${id}/read`, json("POST")),
  deleteNotification: (id: number) => req<void>(`/api/notifications/${id}`, json("DELETE")),
};
