import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useNotifications } from "../hooks/notifications";
import { dateTime } from "../utils/format";

export default function NotificationBell() {
  const { items, unread, markAll, markOne } = useNotifications();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const close = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button className="btn-ghost relative !px-2.5" onClick={() => setOpen((o) => !o)} aria-label={`Notifications (${unread} unread)`}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0" /></svg>
        {unread > 0 && <span className="absolute -right-1 -top-1 min-w-[18px] rounded-full bg-loss px-1 text-center text-[11px] font-bold leading-[18px] text-white">{unread > 9 ? "9+" : unread}</span>}
      </button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-[min(92vw,22rem)] overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
            <span className="font-semibold">Notifications</span>
            <button className="text-xs font-medium text-brand disabled:text-slate-400" disabled={!unread} onClick={markAll}>Mark all read</button>
          </div>
          <div className="max-h-80 divide-y divide-slate-100 overflow-auto">
            {items.length === 0 && <div className="px-4 py-6 text-center text-sm text-slate-500">No notifications yet. Triggered price alerts appear here.</div>}
            {items.slice(0, 15).map((n) => (
              <button key={n.id} onClick={() => !n.is_read && markOne(n.id)} className={`block w-full px-4 py-3 text-left hover:bg-slate-50 ${n.is_read ? "" : "bg-blue-50/50"}`}>
                <div className="flex items-start gap-2">
                  {!n.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand" />}
                  <div>
                    <div className="text-sm text-slate-800">{n.message}</div>
                    <div className="mt-0.5 text-xs text-slate-500">{dateTime(n.created_at)}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
          <Link to="/alerts" onClick={() => setOpen(false)} className="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-brand hover:bg-slate-50">Manage alerts</Link>
        </div>
      )}
    </div>
  );
}
