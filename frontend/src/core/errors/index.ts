import type { ApiErrorDetail, ErrorCode } from "@/shared/types/api.types";

export abstract class AppError extends Error {
  abstract readonly code: ErrorCode;
  abstract readonly statusCode: number;
  readonly details: Record<string, unknown> | null;

  constructor(message: string, details: Record<string, unknown> | null = null) {
    super(message);
    this.name = this.constructor.name;
    this.details = details;
    Object.setPrototypeOf(this, new.target.prototype);
  }

  toApiError(): ApiErrorDetail {
    return { code: this.code, message: this.message, details: this.details };
  }
}

export class NotFoundError extends AppError {
  readonly code = "NOT_FOUND" as const;
  readonly statusCode = 404;
  constructor(
    message = "Resource not found",
    details: Record<string, unknown> | null = null,
  ) {
    super(message, details);
  }
}

export class ValidationError extends AppError {
  readonly code = "VALIDATION_ERROR" as const;
  readonly statusCode = 422;
  readonly fieldErrors: Record<string, string[]> | null;
  constructor(
    message = "Validation failed",
    fieldErrors: Record<string, string[]> | null = null,
  ) {
    super(message, fieldErrors ? { fieldErrors } : null);
    this.fieldErrors = fieldErrors;
  }
}

export class PermissionDeniedError extends AppError {
  readonly code = "PERMISSION_DENIED" as const;
  readonly statusCode = 403;
  constructor(
    message = "Permission denied",
    details: Record<string, unknown> | null = null,
  ) {
    super(message, details);
  }
}

export class ConflictError extends AppError {
  readonly code = "CONFLICT" as const;
  readonly statusCode = 409;
  constructor(
    message = "Resource conflict",
    details: Record<string, unknown> | null = null,
  ) {
    super(message, details);
  }
}

export class BusinessError extends AppError {
  readonly code = "BUSINESS_ERROR" as const;
  readonly statusCode = 400;
  constructor(
    message = "Business rule violated",
    details: Record<string, unknown> | null = null,
  ) {
    super(message, details);
  }
}

export class InternalError extends AppError {
  readonly code = "INTERNAL_ERROR" as const;
  readonly statusCode = 500;
  constructor(
    message = "Internal server error",
    details: Record<string, unknown> | null = null,
  ) {
    super(message, details);
  }
}

export function isAppError(e: unknown): e is AppError {
  return e instanceof AppError;
}
