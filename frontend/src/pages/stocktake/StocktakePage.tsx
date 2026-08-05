import { useState } from "react";

import {
  useCloseCount,
  useOpenCount,
  useReopenCount,
  useStockCount,
  useStockCounts,
  useSubmitCountLine,
  useSubmitCountLinesBulk,
} from "../../api/inventory";
import { ApiError } from "../../api/client";
import { useTranslation } from "../../i18n/LanguageContext";

export default function StocktakePage() {
  const { t } = useTranslation();
  const { data: openCounts } = useStockCounts("open");
  const { data: closedCounts } = useStockCounts("closed");
  const openCount = useOpenCount();
  const [selectedCountId, setSelectedCountId] = useState<number | null>(null);

  return (
    <div className="flex h-screen">
      <div className="w-64 shrink-0 border-r border-slate-200 bg-white p-3">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-slate-900">{t("stocktake.title")}</h1>
          <button
            onClick={() => openCount.mutate(undefined, { onSuccess: (count) => setSelectedCountId(count.id) })}
            disabled={openCount.isPending}
            className="rounded bg-slate-900 px-2 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {t("stocktake.open_new")}
          </button>
        </div>

        <p className="mb-1 text-xs font-medium text-slate-500">{t("stocktake.open")}</p>
        <ul className="mb-4 space-y-0.5">
          {openCounts?.map((count) => (
            <li key={count.id}>
              <button
                onClick={() => setSelectedCountId(count.id)}
                className={`block w-full rounded px-2 py-1 text-left text-sm ${
                  selectedCountId === count.id ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                {t("stocktake.count_number")}{count.id} — {new Date(count.started_at).toLocaleDateString()}
              </button>
            </li>
          ))}
          {openCounts?.length === 0 && <li className="px-2 text-xs text-slate-400">{t("stocktake.none_open")}</li>}
        </ul>

        <p className="mb-1 text-xs font-medium text-slate-500">{t("stocktake.closed")}</p>
        <ul className="space-y-0.5">
          {closedCounts?.slice(0, 10).map((count) => (
            <li key={count.id}>
              <button
                onClick={() => setSelectedCountId(count.id)}
                className={`block w-full rounded px-2 py-1 text-left text-sm ${
                  selectedCountId === count.id ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100"
                }`}
              >
                {t("stocktake.count_number")}{count.id} — {count.closed_at && new Date(count.closed_at).toLocaleDateString()}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1 overflow-auto">
        {selectedCountId ? (
          <CountDetail countId={selectedCountId} />
        ) : (
          <p className="p-8 text-sm text-slate-500">{t("stocktake.select_prompt")}</p>
        )}
      </div>
    </div>
  );
}

function CountDetail({ countId }: { countId: number }) {
  const { t } = useTranslation();
  const { data: count, isLoading } = useStockCount(countId);
  const submitLine = useSubmitCountLine(countId);
  const submitBulk = useSubmitCountLinesBulk(countId);
  const closeCount = useCloseCount();
  const reopenCount = useReopenCount();
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !count) return <div className="p-8 text-slate-500">{t("common.loading")}</div>;

  const uncountedRemaining = count.lines.filter((l) => l.counted === null).length;

  // Every line with a valid draft that differs from what's already saved — "Submit all" only
  // sends what actually changed, so re-clicking after a partial save is always safe.
  const pendingChanges = count.lines
    .map((line) => {
      const draft = drafts[line.id];
      if (draft === undefined || draft === "") return null;
      const counted = parseInt(draft, 10);
      if (Number.isNaN(counted) || counted < 0 || counted === line.counted) return null;
      return { variant_id: line.variant, counted };
    })
    .filter((x): x is { variant_id: number; counted: number } => x !== null);

  function submitAll() {
    setError(null);
    submitBulk.mutate(pendingChanges, {
      onSuccess: () => setDrafts({}),
      onError: (err) => setError(err instanceof ApiError ? err.message : t("stocktake.error_submit")),
    });
  }

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{t("stocktake.count_number")}{count.id}</h2>
          <p className="text-sm text-slate-500">
            {t(`stocktake.${count.status}`)} · {count.lines.length} {t("stocktake.lines")} · {uncountedRemaining} {t("stocktake.not_yet_counted")}
          </p>
        </div>
        <div className="flex gap-2">
          {count.status === "open" && (
            <>
              <button
                onClick={submitAll}
                disabled={pendingChanges.length === 0 || submitBulk.isPending}
                className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-50"
              >
                {submitBulk.isPending
                  ? t("stocktake.submitting")
                  : `${t("stocktake.submit_all")}${pendingChanges.length ? ` (${pendingChanges.length})` : ""}`}
              </button>
              <button
                onClick={() => closeCount.mutate(count.id)}
                disabled={closeCount.isPending}
                className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {t("stocktake.close_count")}
              </button>
            </>
          )}
          {count.status === "closed" && (
            <button
              onClick={() => reopenCount.mutate(count.id)}
              disabled={reopenCount.isPending}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100 disabled:opacity-50"
              title={t("stocktake.reopen_title")}
            >
              {reopenCount.isPending ? t("stocktake.reopening") : t("stocktake.reopen")}
            </button>
          )}
        </div>
      </div>
      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="py-1 pr-2">{t("products.col_sku")}</th>
            <th className="py-1 pr-2">{t("stocktake.col_expected")}</th>
            <th className="py-1 pr-2">{t("stocktake.col_counted")}</th>
            <th className="py-1"></th>
          </tr>
        </thead>
        <tbody>
          {count.lines.map((line) => {
            const draft = drafts[line.id] ?? (line.counted !== null ? String(line.counted) : "");
            const discrepancy = line.counted !== null && line.counted !== line.expected;
            return (
              <tr key={line.id} className="border-b border-slate-100">
                <td className="py-1.5 pr-2 font-mono text-xs">{line.sku}</td>
                <td className="py-1.5 pr-2">{line.expected}</td>
                <td className="py-1.5 pr-2">
                  {count.status === "open" ? (
                    <input
                      value={draft}
                      onChange={(e) => setDrafts((d) => ({ ...d, [line.id]: e.target.value }))}
                      className="w-20 rounded border border-slate-300 px-2 py-0.5 text-sm"
                    />
                  ) : (
                    line.counted ?? "—"
                  )}
                </td>
                <td className="py-1.5">
                  {count.status === "open" && draft !== "" && (
                    <button
                      onClick={() => {
                        setError(null);
                        const counted = parseInt(draft, 10);
                        if (Number.isNaN(counted) || counted < 0) {
                          setError(t("stocktake.error_whole_number"));
                          return;
                        }
                        submitLine.mutate(
                          { variant_id: line.variant, counted },
                          {
                            onSuccess: () => setDrafts((d) => { const next = { ...d }; delete next[line.id]; return next; }),
                            onError: (err) => setError(err instanceof ApiError ? err.message : t("stocktake.error_submit_line")),
                          },
                        );
                      }}
                      className="text-xs text-slate-600 underline hover:text-slate-900"
                    >
                      {t("stocktake.submit")}
                    </button>
                  )}
                  {discrepancy && <span className="ml-2 text-xs text-amber-700">{t("stocktake.discrepancy")}</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
