import { useCallback, useEffect, useRef, useState } from "react";

/** Fetches on mount / when deps change, then re-fetches every `intervalMs` (0 = no polling). */
export function usePolling<T>(fn: () => Promise<T>, intervalMs: number, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const run = useCallback(async (initial = false) => {
    if (initial) setLoading(true);
    try {
      setData(await fnRef.current());
      setError(null);
      setUpdatedAt(new Date());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setData(null);
    run(true);
    if (!intervalMs) return;
    const id = setInterval(() => run(false), intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, run, ...deps]);

  return { data, error, loading, updatedAt, reload: () => run(false) };
}
