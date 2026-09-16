import type {
  InscripcionRepository,
  InscripcionWithRelations,
} from "@/core/repositories/inscripcion.repository";

export interface GetMyInscripcionDeps {
  inscripcionRepository: InscripcionRepository;
}

export async function getMyInscripcion(
  deps: GetMyInscripcionDeps,
  userId: string,
): Promise<InscripcionWithRelations | null> {
  return await deps.inscripcionRepository.findByUserId(userId);
}
