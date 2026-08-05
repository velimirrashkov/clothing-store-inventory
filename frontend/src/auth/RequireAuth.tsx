import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useMe } from "../api/auth";
import { useTranslation } from "../i18n/LanguageContext";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const { data: me, isLoading } = useMe();
  const location = useLocation();

  if (isLoading) return <div className="p-8 text-slate-500">{t("common.loading")}</div>;
  if (!me) return <Navigate to="/app/login" state={{ from: location }} replace />;

  return <>{children}</>;
}

/**
 * Frontend guards are UX, not security — every endpoint re-checks server-side (§6.2, §9).
 * This just hides nav the user can't act on and gives a clear message instead of a raw 403.
 */
export function RequirePermission({ perm, children }: { perm: string; children: ReactNode }) {
  const { t } = useTranslation();
  const { data: me } = useMe();
  if (!me?.permissions.includes(perm)) {
    return <div className="p-8 text-slate-500">{t("nav.no_permission")}</div>;
  }
  return <>{children}</>;
}
