import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useLogin, useMe } from "../api/auth";
import { ApiError } from "../api/client";
import { LanguageSwitcher } from "../i18n/LanguageSwitcher";
import { useTranslation } from "../i18n/LanguageContext";

/** Separate staff login route (see architecture-spec.md §6.4) — mandatory MFA for staff is a
 * backend gap, not implemented yet, so this is a plain email/password form for now. */
export default function LoginPage() {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (me) {
    const from = (location.state as { from?: Location })?.from?.pathname ?? "/app/products";
    return <Navigate to={from} replace />;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    login.mutate(
      { email, password },
      {
        onSuccess: () => navigate("/app/products"),
        // Generic error text — never reveal whether the email exists (§6.4).
        onError: (err) => setError(err instanceof ApiError ? err.message : t("auth.generic_error")),
      },
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <form onSubmit={handleSubmit} className="w-80 space-y-4 rounded-lg bg-white p-8 shadow-sm">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-slate-900">{t("auth.sign_in_title")}</h1>
          <LanguageSwitcher />
        </div>
        <div className="space-y-1">
          <label htmlFor="email" className="text-sm font-medium text-slate-700">{t("auth.email")}</label>
          <input
            id="email"
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="password" className="text-sm font-medium text-slate-700">{t("auth.password")}</label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={login.isPending}
          className="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {login.isPending ? t("auth.signing_in") : t("auth.sign_in")}
        </button>
      </form>
    </div>
  );
}
