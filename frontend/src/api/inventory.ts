import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type { MovementCreateInput, Paginated, StockCount, StockCountLine, StockLevel, VariantStaff } from "./types";

export function useStockLevels(params: { lowStock?: boolean; q?: string } = {}) {
  const search = new URLSearchParams();
  if (params.lowStock) search.set("low_stock", "true");
  if (params.q) search.set("q", params.q);
  const qs = search.toString();

  return useQuery({
    queryKey: ["stock-levels", params],
    queryFn: () => api.get<Paginated<StockLevel>>(`/admin/inventory/levels${qs ? `?${qs}` : ""}`),
  });
}

export function useAdjustStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MovementCreateInput) => api.post("/admin/inventory/movements", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stock-levels"] });
      queryClient.invalidateQueries({ queryKey: ["admin-product"] });
    },
  });
}

export function useBarcodeLookup() {
  return useMutation({
    mutationFn: (barcode: string) => api.post<VariantStaff>("/admin/inventory/lookup", { barcode }),
  });
}

export function useStockCounts(status?: "open" | "closed") {
  return useQuery({
    queryKey: ["stock-counts", status],
    queryFn: () => api.get<StockCount[]>(`/admin/inventory/counts${status ? `?status=${status}` : ""}`),
  });
}

export function useStockCount(countId: number | null) {
  return useQuery({
    queryKey: ["stock-count", countId],
    queryFn: () => api.get<StockCount & { lines: StockCountLine[] }>(`/admin/inventory/counts/${countId}`),
    enabled: countId !== null,
  });
}

export function useOpenCount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<StockCount>("/admin/inventory/counts"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stock-counts"] }),
  });
}

export function useSubmitCountLine(countId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { variant_id: number; counted: number }) =>
      api.post<StockCountLine>(`/admin/inventory/counts/${countId}/lines`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stock-count", countId] }),
  });
}

export function useSubmitCountLinesBulk(countId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lines: { variant_id: number; counted: number }[]) =>
      api.post<StockCountLine[]>(`/admin/inventory/counts/${countId}/lines/bulk`, { lines }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stock-count", countId] }),
  });
}

export function useCloseCount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (countId: number) => api.post<StockCount>(`/admin/inventory/counts/${countId}/close`),
    onSuccess: (_data, countId) => {
      queryClient.invalidateQueries({ queryKey: ["stock-counts"] });
      queryClient.invalidateQueries({ queryKey: ["stock-count", countId] });
      queryClient.invalidateQueries({ queryKey: ["stock-levels"] });
    },
  });
}

export function useReopenCount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (countId: number) => api.post<StockCount>(`/admin/inventory/counts/${countId}/reopen`),
    onSuccess: (_data, countId) => {
      queryClient.invalidateQueries({ queryKey: ["stock-counts"] });
      queryClient.invalidateQueries({ queryKey: ["stock-count", countId] });
      queryClient.invalidateQueries({ queryKey: ["stock-levels"] });
    },
  });
}
