import { useState } from "react";

import { useCategories } from "../../api/catalog";
import type { ProductAdminListItem } from "../../api/types";
import { useTranslation } from "../../i18n/LanguageContext";
import { CategoryTree } from "./CategoryTree";
import { NewCategoryForm } from "./NewCategoryForm";
import { NewProductForm } from "./NewProductForm";
import { ProductDetailPanel } from "./ProductDetailPanel";

/**
 * Master-detail: click a category to expand it lazily, click a product to load its detail in
 * the right-hand pane without leaving the page (see the lazy-category-tree pattern this repo
 * has used since the original inventory tool — this is the same shape, rebuilt on the new stack).
 */
export default function ProductsPage() {
  const { t } = useTranslation();
  const { data: categories, isLoading } = useCategories();
  const [selectedProduct, setSelectedProduct] = useState<ProductAdminListItem | null>(null);
  const [newCategoryOpen, setNewCategoryOpen] = useState(false);
  const [newProductOpen, setNewProductOpen] = useState(false);

  return (
    <div className="flex h-screen">
      <div className="flex w-80 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 p-3">
          <h1 className="text-sm font-semibold text-slate-900">{t("products.title")}</h1>
          <div className="flex gap-2 text-xs">
            <button onClick={() => setNewCategoryOpen((o) => !o)} className="text-slate-600 hover:text-slate-900">
              {t("products.add_category")}
            </button>
            <button onClick={() => setNewProductOpen((o) => !o)} className="text-slate-600 hover:text-slate-900">
              {t("products.add_product")}
            </button>
          </div>
        </div>
        {newCategoryOpen && <NewCategoryForm onClose={() => setNewCategoryOpen(false)} />}
        {newProductOpen && (
          <NewProductForm
            onClose={() => setNewProductOpen(false)}
            onCreated={(product) => setSelectedProduct(product)}
          />
        )}
        <div className="flex-1 overflow-auto p-2">
          {isLoading && <p className="p-2 text-sm text-slate-500">{t("common.loading")}</p>}
          {categories && (
            <CategoryTree
              categories={categories}
              selectedProductId={selectedProduct?.id ?? null}
              onSelectProduct={setSelectedProduct}
            />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {selectedProduct ? (
          <ProductDetailPanel key={selectedProduct.id} productId={selectedProduct.id} />
        ) : (
          <div className="p-8 text-sm text-slate-500">{t("products.select_prompt")}</div>
        )}
      </div>
    </div>
  );
}
