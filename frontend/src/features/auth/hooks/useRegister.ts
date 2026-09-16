"use client";

import { useMutation } from "@tanstack/react-query";
import type { RegisterFormData, User } from "../schemas";
import { registerUser as registerService } from "../services/auth.service";
import { useAuthStore } from "../store/auth.store";

export function useRegister() {
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation<User, Error, RegisterFormData>({
    mutationFn: async (data) => {
      const response = await registerService(data);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Register failed");
      }
      return response.data;
    },
    onSuccess: (user) => {
      setUser(user);
    },
  });
}
