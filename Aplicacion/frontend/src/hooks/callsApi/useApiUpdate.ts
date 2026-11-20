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

// ---------------------------------------------------------------------------
// Variable types
// ---------------------------------------------------------------------------

/** Classic backward-compatible shape: caller provides id + data. */
type ClassicVariables<TPayload> = {
  id: number | string;
  data: TPayload;
};

/** Direct payload shape (like useApiCreate): variable IS the payload. */
type DirectVariables<TPayload> = TPayload;

/**
 * The success message of the envelope.
 *
 * `message` lives in the ROOT of the envelope and it is `null` when the
 * endpoint declares none: it is read, never invented.
 */
function maybeToastSuccess(payload: unknown, showSuccessToast: boolean): void {
  if (!showSuccessToast) return;

  const envelope = payload as { message?: string } | null;
  if (
    envelope &&
    typeof envelope.message === "string" &&
    envelope.message.length > 0
  ) {
    notify.success(envelope.message);
  }
}

// ---------------------------------------------------------------------------
// Props — two modes
// ---------------------------------------------------------------------------

/** Direct-mode props (url provided): behaves like useApiCreate. */
interface UseApiUpdateDirectProps<TData, TVariables> {
  /**
   * Direct URL for the endpoint. Variables are sent as-is as payload.
   *
   * A function receives the variables of the mutation: a route scoped to an
   * identifier is built from the data of the write, not spelled by hand.
   */
  url: string | ((variables: DirectVariables<TVariables>) => string);
  schema?: ZodType<TData>;
  method?: "PUT" | "PATCH";
  /** The configuration of the request: its headers and its timeout. */
  config?: AxiosRequestConfig;
  showToast?: boolean;
  showSuccessToast?: boolean;
  /**
   * The keys invalidated when the mutation settles. The invalidation is
   * EXPLICIT: a mutation declares the reads it dirties.
   */
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<
    UseMutationOptions<TData, AxiosError, DirectVariables<TVariables>>,
    "mutationFn"
  >;
}

/** Classic-mode props (baseUrl provided): expects { id, data } variables. */
interface UseApiUpdateClassicProps<TData, TPayload> {
  /** Base URL; id is appended automatically. */
  baseUrl?: string;
  /**
   * The URL of the endpoint, built from the variables.
   *
   * It is the escape hatch for the routes that are NOT `baseUrl + /id`: a
   * sub-route of a record (`{id}/logo`) declares its own shape.
   */
  getUrl?: (variables: ClassicVariables<TPayload>) => string;
  schema?: ZodType<TData>;
  method?: "PUT" | "PATCH";
  /** The configuration of the request: its headers and its timeout. */
  config?: AxiosRequestConfig;
  showToast?: boolean;
  showSuccessToast?: boolean;
  /** The keys invalidated when the mutation settles. */
  invalidateKeys?: readonly QueryKey[];
  options?: Omit<
    UseMutationOptions<TData, AxiosError, ClassicVariables<TPayload>>,
    "mutationFn"
  >;
}

// ---------------------------------------------------------------------------
// Hook with overloads for clean typing
// ---------------------------------------------------------------------------

/**
 * Unified update hook supporting two calling conventions:
 *
 * **Direct mode** (url prop — like useApiCreate):
 *   const m = useApiUpdate({ url: `/bungalows/${id}/imagenes` })
 *   m.mutate(payload)   // payload goes directly through buildApiPayload
 *
 * **Classic mode** (baseUrl prop — backward-compatible):
 *   const m = useApiUpdate({ baseUrl: "/users" })
 *   m.mutate({ id: 5, data: { name: "Ana" } })   // PATCH /users/5 with data
 */

// Overload 1: direct mode
export function useApiUpdate<TData, TVariables>(
  props: UseApiUpdateDirectProps<TData, TVariables>,
): UseMutationResult<TData, AxiosError, DirectVariables<TVariables>>;

// Overload 2: classic mode
export function useApiUpdate<TData, TPayload>(
  props: UseApiUpdateClassicProps<TData, TPayload>,
): UseMutationResult<TData, AxiosError, ClassicVariables<TPayload>>;

// Implementation
export function useApiUpdate<TData = unknown, TVariables = unknown>(
  props:
    | UseApiUpdateDirectProps<TData, TVariables>
    | UseApiUpdateClassicProps<TData, unknown>,
): UseMutationResult<TData, AxiosError, TVariables> {
  const queryClient = useQueryClient();

  // ------------------------------------------------------------------
  // Detect mode: 'url' key present means direct mode
  // ------------------------------------------------------------------
  const esDirecto =
    "url" in props &&
    (props as UseApiUpdateDirectProps<TData, TVariables>).url !== undefined;

  const directo = props as UseApiUpdateDirectProps<TData, TVariables>;
  const clasico = props as UseApiUpdateClassicProps<TData, unknown>;

  const {
    schema,
    method = "PUT",
    config,
    showToast = true,
    showSuccessToast = true,
    invalidateKeys = [],
    options,
  } = directo;

  return useMutation<TData, AxiosError, TVariables>({
    mutationFn: async (variables) => {
      try {
        const esClasico = !esDirecto;
        const cuerpo = esClasico
          ? (variables as unknown as ClassicVariables<unknown>).data
          : variables;
        const payload = buildApiPayload(cuerpo);

        const destino = esDirecto
          ? typeof directo.url === "function"
            ? directo.url(variables)
            : directo.url
          : clasico.getUrl
            ? clasico.getUrl(variables as unknown as ClassicVariables<unknown>)
            : `${clasico.baseUrl}/${(variables as unknown as ClassicVariables<unknown>).id}`;

        const { status, data } = await apiSend<unknown>(
          method,
          destino,
          payload,
          config,
        );

        // 204 No Content: the body is empty and it is NEVER parsed.
        if (status === 204) return undefined as unknown as TData;

        maybeToastSuccess(data, showSuccessToast);
        return schema ? schema.parse(data) : (data as TData);
      } catch (error) {
        relanzarSiCancelacion(error);
        const apiError = handleApiError(error);
        if (showToast) notify.error(apiError.message);
        throw error;
      } finally {
        await invalidateDatasets(queryClient, invalidateKeys);
      }
    },
    ...options,
  }) as unknown as UseMutationResult<TData, AxiosError, TVariables>;
}
