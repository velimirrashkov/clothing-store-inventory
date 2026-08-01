import { useMemo, useState } from "react";

import { useProducts } from "../../api/catalog";
import type { Category, ProductAdminListItem } from "../../api/types";

/**
 * Categories are fetched in full up front (there are only ever a handful of dozens of them),
 * but a category's PRODUCTS are only fetched the first time it's expanded — this app never
 * renders a full flat list of products, even behind a cap. A catalog with thousands of SKUs
 * should never cost more than "however many categories are currently open" on any render.
 */
export function CategoryTree({
  categories,
  selectedProductId,
  onSelectProduct,
}: {
  categories: Category[];
  selectedProductId: number | null;
  onSelectProduct: (product: ProductAdminListItem) => void;
}) {
  const childrenByParent = useMemo(() => {
    const map = new Map<number | null, Category[]>();
    for (const category of categories) {
      const key = category.parent;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(category);
    }
    for (const list of map.values()) list.sort((a, b) => a.position - b.position || a.name.localeCompare(b.name));
    return map;
  }, [categories]);

  const roots = childrenByParent.get(null) ?? [];

  if (roots.length === 0) {
    return <p className="p-3 text-sm text-slate-500">No categories yet — create one to get started.</p>;
  }

  return (
    <ul className="space-y-0.5">
      {roots.map((category) => (
        <CategoryNode
          key={category.id}
          category={category}
          childrenByParent={childrenByParent}
          depth={0}
          selectedProductId={selectedProductId}
          onSelectProduct={onSelectProduct}
        />
      ))}
    </ul>
  );
}

function CategoryNode({
  category,
  childrenByParent,
  depth,
  selectedProductId,
  onSelectProduct,
}: {
  category: Category;
  childrenByParent: Map<number | null, Category[]>;
  depth: number;
  selectedProductId: number | null;
  onSelectProduct: (product: ProductAdminListItem) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const children = childrenByParent.get(category.id ?? -1) ?? [];
  const { data: productsPage, isLoading } = useProducts({ category: category.slug, enabled: expanded });

  return (
    <li>
      <button
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center gap-1 rounded px-2 py-1 text-left text-sm text-slate-700 hover:bg-slate-100"
        style={{ paddingLeft: `${depth * 14 + 8}px` }}
      >
        <span className="w-3 text-slate-400">{expanded ? "▾" : "▸"}</span>
        {category.name}
      </button>

      {expanded && (
        <ul>
          {children.map((child) => (
            <CategoryNode
              key={child.id}
              category={child}
              childrenByParent={childrenByParent}
              depth={depth + 1}
              selectedProductId={selectedProductId}
              onSelectProduct={onSelectProduct}
            />
          ))}

          {isLoading && (
            <li className="py-1 text-xs text-slate-400" style={{ paddingLeft: `${(depth + 1) * 14 + 8}px` }}>
              Loading…
            </li>
          )}
          {productsPage?.results.map((product) => (
            <li key={product.id}>
              <button
                onClick={() => onSelectProduct(product)}
                className={`block w-full truncate rounded px-2 py-1 text-left text-sm ${
                  selectedProductId === product.id
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
                style={{ paddingLeft: `${(depth + 1) * 14 + 8}px` }}
              >
                {product.name}
                {product.status !== "active" && (
                  <span className="ml-1 text-xs opacity-70">({product.status})</span>
                )}
              </button>
            </li>
          ))}
          {!isLoading && productsPage?.results.length === 0 && children.length === 0 && (
            <li className="py-1 text-xs text-slate-400" style={{ paddingLeft: `${(depth + 1) * 14 + 8}px` }}>
              Empty
            </li>
          )}
        </ul>
      )}
    </li>
  );
}
