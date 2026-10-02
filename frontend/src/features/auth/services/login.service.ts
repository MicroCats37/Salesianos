"use server";

import { NextResponse } from "next/server";

/**
 * Login service — calls backend auth endpoint.
 * Backend: POST /api/auth/login with { identifier, password }
 * Returns: { access, refresh, user }
 */

export interface LoginServiceInput {
  identifier: string;
  password: string;
}

export interface LoginServiceResult {
  access: string;
  refresh: string;
  expiresAt: string;
  user: {
    id: string;
    email: string;
    nombres?: string;
    apellidos?: string;
    rol?: string;
  };
}

export async function loginService(
  input: LoginServiceInput,
): Promise<LoginServiceResult> {
  const backendUrl =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const response = await fetch(`${backendUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      identifier: input.identifier,
      password: input.password,
    }),
  });

  if (!response.ok) {
    let errorMessage = "Error al iniciar sesión";
    try {
      const errorData = (await response.json()) as {
        error?: { message?: string };
        detail?: string;
      };
      errorMessage =
        errorData?.error?.message ||
        errorData?.detail ||
        `Código ${response.status}`;
    } catch {
      errorMessage = `Error HTTP ${response.status}`;
    }
    throw new Error(errorMessage);
  }

  const data = (await response.json()) as {
    access?: string;
    refresh?: string;
    user?: LoginServiceResult["user"];
  };

  if (!data.access || !data.refresh || !data.user) {
    throw new Error("Respuesta inválida del servidor");
  }

  // Backend returns expires_at or we compute a safe fallback
  const expiresAt =
    data.access && typeof data.access === "object" && "expires_at" in data.access
      ? (data.access as { expires_at: string }).expires_at
      : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

  return {
    access: data.access as string,
    refresh: data.refresh as string,
    expiresAt,
    user: data.user,
  };
}
