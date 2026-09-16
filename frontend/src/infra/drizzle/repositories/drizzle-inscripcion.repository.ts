import { and, desc, eq, sql } from "drizzle-orm";
import { db, schema } from "@/infra/drizzle/client";
import type {
  BaseRepository,
  CategoriaRepository,
  CreateInscripcionInput,
  DisciplinaRepository,
  InscripcionRepository,
  InscripcionWithRelations,
  PromocionRepository,
  UpdateInscripcionInput,
} from "@/core/repositories/inscripcion.repository";
import type { InscripcionEstado } from "@/infra/drizzle/schema";

export class DrizzleInscripcionRepository implements InscripcionRepository {
  async create(input: CreateInscripcionInput): Promise<InscripcionWithRelations> {
    return db.transaction(async (tx: any) => {
      // 1. Insert Inscripcion
      const [insc] = await tx
        .insert(schema.inscripciones)
        .values(input.inscripcion)
        .returning();
      if (!insc) throw new Error("Failed to create inscripcion");

      // 2. Insert Equipos based on equiposConfig
      const equiposCreados = [];
      for (const config of input.equiposConfig) {
        const [eq0] = await tx
          .insert(schema.equipos)
          .values({
            inscripcionId: insc.id,
            disciplinaId: config.disciplinaId,
            categoriaId: config.categoriaId,
          })
          .returning();
        equiposCreados.push(eq0);
      }

      // Enrich equipos with disciplina and categoria names
      const disciplinaIds = [...new Set(equiposCreados.map((e: any) => e.disciplinaId))];
      const categoriaIds = [...new Set(equiposCreados.map((e: any) => e.categoriaId))];
      const disciplinasRows =
        disciplinaIds.length > 0
          ? await tx
              .select()
              .from(schema.disciplinas)
              .where(sql`${schema.disciplinas.id} IN ${sql.raw(`('${disciplinaIds.join("','")}')`)}`)
          : [];
      const categoriasRows =
        categoriaIds.length > 0
          ? await tx
              .select()
              .from(schema.categorias)
              .where(sql`${schema.categorias.id} IN ${sql.raw(`('${categoriaIds.join("','")}')`)}`)
          : [];
      const disciplinaMap = Object.fromEntries(
        disciplinasRows.map((d: any) => [d.id, d.nombre])
      );
      const categoriaMap = Object.fromEntries(
        categoriasRows.map((c: any) => [c.id, c.nombre])
      );
      const equiposEnriched = equiposCreados.map((e: any) => ({
        ...e,
        disciplinaNombre: disciplinaMap[e.disciplinaId] ?? e.disciplinaId,
        categoriaNombre: categoriaMap[e.categoriaId] ?? e.categoriaId,
      }));

      // 3. Process Deportistas
      const deportistasOutput: any[] = [];
      for (const dep of input.deportistas) {
        // Upsert Persona by numeroDocumento
        let personaId = "";
        const existingPersona = await tx
          .select()
          .from(schema.personas)
          .where(eq(schema.personas.numeroDocumento, dep.persona.numeroDocumento))
          .limit(1);
        if (existingPersona.length > 0) {
          const [updated] = await tx
            .update(schema.personas)
            .set(dep.persona)
            .where(eq(schema.personas.id, existingPersona[0].id))
            .returning();
          personaId = updated.id;
        } else {
          const [created] = await tx
            .insert(schema.personas)
            .values(dep.persona)
            .returning();
          personaId = created.id;
        }

        // Insert Deportista
        const [deportista] = await tx
          .insert(schema.deportistas)
          .values({
            inscripcionId: insc.id,
            personaId,
            rolDisciplina: dep.rolDisciplina,
            acreditacion: dep.acreditacion,
            shirtSize: dep.shirtSize ?? null,
          })
          .returning();

        // Link to Equipos
        const equipoIds: string[] = [];
        for (const discId of dep.disciplinaIds) {
          const equipo = equiposCreados.find((e: any) => e.disciplinaId === discId);
          if (equipo) {
            await tx.insert(schema.DeportistaEquipos).values({
              DeportistaId: deportista.id,
              equipoId: equipo.id,
            });
            equipoIds.push(equipo.id);
          }
        }

        // Fetch full persona for return
        const [fullPersona] = await tx
          .select()
          .from(schema.personas)
          .where(eq(schema.personas.id, personaId))
          .limit(1);
        deportistasOutput.push({ ...deportista, persona: fullPersona, equipoIds });
      }

      return { inscripcion: insc, equipos: equiposEnriched, deportistas: deportistasOutput };
    });
  }

  async findById(id: string): Promise<InscripcionWithRelations | null> {
    const rows = await db
      .select()
      .from(schema.inscripciones)
      .where(eq(schema.inscripciones.id, id))
      .limit(1);
    const insc = rows[0];
    if (!insc) return null;
    return this.loadRelations(insc);
  }

  async findByUserId(userId: string): Promise<InscripcionWithRelations | null> {
    const rows = await db
      .select()
      .from(schema.inscripciones)
      .where(eq(schema.inscripciones.userId, userId))
      .orderBy(desc(schema.inscripciones.createdAt))
      .limit(1);
    const insc = rows[0];
    if (!insc) return null;
    return this.loadRelations(insc);
  }

  async listAll(filter?: {
    status?: InscripcionEstado;
    page?: number;
    pageSize?: number;
  }): Promise<{ items: InscripcionWithRelations[]; total: number }> {
    const page = filter?.page ?? 1;
    const pageSize = filter?.pageSize ?? 20;
    const offset = (page - 1) * pageSize;
    const whereClause = filter?.status ? eq(schema.inscripciones.status, filter.status) : undefined;

    const totalRows = await db
      .select({ count: sql<number>`count(*)` })
      .from(schema.inscripciones)
      .where(whereClause);
    const total = Number(totalRows[0]?.count ?? 0);

    const rows = await db
      .select()
      .from(schema.inscripciones)
      .where(whereClause)
      .orderBy(desc(schema.inscripciones.createdAt))
      .limit(pageSize)
      .offset(offset);

    const items = await Promise.all(rows.map((r: any) => this.loadRelations(r)));
    return { items, total };
  }

  async updateStatus(id: string, status: InscripcionEstado, observacion?: string | null): Promise<any> {
    const rows = await db
      .update(schema.inscripciones)
      .set({ status, observacion: observacion ?? null, updatedAt: new Date() })
      .where(eq(schema.inscripciones.id, id))
      .returning();
    if (!rows[0]) throw new Error(`Inscripcion ${id} not found`);
    return rows[0];
  }

  async update(id: string, input: UpdateInscripcionInput): Promise<InscripcionWithRelations> {
    return db.transaction(async (tx: any) => {
      // Update inscription teamName if provided
      if (input.teamName !== undefined) {
        await tx
          .update(schema.inscripciones)
          .set({ teamName: input.teamName, updatedAt: new Date() })
          .where(eq(schema.inscripciones.id, id));
      }

      // Get current equipos for this inscripcion
      const currentEquipos = await tx
        .select()
        .from(schema.equipos)
        .where(eq(schema.equipos.inscripcionId, id));

      // If deportistas are provided, upsert each one
      if (input.deportistas && input.deportistas.length > 0) {
        for (const dep of input.deportistas) {
          // Upsert Persona by numeroDocumento
          let personaId = "";
          const existingPersona = await tx
            .select()
            .from(schema.personas)
            .where(eq(schema.personas.numeroDocumento, dep.persona.numeroDocumento))
            .limit(1);
          if (existingPersona.length > 0) {
            const [updated] = await tx
              .update(schema.personas)
              .set({
                tipoDocumento: dep.persona.tipoDocumento,
                nombres: dep.persona.nombres,
                apellidos: dep.persona.apellidos,
                genero: dep.persona.genero ?? null,
                telefono: dep.persona.telefono ?? null,
              })
              .where(eq(schema.personas.id, existingPersona[0].id))
              .returning();
            personaId = updated.id;
          } else {
            const [created] = await tx
              .insert(schema.personas)
              .values({
                tipoDocumento: dep.persona.tipoDocumento,
                numeroDocumento: dep.persona.numeroDocumento,
                nombres: dep.persona.nombres,
                apellidos: dep.persona.apellidos,
                genero: dep.persona.genero ?? null,
                telefono: dep.persona.telefono ?? null,
              })
              .returning();
            personaId = created.id;
          }

          // Check if Deportista already exists for this inscripcion and persona
          const existingDeportista = await tx
            .select()
            .from(schema.deportistas)
            .where(
              and(
                eq(schema.deportistas.inscripcionId, id),
                eq(schema.deportistas.personaId, personaId)
              )
            )
            .limit(1);

          let DeportistaId = "";
          if (existingDeportista.length > 0) {
            const [updated] = await tx
              .update(schema.deportistas)
              .set({
                rolDisciplina: dep.rolDisciplina,
                acreditacion: dep.acreditacion,
                shirtSize: dep.shirtSize ?? null,
              })
              .where(eq(schema.deportistas.id, existingDeportista[0].id))
              .returning();
            DeportistaId = updated.id;
          } else {
            const [created] = await tx
              .insert(schema.deportistas)
              .values({
                inscripcionId: id,
                personaId,
                rolDisciplina: dep.rolDisciplina,
                acreditacion: dep.acreditacion,
                shirtSize: dep.shirtSize ?? null,
              })
              .returning();
            DeportistaId = created.id;
          }

          // Delete old DeportistaEquipos links for this Deportista
          await tx
            .delete(schema.DeportistaEquipos)
            .where(eq(schema.DeportistaEquipos.DeportistaId, DeportistaId));

          // Create new DeportistaEquipos links for each discipline
          for (const discId of dep.disciplinaIds) {
            const equipo = currentEquipos.find((e: any) => e.disciplinaId === discId);
            if (equipo) {
              await tx.insert(schema.DeportistaEquipos).values({
                DeportistaId,
                equipoId: equipo.id,
              });
            }
          }
        }
      }

      // Reload and return
      const rows = await tx
        .select()
        .from(schema.inscripciones)
        .where(eq(schema.inscripciones.id, id))
        .limit(1);
      if (!rows[0]) throw new Error(`Inscripcion ${id} not found after update`);
      return this.loadRelationsFromTx(tx, rows[0]);
    });
  }

  private async loadRelationsFromTx(tx: any, insc: any): Promise<InscripcionWithRelations> {
    const equiposRows = await tx
      .select()
      .from(schema.equipos)
      .where(eq(schema.equipos.inscripcionId, insc.id));
    const deportistasRows = await tx
      .select()
      .from(schema.deportistas)
      .where(eq(schema.deportistas.inscripcionId, insc.id));
    const personaIds = deportistasRows.map((d: any) => d.personaId);
    const personasRows =
      personaIds.length > 0
        ? await tx
            .select()
            .from(schema.personas)
            .where(sql`${schema.personas.id} IN ${sql.raw(`('${personaIds.join("','")}')`)}`)
        : [];
    const deportistIds = deportistasRows.map((d: any) => d.id);
    const equipoLinks =
      deportistIds.length > 0
        ? await tx
            .select()
            .from(schema.DeportistaEquipos)
            .where(
              sql`${schema.DeportistaEquipos.DeportistaId} IN ${sql.raw(`('${deportistIds.join("','")}')`)}`
            )
        : [];

    // Enrich equipos with disciplina and categoria names
    const disciplinaIds = [...new Set(equiposRows.map((e: any) => e.disciplinaId))];
    const categoriaIds = [...new Set(equiposRows.map((e: any) => e.categoriaId))];
    const disciplinasRows =
      disciplinaIds.length > 0
        ? await tx
            .select()
            .from(schema.disciplinas)
            .where(sql`${schema.disciplinas.id} IN ${sql.raw(`('${disciplinaIds.join("','")}')`)}`)
        : [];
    const categoriasRows =
      categoriaIds.length > 0
        ? await tx
            .select()
            .from(schema.categorias)
            .where(sql`${schema.categorias.id} IN ${sql.raw(`('${categoriaIds.join("','")}')`)}`)
        : [];
    const disciplinaMap = Object.fromEntries(
      disciplinasRows.map((d: any) => [d.id, d.nombre])
    );
    const categoriaMap = Object.fromEntries(
      categoriasRows.map((c: any) => [c.id, c.nombre])
    );
    const equiposEnriched = equiposRows.map((e: any) => ({
      ...e,
      disciplinaNombre: disciplinaMap[e.disciplinaId] ?? e.disciplinaId,
      categoriaNombre: categoriaMap[e.categoriaId] ?? e.categoriaId,
    }));

    const deportistasWithRelations = deportistasRows.map((dep: any) => {
      const persona = personasRows.find((p: any) => p.id === dep.personaId);
      const linkedEquipos = equipoLinks
        .filter((e: any) => e.DeportistaId === dep.id)
        .map((e: any) => e.equipoId);
      return { ...dep, persona: persona!, equipoIds: linkedEquipos };
    });

    return {
      inscripcion: insc,
      equipos: equiposEnriched,
      deportistas: deportistasWithRelations,
    } as unknown as InscripcionWithRelations;
  }

  private async loadRelations(insc: any): Promise<InscripcionWithRelations> {
    // Load equipos for this inscripcion
    const equiposRows = await db
      .select()
      .from(schema.equipos)
      .where(eq(schema.equipos.inscripcionId, insc.id));

    // Load deportistas with their personas and equipo links
    const deportistasRows = await db
      .select()
      .from(schema.deportistas)
      .where(eq(schema.deportistas.inscripcionId, insc.id));

    // Load personas for all deportistas
    const personaIds = deportistasRows.map((d: any) => d.personaId);
    const personasRows =
      personaIds.length > 0
        ? await db
            .select()
            .from(schema.personas)
            .where(sql`${schema.personas.id} IN ${sql.raw(`('${personaIds.join("','")}')`)}`)
        : [];

    // Load DeportistaEquipos links
    const deportistIds = deportistasRows.map((d: any) => d.id);
    const equipoLinks =
      deportistIds.length > 0
        ? await db
            .select()
            .from(schema.DeportistaEquipos)
            .where(
              sql`${schema.DeportistaEquipos.DeportistaId} IN ${sql.raw(`('${deportistIds.join("','")}')`)}`
            )
        : [];

    // Enrich equipos with disciplina and categoria names
    const disciplinaIds = [...new Set(equiposRows.map((e: any) => e.disciplinaId))];
    const categoriaIds = [...new Set(equiposRows.map((e: any) => e.categoriaId))];
    const disciplinasRows =
      disciplinaIds.length > 0
        ? await db
            .select()
            .from(schema.disciplinas)
            .where(sql`${schema.disciplinas.id} IN ${sql.raw(`('${disciplinaIds.join("','")}')`)}`)
        : [];
    const categoriasRows =
      categoriaIds.length > 0
        ? await db
            .select()
            .from(schema.categorias)
            .where(sql`${schema.categorias.id} IN ${sql.raw(`('${categoriaIds.join("','")}')`)}`)
        : [];
    const disciplinaMap = Object.fromEntries(disciplinasRows.map((d: any) => [d.id, d.nombre]));
    const categoriaMap = Object.fromEntries(categoriasRows.map((c: any) => [c.id, c.nombre]));
    const equiposEnriched = equiposRows.map((e: any) => ({
      ...e,
      disciplinaNombre: disciplinaMap[e.disciplinaId] ?? e.disciplinaId,
      categoriaNombre: categoriaMap[e.categoriaId] ?? e.categoriaId,
    }));

    // Map deportistas with their persona and equipoIds
    const deportistasWithRelations = deportistasRows.map((dep: any) => {
      const persona = personasRows.find((p: any) => p.id === dep.personaId);
      const linkedEquipos = equipoLinks
        .filter((e: any) => e.DeportistaId === dep.id)
        .map((e: any) => e.equipoId);
      return {
        ...dep,
        persona: persona!,
        equipoIds: linkedEquipos,
      };
    });

    return {
      inscripcion: insc,
      equipos: equiposEnriched,
      deportistas: deportistasWithRelations,
    };
  }
}

export class DrizzlePromocionRepository implements PromocionRepository {
  async listAll(
    onlyActive = true
  ): Promise<Array<{ id: string; anio: number; colegio: string; nombre: string | null }>> {
    return db
      .select({
        id: schema.promociones.id,
        anio: schema.promociones.anio,
        colegio: schema.promociones.colegio,
        nombre: schema.promociones.nombre,
      })
      .from(schema.promociones)
      .where(onlyActive ? eq(schema.promociones.activa, true) : undefined);
  }

  async findById(id: string) {
    const rows = await db
      .select({
        id: schema.promociones.id,
        anio: schema.promociones.anio,
        colegio: schema.promociones.colegio,
        nombre: schema.promociones.nombre,
      })
      .from(schema.promociones)
      .where(eq(schema.promociones.id, id))
      .limit(1);
    return rows[0] ?? null;
  }
}

export class DrizzleDisciplinaRepository implements DisciplinaRepository {
  async listAll() {
    return db
      .select({
        id: schema.disciplinas.id,
        codigo: schema.disciplinas.codigo,
        nombre: schema.disciplinas.nombre,
        maxJugadores: schema.disciplinas.maxJugadores,
      })
      .from(schema.disciplinas);
  }

  async findById(id: string) {
    const rows = await db
      .select({
        id: schema.disciplinas.id,
        codigo: schema.disciplinas.codigo,
        nombre: schema.disciplinas.nombre,
        maxJugadores: schema.disciplinas.maxJugadores,
      })
      .from(schema.disciplinas)
      .where(eq(schema.disciplinas.id, id))
      .limit(1);
    return rows[0] ?? null;
  }

  async findByCodigo(codigo: string) {
    const rows = await db
      .select({
        id: schema.disciplinas.id,
        codigo: schema.disciplinas.codigo,
        nombre: schema.disciplinas.nombre,
        maxJugadores: schema.disciplinas.maxJugadores,
      })
      .from(schema.disciplinas)
      .where(eq(schema.disciplinas.codigo, codigo as "fulbito_var" | "fulbito_dam" | "voley_mix" | "basket_var"))
      .limit(1);
    return rows[0] ?? null;
  }
}

export class DrizzleCategoriaRepository implements CategoriaRepository {
  async listByDisciplina(disciplinaId: string) {
    return db
      .select({
        id: schema.categorias.id,
        codigo: schema.categorias.codigo,
        nombre: schema.categorias.nombre,
        anioMin: schema.categorias.anioMin,
        anioMax: schema.categorias.anioMax,
      })
      .from(schema.categorias)
      .where(eq(schema.categorias.disciplinaId, disciplinaId));
  }

  async findById(id: string) {
    const rows = await db
      .select({
        id: schema.categorias.id,
        codigo: schema.categorias.codigo,
        nombre: schema.categorias.nombre,
        anioMin: schema.categorias.anioMin,
        anioMax: schema.categorias.anioMax,
        disciplinaId: schema.categorias.disciplinaId,
      })
      .from(schema.categorias)
      .where(eq(schema.categorias.id, id))
      .limit(1);
    return rows[0] ?? null;
  }
}

export class DrizzleBaseRepository implements BaseRepository {
  async findActive() {
    const rows = await db
      .select({
        id: schema.bases.id,
        version: schema.bases.version,
        aprobadoEn: schema.bases.aprobadoEn,
      })
      .from(schema.bases)
      .where(eq(schema.bases.activo, true))
      .limit(1);
    return rows[0] ?? null;
  }

  async findById(id: string) {
    const rows = await db
      .select({
        id: schema.bases.id,
        version: schema.bases.version,
        aprobadoEn: schema.bases.aprobadoEn,
      })
      .from(schema.bases)
      .where(eq(schema.bases.id, id))
      .limit(1);
    return rows[0] ?? null;
  }
}
