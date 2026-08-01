import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

import LoginPage from "./auth/LoginPage";
import { RequireAuth, RequirePermission } from "./auth/RequireAuth";
import AppShell from "./layout/AppShell";
import InventoryPage from "./pages/inventory/InventoryPage";
import ProductsPage from "./pages/products/ProductsPage";
import SellPage from "./pages/sell/SellPage";
import StocktakePage from "./pages/stocktake/StocktakePage";

// One React app, two route trees (see architecture-spec.md §3) — `/app/*` is the back-office,
// lazy-loadable as its own chunk later. There's no storefront tree yet (Phase 2), so `/` just
// points here for now.
export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/app/products" replace />} />
        <Route path="/app/login" element={<LoginPage />} />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="products" replace />} />
          <Route path="products" element={<ProductsPage />} />
          <Route
            path="inventory"
            element={
              <RequirePermission perm="inventory.adjust_stock">
                <InventoryPage />
              </RequirePermission>
            }
          />
          <Route
            path="stocktake"
            element={
              <RequirePermission perm="inventory.run_count">
                <StocktakePage />
              </RequirePermission>
            }
          />
          <Route
            path="sell"
            element={
              <RequirePermission perm="orders.create_pos_order">
                <SellPage />
              </RequirePermission>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/app/products" replace />} />
      </Routes>
    </Router>
  );
}
