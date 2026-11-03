export type DataMode = "demo" | "delayed" | "live";
export type Condition = "ABOVE" | "BELOW";
export type RangeKey = "1W" | "1M" | "3M" | "6M" | "1Y";

export interface Meta { data_mode: DataMode; provider: string; refresh_seconds: number }
export interface Quote {
  symbol: string; name: string; price: number; prev_close: number; change: number; change_pct: number;
  open: number | null; high: number | null; low: number | null; volume: number | null; as_of: string | null;
}
export interface MarketStatus { state: "open" | "closed" | "pre_open"; is_open: boolean; label: string; time_ist: string; note: string }
export interface Overview extends Meta {
  status: MarketStatus; index: Quote | null; index_error?: string | null; gainers: Quote[]; losers: Quote[];
  advancers: number; decliners: number; sectors: { sector: string; change_pct: number }[];
}
export interface Point { date: string; close: number }
export interface HistoryResp extends Meta { symbol?: string; range: RangeKey; points: Point[] }
export interface SearchResult { symbol: string; name: string; sector: string; price: number | null; change_pct: number | null }
export interface Profile { name: string; sector: string | null; exchange: string; description: string | null; website?: string | null; employees?: number | null; ceo?: string | null }
export interface StockDetail extends Meta { quote: Quote; profile: Profile }
export interface FinRow { period: string; revenue: number; net_profit: number; revenue_growth_pct: number | null; profit_growth_pct: number | null }
export interface Fundamentals extends Meta {
  symbol: string; available: boolean; message?: string;
  market_cap?: number | null; pe_ratio?: number | null; annual?: FinRow[]; quarterly?: FinRow[];
}
export interface WatchItem { symbol: string; name: string; added_at: string; quote: Quote | null }
export interface Alert {
  id: number; symbol: string; name: string | null; condition: Condition; target_price: number; enabled: boolean;
  triggered_at: string | null; triggered_price: number | null; current_price: number | null; created_at: string;
}
export interface AppNotification {
  id: number; alert_id: number | null; symbol: string; message: string; price: number; data_mode: DataMode; is_read: boolean; created_at: string;
}
