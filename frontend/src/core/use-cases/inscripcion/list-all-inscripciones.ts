import type {
  InscripcionRepository,
  InscripcionWithRelations,
} from "@/core/repositories/inscripcion.repository";
import type { InscripcionEstado } from "@/infra/drizzle/schema";

export interface ListAllInscripcionesDeps {
  inscripcionRepository: InscripcionRepository;
}

export interface ListAllInscripcionesInput {
  status?: InscripcionEstado;
  page?: number;
  pageSize?: number;
}

export interface ListAllInscripcionesResult {
  items: InscripcionWithRelations[];
  total: number;
}

export async function listAllInscripciones(
  deps: ListAllInscripcionesDeps,
  input: ListAllInscripcionesInput = {},
): Promise<ListAllInscripcionesResult> {
  return await deps.inscripcionRepository.listAll(input);
}
