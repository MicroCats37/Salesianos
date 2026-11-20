import {
  type QueryKey,
  type UseMutationOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError, AxiosRequestConfig } from "axios";
import type { ZodType } from "zod";
import { handleApiError, notify } from "@/errors";
import { apiSend } from "@/lib/api";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import { relanzarSiCancelacion } from "./cancelacion";

/**
 * Classic style: caller provides id (number | string).
 * Custom style: caller provides full payload with optional baseUrl override.
 */
type DeleteVariables<TPayload = never> = [TPayload] extends [never]
  ? number | string
  : TPayload & { baseUrl?: string };

interface UseApiDeleteProps<TData, TPayload = never> {
  baseUrl?: string;
  /** Custom URL builder — receives variables (or void if no payload), returns full URL.
   *  When provided, variables are treated as custom payload style.
   *  For classic id-based delete, omit this. */
  getUrl?: (variables: DeleteVariables<TPayload>) => string;
  /** The mirror of the answer. It is parsed when the endpoint answers. */
  schema?: ZodType<TData>;
  /** The configuration of the request: its headers and its timeout. */
  config?: AxiosRequestConfig;
  showToast?: boolean;
  showSuccessToast?: boolean;
  /**
   * The keys invalidated when the mutation settles. The invalidation is
   * EXPLICIT: a deletion declares the reads it dirties.
   */
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<
    UseMutationOptions<TData, AxiosError, DeleteVariables<TPayload>>,
    "mutationFn"
  >;
}

export function useApiDelete<TData = unknown, TPayload = never>({
  baseUrl,
  getUrl,
  schema,
  config,
  showToast = true,
  showSuccessToast = true,
  invalidateKeys = [],
  options,
}: UseApiDeleteProps<TData, TPayload>) {
  const queryClient = useQueryClient();

  return useMutation<TData, AxiosError, DeleteVariables<TPayload>>({
    mutationFn: async (variables) => {
      try {
        let url: string;

        if (getUrl) {
          url = getUrl(variables as DeleteVariables<TPayload>);
        } else if (typeof variables === "object" && "baseUrl" in variables) {
          // baseUrl override in variables
          url = (variables as { baseUrl: string }).baseUrl;
        } else {
          // Classic: baseUrl + id
          url = `${baseUrl}/${variables}`;
        }

        const { status, data } = await apiSend<unknown>(
          "delete",
          url,
          undefined,
          config,
        );

        // 204 No Content: the body is empty and it is NEVER parsed.
        if (status === 204) return undefined as unknown as TData;

        if (showSuccessToast) {
          const envelope = data as { message?: string } | null;
          if (
            envelope &&
            typeof envelope.message === "string" &&
            envelope.message.length > 0
          ) {
            notify.success(envelope.message);
          }
        }
        return schema ? schema.parse(data) : (data as TData);
      } catch (error) {
        relanzarSiCancelacion(error);
        const apiError = handleApiError(error);
        if (showToast) notify.error(apiError.message);
        throw error;
      } finally {
        /**
         * The invalidation lives in the mutation itself and NOT in
         * `onSettled`: a component that unmounts while the mutation is in
         * flight would never invalidate, and the cache would keep the deleted
         * item.
         */
        await invalidateDatasets(queryClient, invalidateKeys);
      }
    },
    ...options,
  });
}
