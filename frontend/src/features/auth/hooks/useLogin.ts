"use client";

import { useMutation } from "@tanstack/react-query";
import { setCookie } from "cookies-next";
import { api } from "@/lib/api";
import { AUTH_COOKIES } from "@/lib/auth";
import type { ApiResponse } from "@/types/api.types";
import type {
  LoginUsernameFormData,
  LoginDniFormData,
  LoginEmailFormData,
  MeResponse,
} from "../schemas";

// Union payload type — discriminated by which field is present
export type LoginPayload =
  | LoginUsernameFormData
  | LoginDniFormData
  | LoginEmailFormData;

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_at: string;
  user: MeResponse;
}

function resolveLogin(payload: LoginPayload): {
  endpoint: string;
  body: Record<string, string>;
} {
  if ("username" in payload) {
    return {
      endpoint: "/auth/login/username",
      body: { username: payload.username, password: payload.password },
    };
  }
  if ("dni" in payload) {
    return {
      endpoint: "/auth/login/dni",
      body: { dni: payload.dni, password: payload.password },
    };
  }
  // email — last case
  return {
    endpoint: "/auth/login/email",
    body: { email: payload.email, password: payload.password },
  };
}

export function useLogin() {
  return useMutation<
    { data: MeResponse; message?: string },
    Error,
    LoginPayload
  >({
    mutationFn: async (payload) => {
      const { endpoint, body } = resolveLogin(payload);
      const loginResponse = await api.post<ApiResponse<LoginResponse>>(
        endpoint,
        body,
      );

      if (!loginResponse.data?.success || !loginResponse.data?.data) {
        throw new Error(
          loginResponse.data?.error?.message ?? "Error al iniciar sesión",
        );
      }

      const user = persistAuthAndReturnUser(loginResponse.data.data);
      return { data: user, message: loginResponse.data.message };
    },
  });
}

function persistAuthAndReturnUser(loginData: LoginResponse): MeResponse {
  const { access_token, refresh_token, expires_at, user } = loginData;

  const cookieOptions = {
    path: "/",
    secure: process.env.NEXT_PUBLIC_COOKIE_SECURE === "true",
    sameSite: "lax" as const,
    maxAge: 7 * 24 * 60 * 60,
    httpOnly: false,
  };

  setCookie(AUTH_COOKIES.ACCESS_TOKEN, access_token, cookieOptions);
  setCookie(AUTH_COOKIES.REFRESH_TOKEN, refresh_token, cookieOptions);
  setCookie(AUTH_COOKIES.EXPIRES_AT, expires_at, cookieOptions);
  setCookie(AUTH_COOKIES.USER_SESSION, JSON.stringify(user), cookieOptions);

  return user;
}
