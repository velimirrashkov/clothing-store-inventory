import { useState } from "react";

import { useStockLevels } from "../../api/inventory";
import { BarcodeLookup } from "./BarcodeLookup";

/**
 * No "browse everything" view here on purpose — a global flat stock table is exactly the shape
 * this app avoids (see the category-tree pattern on the Products page). This page defaults to
 * low-stock (bounded by definition) and lets staff search a specific SKU; browsing by category
 * belongs on the Products page, which already shows each variant's availability.
 */
export default function InventoryPage() {
  const [query, setQuery] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(true);
  const { data, isLoading } = useStockLevels({ lowStock: lowStockOnly && !query, q: query || undefined });

  return (
    <div className="space-y-8 p-6">
      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Barcode lookup</h2>
        <BarcodeLookup />
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">
            {query ? "Search results" : "Low stock"}
          </h2>
          <div className="flex items-center gap-3">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by SKU"
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            />
            {!query && (
              <label className="flex items-center gap-1 text-xs text-slate-600">
                <input type="checkbox" checked={lowStockOnly} onChange={(e) => setLowStockOnly(e.target.checked)} />
                Low stock only (≤5)
              </label>
            )}
          </div>
        </div>

        {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
        {!isLoading && data?.results.length === 0 && (
          <p className="text-sm text-slate-500">Nothing to show.</p>
        )}
        {data && data.results.length > 0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="py-1 pr-2">SKU</th>
                <th className="py-1 pr-2">On hand</th>
                <th className="py-1 pr-2">Reserved</th>
                <th className="py-1 pr-2">Available</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map((level) => (
                <tr key={level.variant} className="border-b border-slate-100">
                  <td className="py-1.5 pr-2 font-mono text-xs">{level.sku}</td>
                  <td className="py-1.5 pr-2">{level.on_hand}</td>
                  <td className="py-1.5 pr-2">{level.reserved}</td>
                  <td className="py-1.5 pr-2 font-semibold text-amber-700">{level.available}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
