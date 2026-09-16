export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiErrorDetail | null;
  meta?: PaginationMeta | null;
}

export interface ApiErrorDetail {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown> | null;
}

export type ErrorCode =
  | "NOT_FOUND"
  | "VALIDATION_ERROR"
  | "PERMISSION_DENIED"
  | "CONFLICT"
  | "BUSINESS_ERROR"
  | "INTERNAL_ERROR";

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
