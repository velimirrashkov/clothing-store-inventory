import { Fragment, useState } from "react";
import type { FormEvent } from "react";

import {
  useArchiveProduct,
  useAssignBarcodes,
  useGenerateVariantMatrix,
  useProduct,
  useUpdateProduct,
} from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useAdjustStock } from "../../api/inventory";
import type { StockMovementReason } from "../../api/types";
import { formatMoney } from "../../lib/money";

const MANUAL_REASONS: { value: StockMovementReason; label: string }[] = [
  { value: "receipt", label: "Receipt (new delivery)" },
  { value: "correction", label: "Correction (recount)" },
  { value: "damage", label: "Damage" },
  { value: "loss", label: "Loss / theft" },
  { value: "initial_load", label: "Initial load" },
];

export function ProductDetailPanel({ productId }: { productId: number }) {
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
  const [reason, setReason] = useState<StockMovementReason>("receipt");
  const [adjustError, setAdjustError] = useState<string | null>(null);

  if (isLoading || !product) return <div className="p-8 text-slate-500">Loading…</div>;

  function submitMatrix(event: FormEvent) {
    event.preventDefault();
    setMatrixError(null);
    const amount = Math.round(parseFloat(basePrice) * 100);
    if (Number.isNaN(amount)) {
      setMatrixError("Enter a valid price.");
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
        onError: (err) => setMatrixError(err instanceof ApiError ? err.message : "Could not generate variants."),
      },
    );
  }

  function submitAdjust(event: FormEvent, variantId: number) {
    event.preventDefault();
    setAdjustError(null);
    const parsed = parseInt(delta, 10);
    if (Number.isNaN(parsed) || parsed === 0) {
      setAdjustError("Enter a non-zero whole number.");
      return;
    }
    adjustStock.mutate(
      { variant_id: variantId, delta: parsed, reason },
      {
        onSuccess: () => {
          setAdjustingVariantId(null);
          setDelta("");
        },
        onError: (err) => setAdjustError(err instanceof ApiError ? err.message : "Could not adjust stock."),
      },
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{product.name}</h2>
          <p className="text-sm text-slate-500">
            {product.slug} · {product.status}
            {product.brand && ` · ${product.brand}`}
          </p>
        </div>
        {product.status !== "archived" && (
          <button
            onClick={() => archiveProduct.mutate(productId)}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
          >
            Archive
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
          <h3 className="text-sm font-semibold text-slate-900">Variants</h3>
          <div className="flex gap-2">
            <button
              onClick={() =>
                assignBarcodes.mutate(product.variants.filter((v) => !v.barcode).map((v) => v.id))
              }
              disabled={!product.variants.some((v) => !v.barcode) || assignBarcodes.isPending}
              className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            >
              Assign missing barcodes
            </button>
            <button
              onClick={() => setMatrixOpen((o) => !o)}
              className="rounded bg-slate-900 px-2 py-1 text-xs text-white hover:bg-slate-700"
            >
              Generate variants
            </button>
          </div>
        </div>

        {matrixOpen && (
          <form onSubmit={submitMatrix} className="mb-4 space-y-2 rounded border border-slate-200 bg-slate-50 p-3">
            <div className="grid grid-cols-3 gap-2">
              <label className="text-xs text-slate-600">
                Sizes (comma-separated)
                <input value={sizes} onChange={(e) => setSizes(e.target.value)}
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
              <label className="text-xs text-slate-600">
                Colours (comma-separated)
                <input value={colors} onChange={(e) => setColors(e.target.value)}
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
              <label className="text-xs text-slate-600">
                Base price
                <input value={basePrice} onChange={(e) => setBasePrice(e.target.value)} placeholder="29.99"
                       className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
              </label>
            </div>
            {matrixError && <p className="text-xs text-red-600">{matrixError}</p>}
            <button type="submit" disabled={generateMatrix.isPending}
                    className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
              {generateMatrix.isPending ? "Generating…" : "Generate grid"}
            </button>
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="py-1 pr-2">SKU</th>
              <th className="py-1 pr-2">Size</th>
              <th className="py-1 pr-2">Colour</th>
              <th className="py-1 pr-2">Price</th>
              <th className="py-1 pr-2">Available</th>
              <th className="py-1 pr-2">Barcode</th>
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
                      Adjust
                    </button>
                  </td>
                </tr>
                {adjustingVariantId === variant.id && (
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <td colSpan={7} className="p-2">
                      <form onSubmit={(e) => submitAdjust(e, variant.id)} className="flex items-end gap-2">
                        <label className="text-xs text-slate-600">
                          Quantity change
                          <input
                            value={delta}
                            onChange={(e) => setDelta(e.target.value)}
                            placeholder="e.g. 10 or -2"
                            className="mt-1 block w-28 rounded border border-slate-300 px-2 py-1 text-sm"
                          />
                        </label>
                        <label className="text-xs text-slate-600">
                          Reason
                          <select
                            value={reason}
                            onChange={(e) => setReason(e.target.value as StockMovementReason)}
                            className="mt-1 block rounded border border-slate-300 px-2 py-1 text-sm"
                          >
                            {MANUAL_REASONS.map((r) => (
                              <option key={r.value} value={r.value}>{r.label}</option>
                            ))}
                          </select>
                        </label>
                        <button type="submit" disabled={adjustStock.isPending}
                                className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
                          Save
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
          <p className="py-4 text-sm text-slate-500">No variants yet — generate a size/colour grid above.</p>
        )}
      </section>
    </div>
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
        Name
        <input value={name} onChange={(e) => setName(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="text-xs text-slate-600">
        Brand
        <input value={brand} onChange={(e) => setBrand(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="text-xs text-slate-600">
        Season
        <input value={season} onChange={(e) => setSeason(e.target.value)}
               className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      <label className="col-span-2 text-xs text-slate-600">
        Description
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
                  className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm" />
      </label>
      {dirty && (
        <button type="submit" disabled={saving}
                className="col-span-2 w-fit rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
          {saving ? "Saving…" : "Save changes"}
        </button>
      )}
    </form>
  );
}
