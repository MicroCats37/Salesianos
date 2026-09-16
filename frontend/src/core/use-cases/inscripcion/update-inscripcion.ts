import { ValidationError } from "@/core/errors";
import type {
  InscripcionRepository,
  InscripcionWithRelations,
  UpdateInscripcionInput,
} from "@/core/repositories/inscripcion.repository";
import type {
  AcreditacionTipo,
  DeportistaRol,
  Genero,
  TallaCamiseta,
  TipoDocumento,
} from "@/infra/drizzle/schema";

export interface UpdateInscripcionUseCaseInput {
  teamName?: string;
  deportistas?: Array<{
    tipoDocumento: TipoDocumento;
    numeroDocumento: string;
    nombres: string;
    apellidos: string;
    genero?: Genero | null;
    telefono?: string | null;
    rolDisciplina: DeportistaRol;
    acreditacion: AcreditacionTipo;
    disciplinaIds: string[];
    shirtSize?: TallaCamiseta | null;
  }>;
  equiposConfig?: Array<{ disciplinaId: string; categoriaId: string }>;
}

export interface UpdateInscripcionDeps {
  inscripcionRepository: InscripcionRepository;
}

export async function updateInscripcion(
  deps: UpdateInscripcionDeps,
  inscripcionId: string,
  input: UpdateInscripcionUseCaseInput,
): Promise<InscripcionWithRelations> {
  const fieldErrors: Record<string, string[]> = {};

  if (input.teamName !== undefined && !input.teamName.trim()) {
    fieldErrors.teamName = ["El nombre del equipo no puede estar vacío"];
  }

  if (input.deportistas) {
    for (let depIdx = 0; depIdx < input.deportistas.length; depIdx++) {
      const dep = input.deportistas[depIdx];
      const depPrefix = `deportistas.${depIdx}`;

      if (!dep.numeroDocumento) {
        fieldErrors[`${depPrefix}.numeroDocumento`] = [
          "numeroDocumento requerido",
        ];
      }
      if (!dep.nombres?.trim()) {
        fieldErrors[`${depPrefix}.nombres`] = ["Nombres requeridos"];
      }
      if (!dep.apellidos?.trim()) {
        fieldErrors[`${depPrefix}.apellidos`] = ["Apellidos requeridos"];
      }
      if (!Array.isArray(dep.disciplinaIds) || dep.disciplinaIds.length === 0) {
        fieldErrors[`${depPrefix}.disciplinaIds`] = [
          "Debe estar inscrito en al menos una disciplina",
        ];
      }
    }
  }

  if (Object.keys(fieldErrors).length > 0) {
    throw new ValidationError("Datos de actualización inválidos", fieldErrors);
  }

  // Build update input for repository
  const repoInput: UpdateInscripcionInput = {};

  if (input.teamName !== undefined) {
    repoInput.teamName = input.teamName.trim();
  }

  if (input.deportistas) {
    repoInput.deportistas = input.deportistas.map((d) => ({
      persona: {
        tipoDocumento: d.tipoDocumento,
        numeroDocumento: d.numeroDocumento,
        nombres: d.nombres,
        apellidos: d.apellidos,
        genero: d.genero ?? null,
        telefono: d.telefono ?? null,
      },
      rolDisciplina: d.rolDisciplina,
      acreditacion: d.acreditacion,
      disciplinaIds: d.disciplinaIds,
      shirtSize: d.shirtSize ?? null,
    }));
  }

  if (input.equiposConfig) {
    repoInput.equiposConfig = input.equiposConfig;
  }

  return await deps.inscripcionRepository.update(inscripcionId, repoInput);
}
