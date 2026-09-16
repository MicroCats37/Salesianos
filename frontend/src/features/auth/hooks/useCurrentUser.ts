"use client";

import { useQuery } from "@tanstack/react-query";
import type { User } from "../schemas";
import { getMe } from "../services/auth.service";

export function useCurrentUser() {
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const response = await getMe();
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Failed to fetch user");
      }
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}
