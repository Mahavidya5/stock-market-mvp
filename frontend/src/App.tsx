import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Alerts from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import StockDetail from "./pages/StockDetail";
import Watchlist from "./pages/Watchlist";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="watchlist" element={<Watchlist />} />
        <Route path="stock/:symbol" element={<StockDetail />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="*" element={<div className="card p-8 text-center text-slate-500">Page not found.</div>} />
      </Route>
    </Routes>
  );
}
