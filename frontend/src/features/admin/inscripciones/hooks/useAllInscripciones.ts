"use client";

import { useQuery } from "@tanstack/react-query";
import type { InscripcionEstado } from "@/infra/drizzle/schema";

export interface AdminJugadorItem {
  nombre: string;
  apellido: string;
  tipoDocumento: string;
  numeroDocumento: string;
  telefono: string | null;
  whatsapp: string | null;
  rolDisciplina: string;
  acreditacion: string;
  shirtSize: string | null;
  equipos: { disciplinaNombre: string; categoriaNombre: string }[];
}

export interface AdminInscripcionListItem {
  inscripcion: {
    id: string;
    userId: string;
    promocionId: string;
    basesId: string;
    paqueteMonto: number;
    status: InscripcionEstado;
    observacion: string | null;
    createdAt: string;
  };
  equiposCount: number;
  jugadoresCount: number;
  userNombre: string;
  userApellido: string;
  userDni: string;
  jugadores: AdminJugadorItem[];
}

export interface AdminInscripcionListResponse {
  items: AdminInscripcionListItem[];
  total: number;
}

export function useAllInscripciones(filter?: {
  status?: InscripcionEstado;
  page?: number;
  pageSize?: number;
}) {
  return useQuery<AdminInscripcionListResponse>({
    queryKey: ["admin", "inscripciones", filter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filter?.status) params.set("status", filter.status);
      if (filter?.page) params.set("page", String(filter.page));
      if (filter?.pageSize) params.set("pageSize", String(filter.pageSize));
      const res = await fetch(`/api/admin/inscripciones?${params.toString()}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to fetch inscripciones");
      const json = await res.json();
      return json.success ? json.data : { items: [], total: 0 };
    },
    staleTime: 30 * 1000,
  });
}
