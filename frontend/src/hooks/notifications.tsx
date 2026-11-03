import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { AppNotification } from "../types";

interface Ctx {
  items: AppNotification[]; unread: number; toast: AppNotification | null;
  refresh: () => Promise<void>; markAll: () => Promise<void>; markOne: (id: number) => Promise<void>;
  remove: (id: number) => Promise<void>; dismissToast: () => void;
}
const NotificationsCtx = createContext<Ctx | null>(null);
export const useNotifications = () => {
  const c = useContext(NotificationsCtx);
  if (!c) throw new Error("NotificationsProvider missing");
  return c;
};

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [toast, setToast] = useState<AppNotification | null>(null);
  const lastId = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const r = await api.notifications();
      setItems(r.items);
      setUnread(r.unread);
      const newest = r.items.reduce((m, n) => Math.max(m, n.id), 0);
      if (lastId.current !== null && newest > lastId.current) {
        const fresh = r.items.find((n) => n.id === newest && !n.is_read);
        if (fresh) setToast(fresh);
      }
      lastId.current = Math.max(newest, lastId.current ?? 0);
    } catch { /* backend offline: keep last state */ }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10_000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 8000);
    return () => clearTimeout(t);
  }, [toast]);

  const value: Ctx = {
    items, unread, toast, refresh,
    markAll: async () => { await api.readAll(); await refresh(); },
    markOne: async (id) => { await api.readOne(id); await refresh(); },
    remove: async (id) => { await api.deleteNotification(id); await refresh(); },
    dismissToast: () => setToast(null),
  };
  return <NotificationsCtx.Provider value={value}>{children}</NotificationsCtx.Provider>;
}
