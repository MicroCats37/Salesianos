import type {
  ApiErrorDetail,
  ErrorCode,
  PaginationMeta,
} from "@/shared/types/api.types";

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiErrorDetail | null;
  meta?: PaginationMeta | null;
}

export type { ApiErrorDetail, ErrorCode, PaginationMeta };

export function successData<T>(data: T, meta?: PaginationMeta | null) {
  return { success: true as const, data, error: null, meta: meta ?? null };
}

export function errorData(
  code: ErrorCode,
  message: string,
  details?: Record<string, unknown> | null,
) {
  return {
    success: false as const,
    data: null,
    error: { code, message, details: details ?? null },
    meta: null,
  };
}
