import { desc, eq, sql } from "drizzle-orm";
import type { NextRequest } from "next/server";
import { jsonFromUnknownError, jsonSuccess } from "@/app/_lib";
import { PermissionDeniedError } from "@/core/errors";
import { db } from "@/infra/drizzle/client";
import {
  categorias,
  DeportistaEquipos,
  deportistas,
  disciplinas,
  equipos,
  type InscripcionEstado,
  inscripciones,
  personas,
  users,
} from "@/infra/drizzle/schema";
import { getSession } from "@/lib/auth/get-session";

export async function GET(request: NextRequest) {
  try {
    const session = await getSession();
    if (!session) {
      throw new PermissionDeniedError("No autorizado");
    }
    if (session.rol !== "admin_comite" && session.rol !== "admin_finanzas") {
      throw new PermissionDeniedError(
        "Solo administradores pueden ver esta lista",
      );
    }

    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status") as InscripcionEstado | null;
    const page = Number(searchParams.get("page") ?? "1");
    const pageSize = Number(searchParams.get("pageSize") ?? "20");
    const offset = (page - 1) * pageSize;

    const whereClause = status ? eq(inscripciones.status, status) : undefined;

    // Get total count
    const totalRows = await db
      .select({ count: sql<number>`count(*)` })
      .from(inscripciones)
      .where(whereClause);
    const total = Number(totalRows[0]?.count ?? 0);

    // Get paginated inscripciones with user/persona data
    const inscRows = await db
      .select({
        id: inscripciones.id,
        userId: inscripciones.userId,
        promocionId: inscripciones.promocionId,
        basesId: inscripciones.basesId,
        paqueteMonto: inscripciones.paqueteMonto,
        status: inscripciones.status,
        observacion: inscripciones.observacion,
        createdAt: inscripciones.createdAt,
        userNombre: personas.nombres,
        userApellido: personas.apellidos,
        userDni: personas.numeroDocumento,
      })
      .from(inscripciones)
      .innerJoin(users, eq(inscripciones.userId, users.id))
      .innerJoin(personas, eq(users.personaId, personas.id))
      .where(whereClause)
      .orderBy(desc(inscripciones.createdAt))
      .limit(pageSize)
      .offset(offset);

    // Build items with equipos/deportistas counts AND player arrays
    const inscIds = inscRows.map((r: { id: string }) => r.id);

    // --- Equipos per inscripcion ---
    type EquipoRow = {
      id: string;
      inscripcionId: string;
      disciplinaId: string;
      categoriaId: string;
    };
    const equiposRows: EquipoRow[] =
      inscIds.length > 0
        ? ((await db
            .select()
            .from(equipos)
            .where(
              sql`${equipos.inscripcionId} IN ${sql.raw(`('${inscIds.join("','")}')`)}`,
            )) as unknown as EquipoRow[])
        : [];

    // --- Deportistas per inscripcion ---
    type DepRow = {
      id: string;
      inscripcionId: string;
      personaId: string;
      rolDisciplina: string;
      acreditacion: string;
      shirtSize: string | null;
    };
    const depRows: DepRow[] =
      inscIds.length > 0
        ? ((await db
            .select()
            .from(deportistas)
            .where(
              sql`${deportistas.inscripcionId} IN ${sql.raw(`('${inscIds.join("','")}')`)}`,
            )) as unknown as DepRow[])
        : [];

    // --- DeportistaEquipos links ---
    type DepEquipoLink = { DeportistaId: string; equipoId: string };
    const depIds = depRows.map((d) => d.id);
    const depEquiposLinks: DepEquipoLink[] =
      depIds.length > 0
        ? ((await db
            .select()
            .from(DeportistaEquipos)
            .where(
              sql`${DeportistaEquipos.DeportistaId} IN ${sql.raw(`('${depIds.join("','")}')`)}`,
            )) as unknown as DepEquipoLink[])
        : [];

    // --- Personas for deportistas ---
    type PersonaRow = {
      id: string;
      tipoDocumento: string;
      numeroDocumento: string;
      nombres: string;
      apellidos: string;
      telefono: string | null;
      whatsapp: string | null;
    };
    const depPersonaIds = depRows.map((d) => d.personaId);
    const depPersonas: PersonaRow[] =
      depPersonaIds.length > 0
        ? ((await db
            .select()
            .from(personas)
            .where(
              sql`${personas.id} IN ${sql.raw(`('${depPersonaIds.join("','")}')`)}`,
            )) as unknown as PersonaRow[])
        : [];

    // --- Disciplinas ---
    type DisciplinaRow = { id: string; nombre: string };
    const allDisciplinaIds = [
      ...new Set(equiposRows.map((e) => e.disciplinaId)),
    ];
    const disciplinasRows: DisciplinaRow[] =
      allDisciplinaIds.length > 0
        ? ((await db
            .select()
            .from(disciplinas)
            .where(
              sql`${disciplinas.id} IN ${sql.raw(`('${allDisciplinaIds.join("','")}')`)}`,
            )) as unknown as DisciplinaRow[])
        : [];

    // --- Categorias ---
    type CategoriaRow = { id: string; nombre: string };
    const allCategoriaIds = [...new Set(equiposRows.map((e) => e.categoriaId))];
    const categoriasRows: CategoriaRow[] =
      allCategoriaIds.length > 0
        ? ((await db
            .select()
            .from(categorias)
            .where(
              sql`${categorias.id} IN ${sql.raw(`('${allCategoriaIds.join("','")}')`)}`,
            )) as unknown as CategoriaRow[])
        : [];

    // Build lookup maps
    const disciplinaMap = new Map<string, string>(
      disciplinasRows.map((d) => [d.id, d.nombre]),
    );
    const categoriaMap = new Map<string, string>(
      categoriasRows.map((c) => [c.id, c.nombre]),
    );
    const depPersonaMap = new Map<string, PersonaRow>(
      depPersonas.map((p) => [p.id, p]),
    );

    // Group equipos by inscripcion, enriched
    const equiposByInsc = new Map<
      string,
      { id: string; disciplinaNombre: string; categoriaNombre: string }[]
    >();
    for (const e of equiposRows) {
      const entry = {
        id: e.id,
        disciplinaNombre: disciplinaMap.get(e.disciplinaId) ?? e.disciplinaId,
        categoriaNombre: categoriaMap.get(e.categoriaId) ?? e.categoriaId,
      };
      const existing = equiposByInsc.get(e.inscripcionId) ?? [];
      existing.push(entry);
      equiposByInsc.set(e.inscripcionId, existing);
    }

    // Group depEquiposLinks by DeportistaId
    const depEquiposByDepMap = new Map<string, string[]>();
    for (const link of depEquiposLinks) {
      const existing = depEquiposByDepMap.get(link.DeportistaId) ?? [];
      existing.push(link.equipoId);
      depEquiposByDepMap.set(link.DeportistaId, existing);
    }

    // Group depRows by inscripcionId with full persona and equipo details
    type JugadorOutput = {
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
    };
    const jugadoresByInsc = new Map<string, JugadorOutput[]>();
    for (const d of depRows) {
      const persona = depPersonaMap.get(d.personaId);
      const linkedEquipos: {
        disciplinaNombre: string;
        categoriaNombre: string;
      }[] = [];
      for (const eqId of depEquiposByDepMap.get(d.id) ?? []) {
        const eq = equiposRows.find((e) => e.id === eqId);
        if (eq) {
          linkedEquipos.push({
            disciplinaNombre:
              disciplinaMap.get(eq.disciplinaId) ?? eq.disciplinaId,
            categoriaNombre: categoriaMap.get(eq.categoriaId) ?? eq.categoriaId,
          });
        }
      }
      const jugador: JugadorOutput = {
        nombre: persona?.nombres ?? "",
        apellido: persona?.apellidos ?? "",
        tipoDocumento: persona?.tipoDocumento ?? "DNI",
        numeroDocumento: persona?.numeroDocumento ?? "",
        telefono: persona?.telefono ?? null,
        whatsapp: persona?.whatsapp ?? null,
        rolDisciplina: d.rolDisciplina,
        acreditacion: d.acreditacion,
        shirtSize: d.shirtSize,
        equipos: linkedEquipos,
      };
      const existing = jugadoresByInsc.get(d.inscripcionId) ?? [];
      existing.push(jugador);
      jugadoresByInsc.set(d.inscripcionId, existing);
    }

    type InscRow = (typeof inscRows)[number];

    const items = inscRows.map((row: InscRow) => ({
      inscripcion: {
        id: row.id,
        userId: row.userId,
        promocionId: row.promocionId,
        basesId: row.basesId,
        paqueteMonto: row.paqueteMonto,
        status: row.status,
        observacion: row.observacion,
        createdAt:
          row.createdAt instanceof Date
            ? row.createdAt.toISOString()
            : String(row.createdAt),
      },
      equiposCount: (equiposByInsc.get(row.id) ?? []).length,
      jugadoresCount: (jugadoresByInsc.get(row.id) ?? []).length,
      userNombre: row.userNombre ?? "",
      userApellido: row.userApellido ?? "",
      userDni: row.userDni ?? "",
      jugadores: jugadoresByInsc.get(row.id) ?? [],
    }));

    const meta = {
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize),
    };

    return jsonSuccess({ items, total }, 200, meta);
  } catch (error) {
    return jsonFromUnknownError(error, "GET /api/admin/inscripciones");
  }
}

export const dynamic = "force-dynamic";
