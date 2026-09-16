import api from "@/lib/api";
import type { ApiResponse } from "@/shared/types/api.types";

export interface Promocion {
  id: string;
  nombre: string | null;
  anio: number;
  activa: boolean;
  fechaInicio: string | null;
  fechaFin: string | null;
}

export interface Disciplina {
  id: string;
  nombre: string;
  descripcion: string | null;
  activa: boolean;
}

export interface Base {
  id: string;
  titulo: string;
  archivoUrl: string | null;
  activa: boolean;
  fechaPublicacion: string | null;
}

export async function getPromociones(): Promise<ApiResponse<Promocion[]>> {
  const { data } = await api.get<ApiResponse<Promocion[]>>(
    "/api/catalogs/promociones",
  );
  return data;
}

export async function getDisciplinas(): Promise<ApiResponse<Disciplina[]>> {
  const { data } = await api.get<ApiResponse<Disciplina[]>>(
    "/api/catalogs/disciplinas",
  );
  return data;
}

export async function getBases(): Promise<ApiResponse<Base | null>> {
  const { data } = await api.get<ApiResponse<Base | null>>(
    "/api/catalogs/bases",
  );
  return data;
}
