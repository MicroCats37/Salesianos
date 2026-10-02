import { type UseMutationOptions, useMutation } from "@tanstack/react-query";
import type { AxiosError, AxiosResponse } from "axios";
import type { ZodType } from "zod";
import { getErrorMessage, handleApiError, notify } from "@/errors";
import api from "@/lib/api";
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
  options,
}: UseApiCreateProps<TData, TVariables>) {
  return useMutation<TData, AxiosError, TVariables>({
    mutationFn: async (variables) => {
      try {
        const payload = buildApiPayload(variables);
        const response: AxiosResponse<unknown> = await api.post(url, payload);
        const envelope = response.data as { message?: string } | null;
        if (showSuccessToast && envelope && typeof envelope.message === "string" && envelope.message.length > 0) {
          notify.success(envelope.message);
        }
        return schema ? schema.parse(response.data) : (response.data as TData);
      } catch (error) {
        const apiError = handleApiError(error);
        if (showToast) notify.error(apiError.message);
        throw error;
      }
    },
    ...options,
  });
}
