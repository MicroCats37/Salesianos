import {
  type QueryKey,
  type UseQueryOptions,
  useQuery,
} from "@tanstack/react-query";
import type { AxiosError, AxiosRequestConfig } from "axios";
import type { ZodType } from "zod";
import { getErrorMessage, notify } from "@/errors";
import api from "@/lib/api";
import { buildQueryKey } from "@/shared/utils/query-keys";
import {
  type DatasetKind,
  datasetQueryOptions,
} from "@/shared/utils/query-options";
import { relanzarSiCancelacion } from "./cancelacion";

interface UseApiQueryProps<T, TData = T> {
  queryKey: QueryKey;
  url: string | null;
  schema: ZodType<T>;
  params?: Record<string, unknown>;
  /**
   * The configuration of the request: the headers of the endpoint (a token
   * that travels in a header, not in the query) and its timeout.
   */
  config?: AxiosRequestConfig;
  showToast?: boolean;
  queryOptions?: Omit<
    UseQueryOptions<T, ApiQueryError, TData>,
    "queryKey" | "queryFn"
  >;
}

/**
 * Error class that preserves axios response status for status-aware error handling.
 * Thrown instead of plain Error so callers can distinguish 404 (not found) from
 * 503/timeout (service unavailable).
 */
export class ApiQueryError extends Error {
  constructor(
    message: string,
    public readonly status: number | undefined,
  ) {
    super(message);
    this.name = "ApiQueryError";
  }
}

/**
 * The read of a resource.
 *
 * The body is parsed by the Zod mirror of the wrapper: an answer that does not
 * match the contract is a failure, never a partially trusted value.
 */
async function fetchApiResource<T>(
  url: string,
  schema: ZodType<T>,
  params?: Record<string, unknown>,
  config?: AxiosRequestConfig,
  signal?: AbortSignal,
): Promise<T> {
  const { data } = await api.get(url, { ...config, params, signal });
  return schema.parse(data);
}

export function useApiQuery<T, TData = T>({
  queryKey,
  url,
  schema,
  params,
  config,
  showToast = true,
  queryOptions,
}: UseApiQueryProps<T, TData>) {
  const isEnabled = !!url && queryOptions?.enabled !== false;

  /**
   * EVERY parameter that changes the answer travels in the key, and a
   * parameter that is `undefined` does NOT create a second cache entry.
   */
  const finalQueryKey = buildQueryKey(queryKey, params);

  return useQuery<T, ApiQueryError, TData>({
    queryKey: finalQueryKey,
    queryFn: async ({ signal }) => {
      if (!url) throw new Error("URL is required");

      try {
        return await fetchApiResource(url, schema, params, config, signal);
      } catch (error) {
        relanzarSiCancelacion(error);
        const axiosError = error as AxiosError;
        const msg = getErrorMessage(error);
        if (showToast) notify.error(msg);
        // Preserve status code so callers can distinguish error types
        throw new ApiQueryError(msg, axiosError.response?.status);
      }
    },
    enabled: isEnabled,
    // Type assertion needed: queryOptions uses Error type for compatibility,
    // but runtime behavior is correct since ApiQueryError extends Error
    ...(queryOptions as Omit<
      UseQueryOptions<T, ApiQueryError, TData>,
      "queryKey" | "queryFn"
    >),
  });
}

export interface ApiQueryOptionsInput<T> {
  queryKey: QueryKey;
  url: string;
  schema: ZodType<T>;
  params?: Record<string, unknown>;
  /** The configuration of the request: its headers and its timeout. */
  config?: AxiosRequestConfig;
  /** The kind of dataset, which decides the staleness of the read. */
  kind?: DatasetKind;
  staleTime?: number;
  gcTime?: number;
}

/**
 * The `queryOptions` of a read.
 *
 * It is the SAME read that `useApiQuery` performs, with the SAME key and the
 * SAME policy: a prefetch, a server-side hydration or a component read share
 * one cache entry.
 */
export function apiQueryOptions<T>({
  queryKey,
  url,
  schema,
  params,
  config,
  kind = "comercial",
  staleTime,
  gcTime,
}: ApiQueryOptionsInput<T>) {
  return datasetQueryOptions<T>({
    queryKey: buildQueryKey(queryKey, params),
    queryFn: () => fetchApiResource(url, schema, params, config),
    kind,
    staleTime,
    gcTime,
  });
}
