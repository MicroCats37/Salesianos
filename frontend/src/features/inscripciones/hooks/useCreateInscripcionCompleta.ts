"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type {
  InscripcionCompletaOut,
  InscripcionCompletaPayload,
} from "../services/inscripcion.service";
import { createInscripcionCompleta } from "../services/inscripcion.service";

/**
 * Arguments accepted by `useCreateInscripcionCompleta`.
 *
 * The wizard builds the payload directly from form state + selected paquete —
 * there is NO intermediate mapping function in `inscripcion.schema`. The
 * estado is always `"BORRADOR"` for atomic creation.
 */
export interface CreateInscripcionCompletaArgs {
  evento_id: string;
  paquete_id: string;
  promocion_id: string;
  fusion_promocion_id?: string | null;
  delegado_id?: string | null;
  cantidad: number;
  equipos: Array<{
    disciplina_id: string;
    categoria_id?: string | null;
    nombre: string;
  }>;
  observacion?: string;
  /** Quoted unit price — triggers server-side price revalidation when set. */
  precio_unitario_cotizado?: number | null;
  /** Quotation version — metadata propagated to backend, not yet validated. */
  cotizacion_version?: number | null;
}

export interface CreateInscripcionCompletaResult {
  data: InscripcionCompletaOut;
  message?: string;
}

/**
 * Mutation hook for atomic inscription + compra + equipos creation.
 *
 * Responsibilities:
 * 1. POST /api/inscripciones/completa/ with `InscripcionCompletaPayload`
 * 2. Handle errors with toast
 * 3. Redirect to inscription detail page on success
 * 4. Always sends `estado: "BORRADOR"` (canonical creation state).
 */
export function useCreateInscripcionCompleta() {
  const router = useRouter();

  return useMutation<
    CreateInscripcionCompletaResult,
    Error,
    CreateInscripcionCompletaArgs
  >({
    mutationFn: async (args) => {
      const servicePayload: InscripcionCompletaPayload = {
        evento_id: args.evento_id,
        paquete_id: args.paquete_id,
        promocion_id: args.promocion_id,
        fusion_promocion_id: args.fusion_promocion_id ?? null,
        delegado_id: args.delegado_id ?? null,
        cantidad: args.cantidad,
        equipos: args.equipos,
        estado: "BORRADOR",
        observacion: args.observacion ?? "",
        precio_unitario_cotizado: args.precio_unitario_cotizado ?? null,
        cotizacion_version: args.cotizacion_version ?? null,
      };
      const response = await createInscripcionCompleta(servicePayload);
      if (!response.success || !response.data) {
        const err = response.error;
        // Carry the backend error code so the caller can handle specific conflicts.
        const error = new Error(
          err?.message ?? "Error al crear la inscripción",
        ) as Error & {
          code?: string;
          precio_actual?: number;
          total_nuevo?: number;
        };
        error.code = err?.code;
        if (err?.code === "PRECIO_CAMBIO") {
          // Attach new price info so the UI can show the updated quotation.
          error.precio_actual = (err as unknown as Record<string, unknown>)
            ?.precio_actual as number;
          error.total_nuevo = (err as unknown as Record<string, unknown>)
            ?.total_nuevo as number;
        }
        throw error;
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      if (message) toast.success(message);
      router.push(`/dashboard/inscripcion/${data.inscripcion_id}`);
    },
    onError: (error) => {
      const err = error as Error & {
        code?: string;
        precio_actual?: number;
        total_nuevo?: number;
      };
      if (err.code === "PRECIO_CAMBIO") {
        toast.error(
          `⚠️ El precio cambió. Nuevo total: S/${(err.total_nuevo ?? 0).toFixed(2)} por persona. Recalcula la cotización e intenta nuevamente.`,
          { duration: 8000 },
        );
      } else {
        toast.error(
          error instanceof Error
            ? error.message
            : "Error al crear la inscripción",
        );
      }
    },
  });
}
