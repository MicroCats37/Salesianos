"use client";

import { useMutation } from "@tanstack/react-query";
import { logout as logoutService } from "../services/auth.service";
import { useAuthStore } from "../store/auth.store";

export function useLogout() {
  const clearUser = useAuthStore((s) => s.clearUser);

  return useMutation<void, Error, void>({
    mutationFn: async () => {
      await logoutService();
      clearUser();
    },
  });
}
