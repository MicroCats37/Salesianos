import {
  type QueryKey,
  type UseMutationOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import type { ZodType } from "zod";
import { handleApiError, notify } from "@/errors";
import { apiSend } from "@/lib/api";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import { buildApiPayload } from "@/utils";

interface UseApiCreateProps<TData, TVariables> {
  url: string;
  schema?: ZodType<TData>;
  showToast?: boolean;
  /**
   * When the backend includes a top-level `message` on the response envelope,
   * trigger `notify.success(message)` automatically. Defaults to true so
   * generic hooks surface success feedback without per-call boilerplate.
   */
  showSuccessToast?: boolean;
  /**
   * The keys invalidated when the mutation settles.
   *
   * The invalidation is EXPLICIT: a mutation that changes a dataset declares
   * the keys it dirties. A mutation that declares nothing dirties nothing.
   */
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<
    UseMutationOptions<TData, AxiosError, TVariables>,
    "mutationFn"
  >;
}

export function useApiCreate<TData = unknown, TVariables = unknown>({
  url,
  schema,
  showToast = true,
  showSuccessToast = true,
  invalidateKeys = [],
  options,
}: UseApiCreateProps<TData, TVariables>) {
  const queryClient = useQueryClient();

  return useMutation<TData, AxiosError, TVariables>({
    mutationFn: async (variables) => {
      try {
        const payload = buildApiPayload(variables);
        const { status, data } = await apiSend<unknown>("post", url, payload);

        // 204 No Content: the body is empty and it is NEVER parsed.
        if (status === 204) return undefined as unknown as TData;

        const envelope = data as { message?: string } | null;
        if (
          showSuccessToast &&
          envelope &&
          typeof envelope.message === "string" &&
          envelope.message.length > 0
        ) {
          notify.success(envelope.message);
        }
        return schema ? schema.parse(data) : (data as TData);
      } catch (error) {
        const apiError = handleApiError(error);
        if (showToast) notify.error(apiError.message);
        throw error;
      } finally {
        /**
         * The invalidation lives in the mutation itself and NOT in
         * `onSettled`: a component that unmounts while the mutation is in
         * flight would never invalidate, and the cache would keep the old
         * answer.
         */
        await invalidateDatasets(queryClient, invalidateKeys);
      }
    },
    ...options,
  });
}
