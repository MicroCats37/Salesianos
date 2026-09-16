"use client";

import { useMutation } from "@tanstack/react-query";
import { updateInscripcionStatusAction } from "@/app/actions/inscripcion/update-status";

export function useUpdateInscripcionStatus() {
  return useMutation({
    mutationFn: (input: {
      inscripcionId: string;
      status: "en_revision" | "validada" | "observada" | "rechazada";
      observacion?: string;
    }) => updateInscripcionStatusAction(input),
  });
}
