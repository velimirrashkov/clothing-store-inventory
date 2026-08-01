import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ApiError } from "./client";
import type { Me } from "./types";

export function useMe() {
  return useQuery<Me | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api.get<Me>("/auth/me");
      } catch (err) {
        // SessionAuthentication has no WWW-Authenticate header, so DRF maps an anonymous
        // request to 403, not 401 (see REST_FRAMEWORK settings in config/settings/base.py).
        if (err instanceof ApiError && err.status === 403) return null;
        throw err;
      }
    },
    retry: false,
    staleTime: 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { email: string; password: string }) =>
      api.post<{ public_id: string; email: string }>("/auth/login", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/auth/logout"),
    onSuccess: () => queryClient.setQueryData(["me"], null),
  });
}

/** Layer 1 permission check, client-side — UX only, every endpoint re-checks server-side (§6.2). */
export function hasPerm(me: Me | null | undefined, perm: string): boolean {
  return !!me?.permissions.includes(perm);
}
