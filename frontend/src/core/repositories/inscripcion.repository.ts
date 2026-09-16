import type {
  AcreditacionTipo,
  Deportista,
  DeportistaRol,
  Equipo,
  Inscripcion,
  InscripcionEstado,
  NewInscripcion,
  NewPersona,
  Persona,
} from "@/infra/drizzle/schema";

export interface DeportistaData {
  persona: Omit<NewPersona, "id" | "createdAt" | "updatedAt">;
  rolDisciplina: DeportistaRol;
  acreditacion: AcreditacionTipo;
  disciplinaIds: string[];
  shirtSize?: string | null;
}

export interface CreateInscripcionInput {
  inscripcion: Omit<NewInscripcion, "id" | "createdAt" | "updatedAt">;
  deportistas: DeportistaData[];
  equiposConfig: Array<{ disciplinaId: string; categoriaId: string }>;
}

/** Equipo enriched with human-readable disciplina/categoria names for UI display */
export type EquipoConNombre = Equipo & {
  disciplinaNombre: string;
  categoriaNombre: string;
};

export interface InscripcionWithRelations {
  inscripcion: Inscripcion;
  equipos: EquipoConNombre[];
  deportistas: Array<Deportista & { persona: Persona; equipoIds: string[] }>;
}

export interface UpdateInscripcionInput {
  teamName?: string;
  deportistas?: DeportistaData[];
  equiposConfig?: Array<{ disciplinaId: string; categoriaId: string }>;
}

export interface InscripcionRepository {
  create(input: CreateInscripcionInput): Promise<InscripcionWithRelations>;
  findById(id: string): Promise<InscripcionWithRelations | null>;
  findByUserId(userId: string): Promise<InscripcionWithRelations | null>;
  listAll(filter?: {
    status?: InscripcionEstado;
    page?: number;
    pageSize?: number;
  }): Promise<{
    items: InscripcionWithRelations[];
    total: number;
  }>;
  updateStatus(
    id: string,
    status: InscripcionEstado,
    observacion?: string | null,
  ): Promise<Inscripcion>;
  update(
    id: string,
    input: UpdateInscripcionInput,
  ): Promise<InscripcionWithRelations>;
}

export interface PromocionRepository {
  listAll(
    onlyActive?: boolean,
  ): Promise<
    Array<{ id: string; anio: number; colegio: string; nombre: string | null }>
  >;
  findById(id: string): Promise<{
    id: string;
    anio: number;
    colegio: string;
    nombre: string | null;
  } | null>;
}

export interface DisciplinaRepository {
  listAll(): Promise<
    Array<{ id: string; codigo: string; nombre: string; maxJugadores: number }>
  >;
  findById(id: string): Promise<{
    id: string;
    codigo: string;
    nombre: string;
    maxJugadores: number;
  } | null>;
  findByCodigo(codigo: string): Promise<{
    id: string;
    codigo: string;
    nombre: string;
    maxJugadores: number;
  } | null>;
}

export interface CategoriaRepository {
  listByDisciplina(disciplinaId: string): Promise<
    Array<{
      id: string;
      codigo: string;
      nombre: string;
      anioMin: number;
      anioMax: number;
    }>
  >;
  findById(id: string): Promise<{
    id: string;
    codigo: string;
    nombre: string;
    anioMin: number;
    anioMax: number;
    disciplinaId: string;
  } | null>;
}

export interface BaseRepository {
  findActive(): Promise<{
    id: string;
    version: string;
    aprobadoEn: Date;
  } | null>;
  findById(
    id: string,
  ): Promise<{ id: string; version: string; aprobadoEn: Date } | null>;
}
