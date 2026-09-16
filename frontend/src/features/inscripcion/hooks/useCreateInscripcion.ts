"use client";

import { useMutation } from "@tanstack/react-query";
import type { InscripcionPayload } from "../schemas";
import { createInscripcion } from "../services/inscripcion.service";

export function useCreateInscripcion() {
  return useMutation({
    mutationFn: async (payload: InscripcionPayload) => {
      const res = await createInscripcion(payload);
      // When the server returns { success: false, error: {...} } (e.g. 409 duplicate),
      // throw a normal Error so react-query treats it as a mutation error.
      // GenericForm will catch it via handleApiError and show a toast.
      if (!res.success) {
        const message = res.error?.message ?? "Error al crear la inscripción";
        throw new Error(message);
      }
      return res;
    },
  });
}
