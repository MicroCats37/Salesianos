"use client";

import { useQuery } from "@tanstack/react-query";
import type { InscripcionWithRelations } from "@/core/repositories/inscripcion.repository";

export type MyInscripcion = InscripcionWithRelations;

export function useMyInscripcion() {
  return useQuery<MyInscripcion | null>({
    queryKey: ["inscripcion", "mine"],
    queryFn: async () => {
      const res = await fetch("/api/inscripcion/mine", {
        credentials: "include",
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch inscripcion");
      const json = await res.json();
      return json.success ? json.data : null;
    },
    retry: false,
    staleTime: 60 * 1000,
  });
}
