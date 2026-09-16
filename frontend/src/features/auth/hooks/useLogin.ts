"use client";

import { useMutation } from "@tanstack/react-query";
import type { LoginPayload, User } from "../schemas";
import {
  loginDni,
  loginEmail,
  login as loginService,
  loginUsername,
} from "../services/auth.service";
import { useAuthStore } from "../store/auth.store";

export function useLogin() {
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation<User, Error, LoginPayload>({
    mutationFn: async (data) => {
      const response = await resolveLogin(data);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Login failed");
      }
      return response.data;
    },
    onSuccess: (user) => {
      setUser(user);
    },
  });
}

function resolveLogin(data: LoginPayload) {
  if ("username" in data) {
    return loginUsername(data.username, data.password);
  }

  if ("dni" in data) {
    return loginDni(data.dni, data.password);
  }

  if ("email" in data) {
    return loginEmail(data.email, data.password);
  }

  return loginService(data);
}
