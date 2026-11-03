import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import NotificationBell from "./NotificationBell";
import { useNotifications } from "../hooks/notifications";

const NAV = [
  { to: "/", label: "Dashboard", d: "M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z" },
  { to: "/watchlist", label: "Watchlist", d: "M12 17.3l-6.2 3.7 1.6-7L2 9.2l7.2-.6L12 2l2.8 6.6 7.2.6-5.4 4.8 1.6 7z" },
  { to: "/alerts", label: "Price Alerts", d: "M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0" },
];

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="space-y-1">
      {NAV.map((n) => (
        <NavLink key={n.to} to={n.to} end={n.to === "/"} onClick={onNavigate}
          className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${isActive ? "bg-brand-soft text-brand" : "text-slate-600 hover:bg-slate-100"}`}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={n.d} /></svg>
          {n.label}
        </NavLink>
      ))}
    </nav>
  );
}

const Brand = () => (
  <div className="flex items-center gap-2.5 px-2">
    <div className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-white">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" /></svg>
    </div>
    <div className="leading-tight"><div className="font-bold text-slate-900">NSE Markets</div><div className="text-[11px] text-slate-500">Phase 1 · India</div></div>
  </div>
);

export default function Layout() {
  const [drawer, setDrawer] = useState(false);
  const { toast, dismissToast } = useNotifications();
  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white p-4 md:block">
        <div className="sticky top-4 space-y-8"><Brand /><Nav /></div>
      </aside>

      {drawer && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setDrawer(false)} />
          <aside className="absolute left-0 top-0 h-full w-64 space-y-8 bg-white p-4 shadow-xl"><Brand /><Nav onNavigate={() => setDrawer(false)} /></aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur md:justify-end">
          <button className="btn-ghost !px-2.5 md:hidden" onClick={() => setDrawer(true)} aria-label="Open menu">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
          </button>
          <span className="font-bold text-slate-900 md:hidden">NSE Markets</span>
          <NotificationBell />
        </header>
        <main className="mx-auto max-w-6xl space-y-5 p-4 md:p-6"><Outlet /></main>
      </div>

      {toast && (
        <div role="status" className="fixed bottom-4 right-4 z-50 w-[min(92vw,24rem)] rounded-xl border border-blue-200 bg-white p-4 shadow-xl">
          <div className="flex items-start justify-between gap-3">
            <div><div className="text-sm font-semibold text-brand">Price alert triggered</div><div className="mt-1 text-sm text-slate-700">{toast.message}</div></div>
            <button onClick={dismissToast} aria-label="Dismiss" className="text-slate-400 hover:text-slate-600">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}
