import axios, { type AxiosError, type AxiosInstance } from "axios";
import type { ApiErrorDetail, ApiResponse } from "@/shared/types/api.types";

const baseURL =
  typeof window === "undefined"
    ? (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000")
    : "";

export const api: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/api/auth/")
    ) {
      try {
        await axios.post("/api/auth/refresh", {}, { withCredentials: true });
        if (error.config) {
          return api.request(error.config);
        }
      } catch {
        // Refresh failed — let the error propagate
      }
    }
    return Promise.reject(error);
  },
);

export function unwrap<T>(response: { data: ApiResponse<T> }): T {
  if (!response.data.success || response.data.data === null) {
    throw new ApiCallError(
      response.data.error ?? {
        code: "INTERNAL_ERROR",
        message: "Unknown error",
      },
    );
  }
  return response.data.data;
}

export class ApiCallError extends Error {
  readonly code: string;
  readonly details: Record<string, unknown> | null;
  constructor(error: ApiErrorDetail) {
    super(error.message);
    this.name = "ApiCallError";
    this.code = error.code;
    this.details = error.details ?? null;
  }
}

export default api;
