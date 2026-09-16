import { NotFoundError, ValidationError } from "@/core/errors";
import type { InscripcionRepository } from "@/core/repositories/inscripcion.repository";
import type { Inscripcion, InscripcionEstado } from "@/infra/drizzle/schema";

const ADMIN_TRANSITIONS = [
  "en_revision",
  "validada",
  "observada",
  "rechazada",
] as const;
type AdminStatus = (typeof ADMIN_TRANSITIONS)[number];

export interface UpdateInscripcionStatusInput {
  inscripcionId: string;
  status: InscripcionEstado;
  observacion?: string | null;
}

export interface UpdateInscripcionStatusDeps {
  inscripcionRepository: InscripcionRepository;
}

export async function updateInscripcionStatus(
  deps: UpdateInscripcionStatusDeps,
  input: UpdateInscripcionStatusInput,
): Promise<Inscripcion> {
  if (!ADMIN_TRANSITIONS.includes(input.status as AdminStatus)) {
    throw new ValidationError("Transición de estado no permitida para admin", {
      status: ["Solo se permiten: en_revision, validada, observada, rechazada"],
    });
  }

  if (
    input.status === "observada" &&
    (!input.observacion || input.observacion.trim().length === 0)
  ) {
    throw new ValidationError("Debes incluir una observación", {
      observacion: ["Requerido cuando el estado es observada"],
    });
  }

  const existing = await deps.inscripcionRepository.findById(
    input.inscripcionId,
  );
  if (!existing) {
    throw new NotFoundError("Inscripción no encontrada");
  }

  return await deps.inscripcionRepository.updateStatus(
    input.inscripcionId,
    input.status,
    input.observacion ?? null,
  );
}
