"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useCurrentUser } from "../hooks/useCurrentUser";
import { useAuthStore } from "../store/auth.store";

export function AuthHydrationShell({ children }: { children: ReactNode }) {
  const setUser = useAuthStore((s) => s.setUser);
  const clearUser = useAuthStore((s) => s.clearUser);

  const { data, error, isLoading } = useCurrentUser();

  useEffect(() => {
    if (isLoading) return;
    if (error) {
      clearUser();
      return;
    }
    if (data) {
      setUser(data);
    }
  }, [data, error, isLoading, setUser, clearUser]);

  return <>{children}</>;
}
