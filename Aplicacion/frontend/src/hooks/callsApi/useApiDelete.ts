import { type UseMutationOptions, useMutation } from "@tanstack/react-query";
import type { AxiosError, AxiosResponse } from "axios";
import { handleApiError, notify } from "@/errors";
import api from "@/lib/api";

/**
 * Classic style: caller provides id (number | string).
 * Custom style: caller provides full payload with optional baseUrl override.
 */
type DeleteVariables<TPayload = never> = TPayload extends never
  ? number | string
  : TPayload & { baseUrl?: string };

interface UseApiDeleteProps<TData, TPayload = never> {
  baseUrl?: string;
  /** Custom URL builder — receives variables (or void if no payload), returns full URL.
   *  When provided, variables are treated as custom payload style.
   *  For classic id-based delete, omit this. */
  getUrl?: (variables: DeleteVariables<TPayload>) => string;
  showToast?: boolean;
  showSuccessToast?: boolean;
  options?: Omit<
    UseMutationOptions<TData, AxiosError, DeleteVariables<TPayload>>,
    "mutationFn"
  >;
}

export function useApiDelete<TData = unknown, TPayload = never>({
  baseUrl,
  getUrl,
  showToast = true,
  showSuccessToast = true,
  options,
}: UseApiDeleteProps<TData, TPayload>) {
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

        const response: AxiosResponse<unknown> = await api.delete(url);
        if (showSuccessToast) {
          const envelope = response.data as { message?: string } | null;
          if (envelope && typeof envelope.message === "string" && envelope.message.length > 0) {
            notify.success(envelope.message);
          }
        }
        return response.data as TData;
      } catch (error) {
        const apiError = handleApiError(error);
        if (showToast) notify.error(apiError.message);
        throw error;
      }
    },
    ...options,
  });
}
