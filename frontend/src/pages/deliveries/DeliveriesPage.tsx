import { useState } from "react";

import { useMe } from "../../api/auth";
import { useCategories, useProduct } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useDeliveries, useReceiveDelivery, useSuppliers, useVendorCatalog } from "../../api/suppliers";
import type { ProductAdminListItem, VariantStaff } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";
import { CategoryTree } from "../products/CategoryTree";

interface DraftLine {
  variantId: number;
  sku: string;
  size: string;
  color: string;
  quantity: number;
  unitCost: number;
}

export default function DeliveriesPage() {
  const { t } = useTranslation();
  const { data: suppliers } = useSuppliers();
  const { data: categories, isLoading: categoriesLoading } = useCategories();
  const { data: deliveries } = useDeliveries();
  const receiveDelivery = useReceiveDelivery();

  const [supplierId, setSupplierId] = useState<string>("");
  const [selectedProduct, setSelectedProduct] = useState<ProductAdminListItem | null>(null);
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [reference, setReference] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirmedDelivery, setConfirmedDelivery] = useState<number | null>(null);

  function addLine(variant: VariantStaff, defaultCost: number) {
    setLines((current) => {
      if (current.some((l) => l.variantId === variant.id)) return current;
      return [...current, {
        variantId: variant.id, sku: variant.sku, size: variant.size, color: variant.color,
        quantity: 1, unitCost: defaultCost,
      }];
    });
  }

  function updateLine(variantId: number, changes: Partial<DraftLine>) {
    setLines((current) => current.map((l) => (l.variantId === variantId ? { ...l, ...changes } : l)));
  }

  function removeLine(variantId: number) {
    setLines((current) => current.filter((l) => l.variantId !== variantId));
  }

  function submit() {
    setError(null);
    if (!supplierId) {
      setError(t("deliveries.error_choose_supplier"));
      return;
    }
    receiveDelivery.mutate(
      {
        supplier_id: Number(supplierId),
        reference,
        lines: lines.map((l) => ({ variant_id: l.variantId, quantity: l.quantity, unit_cost: l.unitCost })),
      },
      {
        onSuccess: (delivery) => {
          setConfirmedDelivery(delivery.id);
          setLines([]);
          setReference("");
        },
        onError: (err) => setError(err instanceof ApiError ? err.message : t("deliveries.error_receive")),
      },
    );
  }

  return (
    <div className="flex h-screen">
      <div className="flex w-72 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 p-3 text-sm font-semibold text-slate-900">{t("deliveries.browse_products")}</div>
        <div className="flex-1 overflow-auto p-2">
          {categoriesLoading && <p className="p-2 text-sm text-slate-500">{t("common.loading")}</p>}
          {categories && (
            <CategoryTree categories={categories} selectedProductId={selectedProduct?.id ?? null}
                           onSelectProduct={setSelectedProduct} />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {confirmedDelivery ? (
          <div className="p-6">
            <p className="mb-3 text-sm font-medium text-green-700">
              {t("deliveries.delivery_number")}{confirmedDelivery} {t("deliveries.received")}
            </p>
            <button onClick={() => setConfirmedDelivery(null)}
                    className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700">
              {t("deliveries.receive_another")}
            </button>
          </div>
        ) : selectedProduct ? (
          <VariantPicker productId={selectedProduct.id} onAdd={addLine} />
        ) : (
          <div className="p-6">
            <p className="mb-6 text-sm text-slate-500">{t("deliveries.pick_product")}</p>
            <DeliveryHistory deliveries={deliveries?.results ?? []} />
          </div>
        )}
      </div>

      {!confirmedDelivery && (
        <div className="flex w-96 shrink-0 flex-col border-l border-slate-200 bg-white">
          <div className="border-b border-slate-200 p-3 text-sm font-semibold text-slate-900">{t("deliveries.new_delivery")}</div>
          <div className="space-y-2 border-b border-slate-200 p-3">
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)}
                    className="w-full rounded border border-slate-300 px-2 py-1 text-sm">
              <option value="">{t("deliveries.choose_supplier")}</option>
              {suppliers?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <input value={reference} onChange={(e) => setReference(e.target.value)}
                   placeholder={t("deliveries.reference_placeholder")}
                   className="w-full rounded border border-slate-300 px-2 py-1 text-sm" />
          </div>

          <div className="flex-1 overflow-auto p-3">
            {lines.length === 0 && <p className="text-sm text-slate-500">{t("deliveries.no_lines")}</p>}
            {lines.map((line) => (
              <div key={line.variantId} className="mb-2 rounded border border-slate-100 p-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs">{line.sku}</span>
                  <button onClick={() => removeLine(line.variantId)} className="text-xs text-red-600">✕</button>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <label>
                    {t("deliveries.qty")}
                    <input type="number" min={1} value={line.quantity}
                           onChange={(e) => updateLine(line.variantId, { quantity: Math.max(1, Number(e.target.value)) })}
                           className="ml-1 w-14 rounded border border-slate-300 px-1 py-0.5" />
                  </label>
                  <label>
                    {t("deliveries.unit_cost")}
                    <input type="number" min={0} step="0.01" value={(line.unitCost / 100).toFixed(2)}
                           onChange={(e) => updateLine(line.variantId, { unitCost: Math.round(Number(e.target.value) * 100) })}
                           className="ml-1 w-20 rounded border border-slate-300 px-1 py-0.5" />
                  </label>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-200 p-3">
            {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
            <button
              onClick={submit}
              disabled={lines.length === 0 || receiveDelivery.isPending}
              className="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {receiveDelivery.isPending ? t("deliveries.receiving") : t("deliveries.receive")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function VariantPicker({ productId, onAdd }: {
  productId: number;
  onAdd: (variant: VariantStaff, defaultCost: number) => void;
}) {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const canSeeCosts = !!me?.permissions.includes("suppliers.manage_suppliers");
  const { data: product, isLoading } = useProduct(productId);
  const { data: vendorCatalog } = useVendorCatalog(productId, canSeeCosts);

  if (isLoading || !product) return <div className="p-8 text-slate-500">{t("common.loading")}</div>;

  // If this product has a quoted cost from any supplier, use it as a starting point — still
  // editable per line, since what actually arrives may differ from the quote.
  const suggestedCost = vendorCatalog?.[0]?.cost_price ?? 0;

  return (
    <div className="p-6">
      <h2 className="mb-3 text-lg font-semibold text-slate-900">{product.name}</h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {product.variants.map((variant) => (
          <button
            key={variant.id}
            onClick={() => onAdd(variant, suggestedCost || variant.price_amount)}
            className="rounded border border-slate-200 p-3 text-left text-sm hover:border-slate-400"
          >
            <p className="font-medium">{variant.size} · {variant.color}</p>
            <p className="text-slate-500">{variant.available} {t("deliveries.currently_in_stock")}</p>
          </button>
        ))}
      </div>
      {product.variants.length === 0 && <p className="text-sm text-slate-500">{t("sell.no_variants")}</p>}
    </div>
  );
}

function DeliveryHistory({ deliveries }: { deliveries: { id: number; supplier_name: string; reference: string; created_at: string; lines: unknown[] }[] }) {
  const { t } = useTranslation();
  if (deliveries.length === 0) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("deliveries.recent")}</h3>
      <table className="w-full max-w-2xl text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
            <th className="py-1 pr-2">#</th>
            <th className="py-1 pr-2">{t("deliveries.col_supplier")}</th>
            <th className="py-1 pr-2">{t("deliveries.col_reference")}</th>
            <th className="py-1 pr-2">{t("deliveries.col_lines")}</th>
            <th className="py-1 pr-2">{t("deliveries.col_date")}</th>
          </tr>
        </thead>
        <tbody>
          {deliveries.map((d) => (
            <tr key={d.id} className="border-b border-slate-100">
              <td className="py-1.5 pr-2">{d.id}</td>
              <td className="py-1.5 pr-2">{d.supplier_name}</td>
              <td className="py-1.5 pr-2 text-slate-500">{d.reference || "—"}</td>
              <td className="py-1.5 pr-2">{d.lines.length}</td>
              <td className="py-1.5 pr-2 text-slate-500">{new Date(d.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
