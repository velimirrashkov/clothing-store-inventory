import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type {
  Category,
  Paginated,
  ProductAdminDetail,
  ProductAdminListItem,
  ProductWriteInput,
  VariantMatrixInput,
  VariantStaff,
  VariantUpdateInput,
} from "./types";

// Categories are read via the public endpoint (AllowAny, returns everything active) — no need
// for a separate staff-only read path, only for the write side (see admin_views.py's comment).
export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<Category[]>("/categories"),
    staleTime: 60_000,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string; parent?: number | null; position?: number }) =>
      api.post<Category>("/admin/categories", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useProducts(params: { category?: string; status?: string; enabled?: boolean } = {}) {
  const search = new URLSearchParams();
  if (params.category) search.set("category", params.category);
  if (params.status) search.set("status", params.status);
  const qs = search.toString();

  return useQuery({
    queryKey: ["admin-products", params.category, params.status],
    queryFn: () => api.get<Paginated<ProductAdminListItem>>(`/admin/products${qs ? `?${qs}` : ""}`),
    enabled: params.enabled ?? true,
  });
}

export function useProduct(productId: number | null) {
  return useQuery({
    queryKey: ["admin-product", productId],
    queryFn: () => api.get<ProductAdminDetail>(`/admin/products/${productId}`),
    enabled: productId !== null,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProductWriteInput) => api.post<ProductAdminDetail>("/admin/products", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-products"] }),
  });
}

export function useUpdateProduct(productId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: Partial<ProductWriteInput>) =>
      api.patch<ProductAdminDetail>(`/admin/products/${productId}`, input),
    onSuccess: (product) => {
      queryClient.setQueryData(["admin-product", productId], product);
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    },
  });
}

export function useArchiveProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (productId: number) => api.post<ProductAdminDetail>(`/admin/products/${productId}/archive`),
    onSuccess: (product) => {
      queryClient.setQueryData(["admin-product", product.id], product);
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
    },
  });
}

export function useGenerateVariantMatrix(productId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: VariantMatrixInput) =>
      api.post<VariantStaff[]>(`/admin/products/${productId}/variants/matrix`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-product", productId] }),
  });
}

export function useUpdateVariant(productId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ variantId, input }: { variantId: number; input: VariantUpdateInput }) =>
      api.patch<VariantStaff>(`/admin/variants/${variantId}`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-product", productId] }),
  });
}

export function useAssignBarcodes(productId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (variantIds: number[]) =>
      api.post<VariantStaff[]>("/admin/variants/assign-barcodes", { variant_ids: variantIds }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-product", productId] }),
  });
}
