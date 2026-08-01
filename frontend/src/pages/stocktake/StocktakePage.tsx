import { useState } from "react";

import { useCloseCount, useOpenCount, useStockCount, useStockCounts, useSubmitCountLine } from "../../api/inventory";
import { ApiError } from "../../api/client";

export default function StocktakePage() {
  const { data: openCounts } = useStockCounts("open");
  const { data: closedCounts } = useStockCounts("closed");
  const openCount = useOpenCount();
  const [selectedCountId, setSelectedCountId] = useState<number | null>(null);

  return (
    <div className="flex h-screen">
      <div className="w-64 shrink-0 border-r border-slate-200 bg-white p-3">
        <div className="mb-3 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-slate-900">Stocktakes</h1>
          <button
            onClick={() => openCount.mutate(undefined, { onSuccess: (count) => setSelectedCountId(count.id) })}
            disabled={openCount.isPending}
            className="rounded bg-slate-900 px-2 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Open new
          </button>
        </div>

        <p className="mb-1 text-xs font-medium text-slate-500">Open</p>
        <ul className="mb-4 space-y-0.5">
          {openCounts?.map((count) => (
            <li key={count.id}>
              <button
                onClick={() => setSelectedCountId(count.id)}
                className={`block w-full rounded px-2 py-1 text-left text-sm ${
                  selectedCountId === count.id ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                Count #{count.id} — {new Date(count.started_at).toLocaleDateString()}
              </button>
            </li>
          ))}
          {openCounts?.length === 0 && <li className="px-2 text-xs text-slate-400">None open</li>}
        </ul>

        <p className="mb-1 text-xs font-medium text-slate-500">Closed</p>
        <ul className="space-y-0.5">
          {closedCounts?.slice(0, 10).map((count) => (
            <li key={count.id}>
              <button
                onClick={() => setSelectedCountId(count.id)}
                className={`block w-full rounded px-2 py-1 text-left text-sm ${
                  selectedCountId === count.id ? "bg-slate-900 text-white" : "text-slate-500 hover:bg-slate-100"
                }`}
              >
                Count #{count.id} — {count.closed_at && new Date(count.closed_at).toLocaleDateString()}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1 overflow-auto">
        {selectedCountId ? (
          <CountDetail countId={selectedCountId} />
        ) : (
          <p className="p-8 text-sm text-slate-500">Open a new stocktake or select one from the list.</p>
        )}
      </div>
    </div>
  );
}

function CountDetail({ countId }: { countId: number }) {
  const { data: count, isLoading } = useStockCount(countId);
  const submitLine = useSubmitCountLine(countId);
  const closeCount = useCloseCount();
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !count) return <div className="p-8 text-slate-500">Loading…</div>;

  const uncountedRemaining = count.lines.filter((l) => l.counted === null).length;

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Count #{count.id}</h2>
          <p className="text-sm text-slate-500">
            {count.status} · {count.lines.length} lines · {uncountedRemaining} not yet counted
          </p>
        </div>
        {count.status === "open" && (
          <button
            onClick={() => closeCount.mutate(count.id)}
            disabled={closeCount.isPending}
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Close count
          </button>
        )}
      </div>
      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}

      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="py-1 pr-2">SKU</th>
            <th className="py-1 pr-2">Expected</th>
            <th className="py-1 pr-2">Counted</th>
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
                          setError("Enter a whole number ≥ 0.");
                          return;
                        }
                        submitLine.mutate(
                          { variant_id: line.variant, counted },
                          { onError: (err) => setError(err instanceof ApiError ? err.message : "Could not submit.") },
                        );
                      }}
                      className="text-xs text-slate-600 underline hover:text-slate-900"
                    >
                      Submit
                    </button>
                  )}
                  {discrepancy && <span className="ml-2 text-xs text-amber-700">discrepancy</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
