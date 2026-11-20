import {
  type QueryKey,
  type UseMutationOptions,
  type UseMutationResult,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError, AxiosRequestConfig } from "axios";
import type { ZodType } from "zod";
import { handleApiError, notify } from "@/errors";
import { apiSend } from "@/lib/api";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import { buildApiPayload } from "@/utils";
import { relanzarSiCancelacion } from "./cancelacion";

/** The variables of a write that is scoped to a record. */
export interface VariablesAcopladas<TPayload> {
  /** The record that owns the write. It NEVER travels in the payload. */
  id: number | string;
  /** The payload of the write. */
  data: TPayload;
  /**
   * The extra identifiers of the path.
   *
   * A route that carries TWO identifiers (`{id}/{equipo_id}`) keeps them here:
   * they travel in the URL and NEVER in the payload.
   */
  params?: Record<string, string>;
}

interface UseApiCreateDirectProps<TData, TVariables> {
  /**
   * The endpoint of the creation.
   *
   * A function receives the variables of the mutation: a route scoped to an
   * identifier is built from the data of the write, not spelled by hand.
   */
  url: string | ((variables: TVariables) => string);
  schema?: ZodType<TData>;
  /**
   * The configuration of the request: the headers of the endpoint (a token
   * that travels in a header, not in the query) and its timeout.
   */
  config?: AxiosRequestConfig;
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

interface UseApiCreateScopedProps<TData, TPayload> {
  /**
   * The URL of the endpoint, built from the variables.
   *
   * The write is scoped to a record (`{id}/participantes`): the identifier
   * travels in the URL and NEVER in the payload.
   */
  getUrl: (variables: VariablesAcopladas<TPayload>) => string;
  schema?: ZodType<TData>;
  /** The configuration of the request: its headers and its timeout. */
  config?: AxiosRequestConfig;
  showToast?: boolean;
  showSuccessToast?: boolean;
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<
    UseMutationOptions<TData, AxiosError, VariablesAcopladas<TPayload>>,
    "mutationFn"
  >;
}

export function useApiCreate<TData = unknown, TVariables = unknown>(
  props: UseApiCreateDirectProps<TData, TVariables>,
): UseMutationResult<TData, AxiosError, TVariables>;

export function useApiCreate<TData = unknown, TPayload = unknown>(
  props: UseApiCreateScopedProps<TData, TPayload>,
): UseMutationResult<TData, AxiosError, VariablesAcopladas<TPayload>>;

export function useApiCreate<TData = unknown, TVariables = unknown>(
  props:
    | UseApiCreateDirectProps<TData, TVariables>
    | UseApiCreateScopedProps<TData, unknown>,
) {
  const queryClient = useQueryClient();

  const esAcoplado = "getUrl" in props;
  const directo = props as UseApiCreateDirectProps<TData, TVariables>;
  const acoplado = props as UseApiCreateScopedProps<TData, unknown>;

  const {
    schema,
    config,
    showToast = true,
    showSuccessToast = true,
    invalidateKeys = [],
    options,
  } = directo;

  return useMutation<TData, AxiosError, TVariables>({
    mutationFn: async (variables) => {
      try {
        const cuerpo = esAcoplado
          ? (variables as unknown as VariablesAcopladas<unknown>).data
          : variables;
        const payload = buildApiPayload(cuerpo);

        const destino = esAcoplado
          ? acoplado.getUrl(variables as unknown as VariablesAcopladas<unknown>)
          : typeof directo.url === "function"
            ? directo.url(variables)
            : directo.url;

        const { status, data } = await apiSend<unknown>(
          "post",
          destino,
          payload,
          config,
        );

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
        relanzarSiCancelacion(error);
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
