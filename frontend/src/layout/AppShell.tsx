import { NavLink, Outlet } from "react-router-dom";

import { useLogout, useMe } from "../api/auth";
import { LanguageSwitcher } from "../i18n/LanguageSwitcher";
import { useTranslation } from "../i18n/LanguageContext";

const NAV_ITEMS = [
  { to: "/app/products", labelKey: "nav.products", perm: "catalog.view_product" },
  { to: "/app/inventory", labelKey: "nav.inventory", perm: "inventory.adjust_stock" },
  { to: "/app/stocktake", labelKey: "nav.stocktake", perm: "inventory.run_count" },
  { to: "/app/deliveries", labelKey: "nav.deliveries", perm: "suppliers.receive_delivery" },
  { to: "/app/suppliers", labelKey: "nav.suppliers", perm: "suppliers.receive_delivery" },
  { to: "/app/sell", labelKey: "nav.sell", perm: "orders.create_pos_order" },
];

function linkClasses(isActive: boolean) {
  return `block rounded px-3 py-2 text-sm font-medium ${
    isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-200"
  }`;
}

export default function AppShell() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const logout = useLogout();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white p-4">
        <div className="mb-6 flex items-center justify-between px-1">
          <span className="text-sm font-semibold text-slate-900">{t("nav.brand")}</span>
          <LanguageSwitcher />
        </div>
        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.filter((item) => me?.permissions.includes(item.perm)).map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClasses(isActive)}>
              {t(item.labelKey)}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-200 pt-3 text-xs text-slate-500">
          <div className="mb-2 truncate">{me?.user.email}</div>
          <button onClick={() => logout.mutate()} className="text-slate-600 underline hover:text-slate-900">
            {t("nav.sign_out")}
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
