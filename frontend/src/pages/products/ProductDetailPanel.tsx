import { Fragment, useState } from "react";
import type { FormEvent } from "react";

import {
  useArchiveProduct,
  useAssignBarcodes,
  useGenerateVariantMatrix,
  useProduct,
  useUpdateProduct,
} from "../../api/catalog";
import { useMe } from "../../api/auth";
import { ApiError } from "../../api/client";
import { useAdjustStock } from "../../api/inventory";
import { useSetVendorCost, useSuppliers, useVendorCatalog } from "../../api/suppliers";
import type { StockMovementReason } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";
import { formatMoney } from "../../lib/money";

// "receipt" (new stock arriving) deliberately isn't offered here — that's what the Deliveries
// page is for, since it also records the supplier and cost. This stays for corrections only.
const MANUAL_REASONS: StockMovementReason[] = ["correction", "damage", "loss", "initial_load"];

export function ProductDetailPanel({ productId }: { productId: number }) {
  const { t } = useTranslation();
  const { data: product, isLoading } = useProduct(productId);
  const updateProduct = useUpdateProduct(productId);
  const archiveProduct = useArchiveProduct();
  const generateMatrix = useGenerateVariantMatrix(productId);
  const assignBarcodes = useAssignBarcodes(productId);
  const adjustStock = useAdjustStock();

  const [matrixOpen, setMatrixOpen] = useState(false);
  const [sizes, setSizes] = useState("S, M, L");
  const [colors, setColors] = useState("black");
  const [basePrice, setBasePrice] = useState("");
  const [matrixError, setMatrixError] = useState<string | null>(null);

  const [adjustingVariantId, setAdjustingVariantId] = useState<number | null>(null);
  const [delta, setDelta] = useState("");
  const [reason, setReason] = useState<StockMovementReason>("correction");
  const [adjustError, setAdjustError] = useState<string | null>(null);

  if (isLoading || !product) return <div className="p-8 text-slate-500">{t("common.loading")}</div>;

  function submitMatrix(event: FormEvent) {
    event.preventDefault();
    setMatrixError(null);
    const amount = Math.round(parseFloat(basePrice) * 100);
    if (Number.isNaN(amount)) {
      setMatrixError(t("products.error_invalid_price"));
      return;
    }
    generateMatrix.mutate(
      {
        sizes: sizes.split(",").map((s) => s.trim()).filter(Boolean),
        colors: colors.split(",").map((c) => c.trim()).filter(Boolean),
        base_price_amount: amount,
      },
      {
        onSuccess: () => setMatrixOpen(false),
        onError: (err) => setMatrixError(err instanceof ApiError ? err.message : t("products.error_generate_variants")),
      },
    );
  }

  function submitAdjust(event: FormEvent, variantId: number) {
    event.preventDefault();
    setAdjustError(null);
    const parsed = parseInt(delta, 10);
    if (Number.isNaN(parsed) || parsed === 0) {
      setAdjustError(t("products.error_quantity"));
      return;
    }
    adjustStock.mutate(
      { variant_id: variantId, delta: parsed, reason },
      {
        onSuccess: () => {
          setAdjustingVariantId(null);
          setDelta("");
        },
        onError: (err) => setAdjustError(err instanceof ApiError ? err.message : t("products.error_adjust")),
      },
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{product.name}</h2>
          <p className="text-sm text-slate-500">
            {product.slug} · {t(`status.${product.status}`)}
            {product.brand && ` · ${product.brand}`}
          </p>
        </div>
        {product.status !== "archived" && (
          <button
            onClick={() => archiveProduct.mutate(productId)}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
          >
            {t("products.archive")}
          </button>
        )}
      </div>

      <EditProductForm
        key={product.id}
        product={product}
        onSave={(changes) => updateProduct.mutate(changes)}
        saving={updateProduct.isPending}
      />

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900">{t("products.variants")}</h3>
          <div className="flex gap-2">
            <button
              onClick={() =>
                assignBarcodes.mutate(product.variants.filter((v) => !v.barcode).map((v) => v.id))
              }
              disabled={!product.variants.some((v) => !v.barcode) || assignBarcodes.isPending}
              className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            >
              {t("products.assign_missing_barcodes")}
            </button>
            <button
              onClick={() => setMatrixOpen((o) => !o)}
              className="rounded bg-slate-900 px-2 py-1 text-xs text-white hover:bg-slate-700"
            >
              {t("products.generate_variants")}
            </button>
          </div>
        </div>

        {matrixOpen && (
          <form onSubmit={submitMatrix} className="mb-4 space-y-2 rounded border border-slate-200 bg-slate-50 p-3">
            <div className="grid grid-cols-3 gap-2">
              <label className="text-xs text-slate-600">
                {t("products.sizes_csv")}
                <input value={sizes} onChange={(e) => setSizes(e.target.value)}
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
              <label className="text-xs text-slate-600">
                {t("products.colors_csv")}
                <input value={colors} onChange={(e) => setColors(e.target.value)}
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
              <label className="text-xs text-slate-600">
                {t("products.base_price")}
                <input value={basePrice} onChange={(e) => setBasePrice(e.target.value)} placeholder="29.99"
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
            </div>
            {matrixError && <p className="text-xs text-red-600">{matrixError}</p>}
            <button type="submit" disabled={generateMatrix.isPending}
                    className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
              {generateMatrix.isPending ? t("products.generating") : t("products.generate_grid")}
            </button>
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="py-1 pr-2">{t("products.col_sku")}</th>
              <th className="py-1 pr-2">{t("products.col_size")}</th>
              <th className="py-1 pr-2">{t("products.col_color")}</th>
              <th className="py-1 pr-2">{t("products.col_price")}</th>
              <th className="py-1 pr-2">{t("products.col_available")}</th>
              <th className="py-1 pr-2">{t("products.col_barcode")}</th>
              <th className="py-1"></th>
            </tr>
          </thead>
          <tbody>
            {product.variants.map((variant) => (
              <Fragment key={variant.id}>
                <tr className="border-b border-slate-100">
                  <td className="py-1.5 pr-2 font-mono text-xs">{variant.sku}</td>
                  <td className="py-1.5 pr-2">{variant.size}</td>
                  <td className="py-1.5 pr-2">{variant.color}</td>
                  <td className="py-1.5 pr-2">{formatMoney(variant.price_amount, variant.currency)}</td>
                  <td className="py-1.5 pr-2">
                    <span className={variant.available <= 5 ? "font-semibold text-amber-700" : ""}>
                      {variant.available}
                    </span>
                  </td>
                  <td className="py-1.5 pr-2 font-mono text-xs text-slate-500">{variant.barcode ?? "—"}</td>
                  <td className="py-1.5 text-right">
                    <button
                      onClick={() => {
                        setAdjustingVariantId(adjustingVariantId === variant.id ? null : variant.id);
                        setAdjustError(null);
                      }}
                      className="text-xs text-slate-600 underline hover:text-slate-900"
                    >
                      {t("products.adjust")}
                    </button>
                  </td>
                </tr>
                {adjustingVariantId === variant.id && (
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <td colSpan={7} className="p-2">
                      <form onSubmit={(e) => submitAdjust(e, variant.id)} className="flex items-end gap-2">
                        <label className="text-xs text-slate-600">
                          {t("products.quantity_change")}
                          <input
                            value={delta}
                            onChange={(e) => setDelta(e.target.value)}
                            placeholder={t("products.quantity_placeholder")}
                            className="mt-1 block w-28 rounded border border-slate-300 px-2 py-1 text-sm"
                          />
                        </label>
                        <label className="text-xs text-slate-600">
                          {t("products.reason")}
                          <select
                            value={reason}
                            onChange={(e) => setReason(e.target.value as StockMovementReason)}
                            className="mt-1 block rounded border border-slate-300 px-2 py-1 text-sm"
                          >
                            {MANUAL_REASONS.map((value) => (
                              <option key={value} value={value}>{t(`reason.${value}`)}</option>
                            ))}
                          </select>
                        </label>
                        <button type="submit" disabled={adjustStock.isPending}
                                className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
                          {t("common.save")}
                        </button>
                        {adjustError && <span className="text-xs text-red-600">{adjustError}</span>}
                      </form>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
        {product.variants.length === 0 && (
          <p className="py-4 text-sm text-slate-500">{t("products.no_variants")}</p>
        )}
      </section>

      <VendorCatalogSection productId={productId} />
    </div>
  );
}

function VendorCatalogSection({ productId }: { productId: number }) {
  const { t } = useTranslation();
  const { data: me } = useMe();
  const canManage = !!me?.permissions.includes("suppliers.manage_suppliers");
  const { data: links, isLoading } = useVendorCatalog(productId, canManage);
  const setCost = useSetVendorCost(productId);
  const [supplierId, setSupplierId] = useState("");
  const [costInput, setCostInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!canManage) return null;

  function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const cost = Math.round(parseFloat(costInput) * 100);
    if (!supplierId || Number.isNaN(cost)) {
      setError(t("products.error_vendor_cost"));
      return;
    }
    setCost.mutate(
      { supplier_id: Number(supplierId), cost_price: cost },
      {
        onSuccess: () => { setSupplierId(""); setCostInput(""); },
        onError: (err) => setError(err instanceof ApiError ? err.message : t("products.error_save_cost")),
      },
    );
  }

  return (
    <section>
      <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("products.vendor_catalog")}</h3>
      <p className="mb-2 text-xs text-slate-500">{t("products.vendor_catalog_hint")}</p>
      {isLoading && <p className="text-sm text-slate-500">{t("common.loading")}</p>}
      {links && links.length > 0 && (
        <table className="mb-3 w-full max-w-md text-sm">
          <tbody>
            {links.map((link) => (
              <tr key={link.id} className="border-b border-slate-100">
                <td className="py-1.5 pr-2">{link.supplier_name}</td>
                <td className="py-1.5 text-right">{formatMoney(link.cost_price, link.currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <VendorCatalogForm supplierId={supplierId} setSupplierId={setSupplierId}
                         costInput={costInput} setCostInput={setCostInput}
                         onSubmit={submit} pending={setCost.isPending} error={error} />
    </section>
  );
}

function VendorCatalogForm({ supplierId, setSupplierId, costInput, setCostInput, onSubmit, pending, error }: {
  supplierId: string;
  setSupplierId: (v: string) => void;
  costInput: string;
  setCostInput: (v: string) => void;
  onSubmit: (e: FormEvent) => void;
  pending: boolean;
  error: string | null;
}) {
  const { t } = useTranslation();
  const { data: suppliers } = useSuppliers();

  return (
    <form onSubmit={onSubmit} className="flex items-end gap-2">
      <label className="text-xs text-slate-600">
        {t("products.supplier")}
        <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)}
                className="mt-1 block rounded border border-slate-300 px-2 py-1 text-sm">
          <option value="">{t("common.choose")}</option>
          {suppliers?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </label>
      <label className="text-xs text-slate-600">
        {t("products.cost")}
        <input value={costInput} onChange={(e) => setCostInput(e.target.value)} placeholder="0.00"
               className="mt-1 block w-24 rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <button type="submit" disabled={pending}
              className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
        {t("products.save_cost")}
      </button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </form>
  );
}

function EditProductForm({
  product,
  onSave,
  saving,
}: {
  product: { name: string; description: string; brand: string; season: string };
  onSave: (changes: { name: string; description: string; brand: string; season: string }) => void;
  saving: boolean;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(product.name);
  const [description, setDescription] = useState(product.description);
  const [brand, setBrand] = useState(product.brand);
  const [season, setSeason] = useState(product.season);
  const dirty = name !== product.name || description !== product.description
    || brand !== product.brand || season !== product.season;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSave({ name, description, brand, season });
      }}
      className="grid grid-cols-2 gap-3 rounded border border-slate-200 p-3"
    >
      <label className="text-xs text-slate-600">
        {t("common.name")}
        <input value={name} onChange={(e) => setName(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="text-xs text-slate-600">
        {t("products.brand")}
        <input value={brand} onChange={(e) => setBrand(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="text-xs text-slate-600">
        {t("products.season")}
        <input value={season} onChange={(e) => setSeason(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="col-span-2 text-xs text-slate-600">
        {t("products.description")}
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
                  className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      {dirty && (
        <button type="submit" disabled={saving}
                className="col-span-2 w-fit rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
          {saving ? t("common.saving") : t("common.save_changes")}
        </button>
      )}
    </form>
  );
}
