"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";
import {
  type PaqueteDetailContract,
  PaqueteDetailContractSchema,
  type PaqueteListContract,
  PaqueteListContractSchema,
  paqueteQueryKeys,
} from "../schemas/paquete.schema";

/**
 * Fetch package list for cards and package selection.
 * Uses PaqueteListContract schema — lightweight for card rendering.
 * Trailing slash required for Django/Nginx caching.
 */
export async function fetchPaqueteList(): Promise<PaqueteListContract[]> {
  const { data } = await api.get<ApiResponse<PaqueteListContract[]>>(
    "/catalogo/paquetes/",
  );

  if (!data.success || !data.data) {
    throw new Error(data.message ?? "Error al cargar paquetes");
  }

  // Validate and parse each item with Zod
  return data.data.map((item) => {
    const result = PaqueteListContractSchema.safeParse(item);
    if (!result.success) {
      console.error(
        "PaqueteListContract validation failed for item:",
        JSON.stringify(item),
        "issues:",
        result.error.issues.map((i) => ({
          path: i.path.join("."),
          code: i.code,
          message: i.message,
        })),
      );
      // Return raw data for display continuity but log the contract mismatch
    }
    return result.success ? result.data : (item as PaqueteListContract);
  });
}

/**
 * Fetch package detail for wizard configuration.
 * Uses PaqueteDetailContract schema — complete data for team creation.
 * Trailing slash required for Django/Nginx caching.
 */
export async function fetchPaqueteDetail(
  id: string,
): Promise<PaqueteDetailContract> {
  const { data } = await api.get<ApiResponse<PaqueteDetailContract>>(
    `/catalogo/paquetes/${id}/`,
  );

  if (!data.success || !data.data) {
    throw new Error(data.message ?? "Error al cargar detalle del paquete");
  }

  const result = PaqueteDetailContractSchema.safeParse(data.data);
  if (!result.success) {
    console.error(
      "PaqueteDetailContract validation failed:",
      result.error.format(),
    );
    // Fallback to raw data for display continuity
    return data.data as PaqueteDetailContract;
  }

  return result.data;
}

// ── Re-export query keys for use in hooks ─────────────────────────────────────

export { paqueteQueryKeys };
