import { NextResponse } from "next/server";
import { isAppError } from "@/core/errors";
import type {
  ApiErrorDetail,
  ApiResponse,
  ErrorCode,
  PaginationMeta,
} from "@/shared/types/api.types";

export function jsonSuccess<T>(
  data: T,
  status = 200,
  meta?: PaginationMeta | null,
): NextResponse<ApiResponse<T>> {
  return NextResponse.json(
    { success: true, data, error: null, meta: meta ?? null },
    { status },
  );
}

export function jsonError(
  detail: ApiErrorDetail,
  status: number,
): NextResponse<ApiResponse<null>> {
  return NextResponse.json(
    { success: false, data: null, error: detail, meta: null },
    { status },
  );
}

export function jsonInternalError(
  message = "Error interno del servidor",
): NextResponse<ApiResponse<null>> {
  return jsonError(
    { code: "INTERNAL_ERROR" satisfies ErrorCode, message, details: null },
    500,
  );
}

export function jsonFromUnknownError(
  error: unknown,
  context: string,
): NextResponse<ApiResponse<null>> {
  if (isAppError(error)) {
    return jsonError(error.toApiError(), error.statusCode);
  }
  console.error(`[${context}] unexpected error:`, error);
  return jsonInternalError();
}
