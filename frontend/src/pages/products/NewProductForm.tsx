import { useState } from "react";
import type { FormEvent } from "react";

import { useCategories, useCreateProduct } from "../../api/catalog";
import { ApiError } from "../../api/client";
import type { ProductAdminDetail } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";

const GENDERS = ["unisex", "men", "women", "kids"] as const;

export function NewProductForm({ onClose, onCreated }: {
  onClose: () => void;
  onCreated: (product: ProductAdminDetail) => void;
}) {
  const { t } = useTranslation();
  const { data: categories } = useCategories();
  const createProduct = useCreateProduct();
  const [name, setName] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [gender, setGender] = useState<(typeof GENDERS)[number]>("unisex");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!categoryId) {
      setError(t("products.error_choose_category"));
      return;
    }
    createProduct.mutate(
      { name, category: Number(categoryId), gender },
      {
        onSuccess: (product) => {
          onCreated(product);
          onClose();
        },
        onError: (err) => setError(err instanceof ApiError ? err.message : t("products.error_create_product")),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 border-b border-slate-200 p-3">
      <input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder={t("products.product_name_placeholder")}
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
      />
      <select
        value={categoryId}
        onChange={(e) => setCategoryId(e.target.value)}
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
      >
        <option value="">{t("products.choose_category")}</option>
        {categories?.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      <select
        value={gender}
        onChange={(e) => setGender(e.target.value as (typeof GENDERS)[number])}
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
      >
        {GENDERS.map((g) => (
          <option key={g} value={g}>{t(`gender.${g}`)}</option>
        ))}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={!name || createProduct.isPending}
                className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
          {t("common.create")}
        </button>
        <button type="button" onClick={onClose} className="text-xs text-slate-500 hover:text-slate-800">
          {t("common.cancel")}
        </button>
      </div>
    </form>
  );
}
