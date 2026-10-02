"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";
import type { RegisterFormData, RegisterResponse } from "../schemas";

/**
 * Register a new user account.
 * Backend: POST /api/auth/register
 */
export async function registerUser(
  payload: RegisterFormData,
): Promise<ApiResponse<RegisterResponse>> {
  const { data } = await api.post<ApiResponse<RegisterResponse>>(
    "/auth/register",
    payload,
  );
  return data;
}
