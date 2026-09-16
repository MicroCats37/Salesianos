"use client";

import { useMutation } from "@tanstack/react-query";
import type { InscripcionWithRelations } from "@/core/repositories/inscripcion.repository";
import api from "@/lib/api";
import type { ApiResponse } from "@/shared/types/api.types";
import type { InscripcionPayload } from "../schemas";

export interface UpdateInscripcionPayload {
  teamName?: string;
  deportistas?: InscripcionPayload["deportistas"];
  equiposConfig?: Array<{ disciplinaId: string; categoriaId: string }>;
}

export async function updateInscripcionService(
  id: string,
  payload: UpdateInscripcionPayload,
): Promise<ApiResponse<InscripcionWithRelations>> {
  const { data } = await api.patch<ApiResponse<InscripcionWithRelations>>(
    `/api/inscripcion/${id}`,
    payload,
  );
  return data;
}

export function useUpdateInscripcion() {
  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: string;
      payload: UpdateInscripcionPayload;
    }) => {
      const res = await updateInscripcionService(id, payload);
      if (!res.success) {
        const message =
          res.error?.message ?? "Error al actualizar la inscripción";
        throw new Error(message);
      }
      return res;
    },
  });
}
