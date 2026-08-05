import { useState } from "react";

import { useCategories, useProduct } from "../../api/catalog";
import { ApiError } from "../../api/client";
import { useCreatePosOrder } from "../../api/orders";
import type { Order, ProductAdminListItem, VariantStaff } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";
import { formatMoney } from "../../lib/money";
import { CategoryTree } from "../products/CategoryTree";

interface CartLine {
  variantId: number;
  sku: string;
  size: string;
  color: string;
  quantity: number;
  unitAmount: number;
  currency: string;
  available: number;
}

export default function SellPage() {
  const { t } = useTranslation();
  const { data: categories, isLoading } = useCategories();
  const [selectedProduct, setSelectedProduct] = useState<ProductAdminListItem | null>(null);
  const [cart, setCart] = useState<CartLine[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<"cash" | "card">("cash");
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<Order | null>(null);
  const createPosOrder = useCreatePosOrder();

  function addToCart(variant: VariantStaff) {
    setCart((lines) => {
      const existing = lines.find((l) => l.variantId === variant.id);
      if (existing) {
        if (existing.quantity >= variant.available) return lines;
        return lines.map((l) => (l.variantId === variant.id ? { ...l, quantity: l.quantity + 1 } : l));
      }
      if (variant.available < 1) return lines;
      return [
        ...lines,
        {
          variantId: variant.id, sku: variant.sku, size: variant.size, color: variant.color,
          quantity: 1, unitAmount: variant.price_amount, currency: variant.currency, available: variant.available,
        },
      ];
    });
  }

  function removeLine(variantId: number) {
    setCart((lines) => lines.filter((l) => l.variantId !== variantId));
  }

  function setQuantity(variantId: number, quantity: number) {
    setCart((lines) =>
      lines.map((l) => (l.variantId === variantId ? { ...l, quantity: Math.max(1, Math.min(quantity, l.available)) } : l)),
    );
  }

  const total = cart.reduce((sum, l) => sum + l.unitAmount * l.quantity, 0);
  const currency = cart[0]?.currency ?? "EUR";

  function completeSale() {
    setError(null);
    createPosOrder.mutate(
      {
        lines: cart.map((l) => ({ variant_id: l.variantId, quantity: l.quantity })),
        payment_method: paymentMethod,
      },
      {
        onSuccess: (order) => {
          setReceipt(order);
          setCart([]);
        },
        onError: (err) => setError(err instanceof ApiError ? err.message : t("sell.error_complete")),
      },
    );
  }

  if (receipt) {
    return <Receipt order={receipt} onNewSale={() => setReceipt(null)} />;
  }

  return (
    <div className="flex h-screen">
      <div className="flex w-72 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 p-3 text-sm font-semibold text-slate-900">{t("sell.browse")}</div>
        <div className="flex-1 overflow-auto p-2">
          {isLoading && <p className="p-2 text-sm text-slate-500">{t("common.loading")}</p>}
          {categories && (
            <CategoryTree categories={categories} selectedProductId={selectedProduct?.id ?? null}
                           onSelectProduct={setSelectedProduct} />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {selectedProduct ? (
          <VariantPicker productId={selectedProduct.id} onAdd={addToCart} />
        ) : (
          <p className="p-8 text-sm text-slate-500">{t("sell.pick_product")}</p>
        )}
      </div>

      <div className="flex w-80 shrink-0 flex-col border-l border-slate-200 bg-white">
        <div className="border-b border-slate-200 p-3 text-sm font-semibold text-slate-900">{t("sell.cart")}</div>
        <div className="flex-1 overflow-auto p-3">
          {cart.length === 0 && <p className="text-sm text-slate-500">{t("sell.cart_empty")}</p>}
          {cart.map((line) => (
            <div key={line.variantId} className="mb-2 flex items-center justify-between text-sm">
              <div>
                <p className="font-mono text-xs">{line.sku}</p>
                <p className="text-xs text-slate-500">{line.size} · {line.color}</p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={1}
                  max={line.available}
                  value={line.quantity}
                  onChange={(e) => setQuantity(line.variantId, Number(e.target.value))}
                  className="w-12 rounded border border-slate-300 px-1 py-0.5 text-center text-xs"
                />
                <span className="w-16 text-right text-xs">{formatMoney(line.unitAmount * line.quantity, line.currency)}</span>
                <button onClick={() => removeLine(line.variantId)} className="text-xs text-red-600">✕</button>
              </div>
            </div>
          ))}
        </div>
        <div className="border-t border-slate-200 p-3">
          <div className="mb-2 flex justify-between text-sm font-semibold">
            <span>{t("sell.total")}</span>
            <span>{formatMoney(total, currency)}</span>
          </div>
          <div className="mb-2 flex gap-2 text-sm">
            {(["cash", "card"] as const).map((method) => (
              <label key={method} className="flex items-center gap-1">
                <input type="radio" name="payment" checked={paymentMethod === method}
                       onChange={() => setPaymentMethod(method)} />
                {t(`sell.${method}`)}
              </label>
            ))}
          </div>
          {error && <p className="mb-2 text-xs text-red-600">{error}</p>}
          <button
            onClick={completeSale}
            disabled={cart.length === 0 || createPosOrder.isPending}
            className="w-full rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {createPosOrder.isPending ? t("sell.completing") : t("sell.complete_sale")}
          </button>
        </div>
      </div>
    </div>
  );
}

function VariantPicker({ productId, onAdd }: { productId: number; onAdd: (variant: VariantStaff) => void }) {
  const { t } = useTranslation();
  const { data: product, isLoading } = useProduct(productId);
  if (isLoading || !product) return <div className="p-8 text-slate-500">{t("common.loading")}</div>;

  return (
    <div className="p-6">
      <h2 className="mb-3 text-lg font-semibold text-slate-900">{product.name}</h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {product.variants.filter((v) => v.is_active).map((variant) => (
          <button
            key={variant.id}
            onClick={() => onAdd(variant)}
            disabled={variant.available < 1}
            className="rounded border border-slate-200 p-3 text-left text-sm hover:border-slate-400 disabled:opacity-40"
          >
            <p className="font-medium">{variant.size} · {variant.color}</p>
            <p className="text-slate-500">{formatMoney(variant.price_amount, variant.currency)}</p>
            <p className="text-xs text-slate-400">{variant.available} {t("sell.in_stock")}</p>
          </button>
        ))}
      </div>
      {product.variants.length === 0 && <p className="text-sm text-slate-500">{t("sell.no_variants")}</p>}
    </div>
  );
}

function Receipt({ order, onNewSale }: { order: Order; onNewSale: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-sm p-8">
      <div className="rounded border border-slate-200 p-6 text-sm">
        <h2 className="mb-1 text-center text-lg font-semibold">{t("sell.sale_complete")}</h2>
        <p className="mb-4 text-center text-slate-500">{order.reference}</p>
        <ul className="mb-4 space-y-1">
          {order.lines.map((line, i) => (
            <li key={i} className="flex justify-between">
              <span>{line.product_name} ({line.size}/{line.color}) ×{line.quantity}</span>
              <span>{formatMoney(line.line_total, order.currency)}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>{t("sell.total")} ({order.payment_method && t(`sell.${order.payment_method}`)})</span>
          <span>{formatMoney(order.total_amount, order.currency)}</span>
        </div>
      </div>
      <button onClick={onNewSale} className="mt-4 w-full rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700">
        {t("sell.new_sale")}
      </button>
    </div>
  );
}
