"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import type { InscripcionBackendPayload } from "../schemas/inscripcion.schema";
import type { InscripcionOut } from "../services/inscripcion.service";
import { createInscripcion } from "../services/inscripcion.service";

/**
 * Mutation hook for creating an inscription.
 *
 * Responsibilities:
 * 1. POST /api/inscripciones/ with InscripcionCreateIn payload
 * 2. Handle errors with toast
 * 3. Redirect to inscription detail page
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useCreateInscripcion() {
  const router = useRouter();

  return useMutation<
    { data: InscripcionOut; message?: string },
    Error,
    InscripcionBackendPayload
  >({
    mutationFn: async (payload) => {
      const response = await createInscripcion(payload);
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al crear la inscripción",
        );
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      if (message) toast.success(message);
      router.push(`/dashboard/inscripcion/${data.id}`);
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al crear la inscripción",
      );
    },
  });
}
