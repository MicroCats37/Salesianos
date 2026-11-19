"use client";

import { useMutation } from "@tanstack/react-query";
import { setCookie } from "cookies-next";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { registerUser } from "../services/register.service";
import { useAuthStore } from "../store/auth.store";
import type { RegisterFormData, RegisterResponse } from "../schemas";
import { AUTH_COOKIES } from "@/lib/auth";
import { consumePostAuthRedirect } from "@/lib/post-auth-redirect";

const COOKIE_OPTIONS = {
  path: "/",
  secure: process.env.NEXT_PUBLIC_COOKIE_SECURE === "true",
  sameSite: "lax" as const,
  maxAge: 7 * 24 * 60 * 60,
  httpOnly: false,
};

function persistAuthTokens(data: RegisterResponse) {
  const { access_token, refresh_token, expires_at } = data;
  setCookie(AUTH_COOKIES.ACCESS_TOKEN, access_token, COOKIE_OPTIONS);
  setCookie(AUTH_COOKIES.REFRESH_TOKEN, refresh_token, COOKIE_OPTIONS);
  setCookie(AUTH_COOKIES.EXPIRES_AT, expires_at, COOKIE_OPTIONS);
  setCookie(AUTH_COOKIES.USER_SESSION, JSON.stringify(data.user), COOKIE_OPTIONS);
}

/**
 * Registration mutation hook.
 *
 * Responsibilities:
 * 1. POST /api/auth/register with RegisterIn payload
 * 2. Persist tokens in cookies + Zustand store
 * 3. Redirect to /inscripcion (or nextUrl query param if present)
 * 4. Handle errors with toast
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useRegister() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation<
    { data: RegisterResponse; message?: string },
    Error,
    RegisterFormData
  >({
    mutationFn: async (payload) => {
      const response = await registerUser(payload);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Error al crear la cuenta");
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      persistAuthTokens(data);

      // Persist minimal user info to Zustand auth store
      setAuth({
        id: data.user.id,
        email: data.user.email,
        username: data.user.username,
        nombres: undefined,
        apellidos: undefined,
        rol: undefined,
      });

      const nextUrl = searchParams.get("nextUrl");
      const postAuth = consumePostAuthRedirect();
      const redirectTo = nextUrl
        ? decodeURIComponent(nextUrl)
        : (postAuth ?? "/inscripcion");

      if (message) toast.success(message);
      router.push(redirectTo);
      router.refresh();
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Error al crear la cuenta",
      );
    },
  });
}
