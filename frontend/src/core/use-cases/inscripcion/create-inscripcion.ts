import {
  BusinessError,
  ConflictError,
  NotFoundError,
  ValidationError,
} from "@/core/errors";
import type {
  BaseRepository,
  CategoriaRepository,
  CreateInscripcionInput,
  DisciplinaRepository,
  InscripcionRepository,
  InscripcionWithRelations,
  PromocionRepository,
} from "@/core/repositories/inscripcion.repository";
import type {
  AcreditacionTipo,
  DeportistaRol,
  Genero,
  TallaCamiseta,
  TipoDocumento,
} from "@/infra/drizzle/schema";

export interface CreateInscripcionUseCaseInput {
  userId: string;
  promocionId: string;
  fusionPromocionId?: string | null;
  basesId: string;
  paqueteMonto: number;
  teamName: string;
  acceptedBases: boolean;
  fitnessDeclaration: boolean;
  imageConsent: boolean;
  deportistas: Array<{
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
}

export interface CreateInscripcionDeps {
  inscripcionRepository: InscripcionRepository;
  promocionRepository: PromocionRepository;
  disciplinaRepository: DisciplinaRepository;
  categoriaRepository: CategoriaRepository;
  baseRepository: BaseRepository;
}

const DNI_REGEX = /^\d{8}$/;

export async function createInscripcion(
  deps: CreateInscripcionDeps,
  input: CreateInscripcionUseCaseInput,
): Promise<InscripcionWithRelations> {
  const fieldErrors: Record<string, string[]> = {};

  // --- Input-level validations ---

  if (!input.userId?.trim()) {
    fieldErrors.userId = ["userId requerido"];
  }
  if (!input.promocionId?.trim()) {
    fieldErrors.promocionId = ["promocionId requerido"];
  }
  if (!input.basesId?.trim()) {
    fieldErrors.basesId = ["basesId requerido"];
  }
  if (typeof input.paqueteMonto !== "number" || input.paqueteMonto <= 0) {
    fieldErrors.paqueteMonto = ["Monto debe ser un número positivo"];
  }
  if (!input.acceptedBases) {
    fieldErrors.acceptedBases = ["Debe aceptar las bases"];
  }
  if (!input.fitnessDeclaration) {
    fieldErrors.fitnessDeclaration = [
      "Debe confirmar la declaración de aptitud física",
    ];
  }
  if (!input.imageConsent) {
    fieldErrors.imageConsent = ["Debe dar consentimiento de uso de imagen"];
  }
  if (!input.teamName?.trim()) {
    fieldErrors.teamName = ["Ingresa el nombre del equipo"];
  }
  if (!Array.isArray(input.deportistas) || input.deportistas.length === 0) {
    fieldErrors.deportistas = ["Debe haber al menos un deportista"];
  }

  // --- Duplicate user inscription check ---
  const existingInscripcion = await deps.inscripcionRepository.findByUserId(
    input.userId,
  );
  if (existingInscripcion) {
    throw new ConflictError("Ya existe una inscripción para este usuario");
  }

  // --- Fetch promocion ---
  const promocion = await deps.promocionRepository.findById(input.promocionId);
  if (!promocion) {
    throw new NotFoundError(`Promoción no encontrada: ${input.promocionId}`);
  }

  // --- Bases must be the active version ---
  const activeBases = await deps.baseRepository.findActive();
  if (!activeBases) {
    throw new BusinessError("No hay una versión de bases activa");
  }
  if (activeBases.id !== input.basesId) {
    throw new BusinessError(
      `La versión de bases proporcionada (${input.basesId}) no es la versión activa (${activeBases.id})`,
    );
  }

  // --- Fetch all disciplinas and categorias for category matching ---
  const allDisciplinas = await deps.disciplinaRepository.listAll();

  const equiposConfig: { disciplinaId: string; categoriaId: string }[] = [];

  // --- Validate deportistas and build equiposConfig ---
  for (let depIdx = 0; depIdx < input.deportistas.length; depIdx++) {
    const dep = input.deportistas[depIdx];
    const depPrefix = `deportistas.${depIdx}`;
    let depFieldErrors = 0;

    if (!dep.tipoDocumento) {
      fieldErrors[`${depPrefix}.tipoDocumento`] = ["tipoDocumento requerido"];
      depFieldErrors++;
    }
    if (!dep.numeroDocumento || !DNI_REGEX.test(dep.numeroDocumento)) {
      fieldErrors[`${depPrefix}.numeroDocumento`] = [
        "numeroDocumento debe tener 8 dígitos",
      ];
      depFieldErrors++;
    }
    if (!dep.nombres?.trim()) {
      fieldErrors[`${depPrefix}.nombres`] = ["Nombres requeridos"];
      depFieldErrors++;
    }
    if (!dep.apellidos?.trim()) {
      fieldErrors[`${depPrefix}.apellidos`] = ["Apellidos requeridos"];
      depFieldErrors++;
    }
    if (!Array.isArray(dep.disciplinaIds) || dep.disciplinaIds.length === 0) {
      fieldErrors[`${depPrefix}.disciplinaIds`] = [
        "Debe estar inscrito en al menos una disciplina",
      ];
      depFieldErrors++;
    }

    // Validate each disciplinaId and count players per discipline
    const disciplinaCount: Record<string, number> = {};
    for (const discId of dep.disciplinaIds) {
      const disciplina = allDisciplinas.find((d) => d.id === discId);
      if (!disciplina) {
        fieldErrors[`${depPrefix}.disciplinaIds`] = [
          `Disciplina no encontrada: ${discId}`,
        ];
        depFieldErrors++;
      } else {
        disciplinaCount[discId] = (disciplinaCount[discId] || 0) + 1;
      }
    }

    // Check maxJugadores per discipline
    for (const [discId, count] of Object.entries(disciplinaCount)) {
      const disciplina = allDisciplinas.find((d) => d.id === discId)!;
      if (count > disciplina.maxJugadores) {
        fieldErrors[`${depPrefix}.disciplinaIds`] = [
          `Máximo ${disciplina.maxJugadores} jugadores permitidos para ${disciplina.nombre}`,
        ];
        depFieldErrors++;
      }
    }
  }

  // Build equiposConfig: one equipo per discipline that has players
  for (const disc of allDisciplinas) {
    const playersInDisc = input.deportistas.filter((d) =>
      d.disciplinaIds.includes(disc.id),
    );
    if (playersInDisc.length > 0) {
      // Find category based on Promocion Anio - list categories for this discipline
      const categorias = await deps.categoriaRepository.listByDisciplina(
        disc.id,
      );
      const cat = categorias.find(
        (c) => promocion.anio >= c.anioMin && promocion.anio <= c.anioMax,
      );
      if (!cat) {
        throw new ValidationError(
          `No hay categoría disponible en ${disc.nombre} para la promoción ${promocion.anio}`,
        );
      }
      equiposConfig.push({ disciplinaId: disc.id, categoriaId: cat.id });
    }
  }

  if (Object.keys(fieldErrors).length > 0) {
    throw new ValidationError("Datos de inscripción inválidos", fieldErrors);
  }

  // --- Prepare deportistas payload ---
  const deportistasData = input.deportistas.map((d) => ({
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

  // --- Build and call repo ---
  return await deps.inscripcionRepository.create({
    inscripcion: {
      userId: input.userId,
      promocionId: input.promocionId,
      fusionPromocionId: input.fusionPromocionId ?? null,
      basesId: input.basesId,
      paqueteMonto: input.paqueteMonto,
      teamName: input.teamName.trim(),
      status: "recibida",
      observacion: null,
      acceptedBases: input.acceptedBases,
      declaracionJurada: input.fitnessDeclaration,
      fitnessDeclaration: input.fitnessDeclaration,
      imageConsent: input.imageConsent,
    },
    deportistas: deportistasData,
    equiposConfig,
  });
}
