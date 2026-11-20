import {
  type MutationFunction,
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

interface UseGenericCreateMutationOptions<TVars = unknown> {
  /**
   * The key of the dataset whose reads are invalidated when the creation
   * settles.
   */
  queryKey: QueryKey;
  /**
   * URL del POST — construye el mutationFn internamente (buildApiPayload +
   * apiSend + manejo de errores + toast), como useApiCreate. Alternativa a
   * `mutationFn`.
   */
  url?: string;
  /** mutationFn manual (modo original). Se usa si no se provee `url`. */
  mutationFn?: MutationFunction<unknown, TVars>;
  schema?: ZodType<unknown>;
  showToast?: boolean;
  /**
   * The keys invalidated when the mutation settles.
   */
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<UseMutationOptions<unknown, AxiosError, TVars>, "mutationFn">;
}

/**
 * A creation that NEVER writes into the cache.
 *
 * The server owns the position of the new item: it decides the order, the
 * page and the total. Writing it from the browser means guessing, and the
 * guess lands in EVERY cached page of the list (the same item twice, the
 * total inflated once per page). So the creation invalidates the dataset and
 * lets the server answer.
 */
export function useGenericCreateMutation<
  TItem extends { id: string | number } = { id: string | number },
  TVars = unknown,
>({
  queryKey,
  url,
  mutationFn,
  schema,
  showToast = true,
  invalidateKeys,
  options,
}: UseGenericCreateMutationOptions<TVars>) {
  const queryClient = useQueryClient();

  const internalMutationFn: MutationFunction<TItem | undefined, TVars> = url
    ? async (variables, _context) => {
        try {
          const payload = buildApiPayload(variables);
          const { status, data } = await apiSend<unknown>("post", url, payload);

          // 204 No Content: the body is empty and it is NEVER parsed.
          if (status === 204) return undefined;

          return (schema ? schema.parse(data) : data) as TItem | undefined;
        } catch (error) {
          const apiError = handleApiError(error);
          if (showToast) notify.error(apiError.message);
          throw error;
        }
      }
    : ((mutationFn ??
        (async () => {
          throw new Error(
            "useGenericCreateMutation: se requiere url o mutationFn",
          );
        })) as MutationFunction<TItem | undefined, TVars>);

  return useMutation<TItem | undefined, AxiosError, TVars>({
    mutationFn: async (variables, context) => {
      try {
        return await internalMutationFn(variables, context);
      } finally {
        await invalidateDatasets(queryClient, invalidateKeys ?? [queryKey]);
      }
    },
    ...options,
  });
}
