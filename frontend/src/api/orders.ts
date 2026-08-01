import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import type { Order, PosOrderCreateInput } from "./types";

export function useCreatePosOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PosOrderCreateInput) => api.post<Order>("/admin/orders/pos", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stock-levels"] }),
  });
}
