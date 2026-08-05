import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type {
  Delivery,
  DeliveryCreateInput,
  Paginated,
  ProductSupplierLink,
  Supplier,
  SupplierWriteInput,
} from "./types";

export function useSuppliers() {
  return useQuery({
    queryKey: ["suppliers"],
    queryFn: () => api.get<Supplier[]>("/admin/suppliers"),
  });
}

export function useCreateSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SupplierWriteInput) => api.post<Supplier>("/admin/suppliers", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

export function useUpdateSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ supplierId, input }: { supplierId: number; input: Partial<SupplierWriteInput> }) =>
      api.patch<Supplier>(`/admin/suppliers/${supplierId}`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

export function useVendorCatalog(productId: number | null, enabled = true) {
  return useQuery({
    queryKey: ["vendor-catalog", productId],
    queryFn: () => api.get<ProductSupplierLink[]>(`/admin/products/${productId}/suppliers`),
    enabled: productId !== null && enabled,
  });
}

export function useSetVendorCost(productId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { supplier_id: number; cost_price: number; currency?: string }) =>
      api.post<ProductSupplierLink>(`/admin/products/${productId}/suppliers`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vendor-catalog", productId] }),
  });
}

export function useDeliveries(supplierId?: number) {
  return useQuery({
    queryKey: ["deliveries", supplierId],
    queryFn: () =>
      api.get<Paginated<Delivery>>(`/admin/deliveries${supplierId ? `?supplier=${supplierId}` : ""}`),
  });
}

export function useReceiveDelivery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: DeliveryCreateInput) => api.post<Delivery>("/admin/deliveries", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deliveries"] });
      queryClient.invalidateQueries({ queryKey: ["stock-levels"] });
      queryClient.invalidateQueries({ queryKey: ["admin-product"] });
    },
  });
}
