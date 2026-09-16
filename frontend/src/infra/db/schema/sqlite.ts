/**
 * SQLite schema — uses drizzle-orm/sqlite-core sqliteTable.
 * All tables use unixepoch() for timestamp defaults and integer for booleans.
 */
import { sql } from "drizzle-orm";
import {
  integer,
  primaryKey,
  sqliteTable,
  text,
} from "drizzle-orm/sqlite-core";

// ── Enums (TypeScript only, not baked into SQLite) ────────────────────────────

export const userRoles = [
  "responsable",
  "admin_comite",
  "admin_finanzas",
] as const;
export type UserRole = (typeof userRoles)[number];

export const tipoDocumentos = ["DNI", "CE", "PAS"] as const;
export type TipoDocumento = (typeof tipoDocumentos)[number];

export const generos = ["V", "M"] as const;
export type Genero = (typeof generos)[number];

export const inscripcionEstados = [
  "recibida",
  "en_revision",
  "observada",
  "validada",
  "pago_pendiente",
  "pagada",
  "confirmada",
  "rechazada",
] as const;
export type InscripcionEstado = (typeof inscripcionEstados)[number];

export const DeportistaRoles = ["Capitán", "Delegado", "Jugador"] as const;
export type DeportistaRol = (typeof DeportistaRoles)[number];

export const AcreditacionTipos = [
  "Verificación en padrón",
  "Excepción aprobada",
] as const;
export type AcreditacionTipo = (typeof AcreditacionTipos)[number];

export const TallaCamisetas = ["XS", "S", "M", "L", "XL", "XXL"] as const;
export type TallaCamiseta = (typeof TallaCamisetas)[number];

export const categoriaCodigos = [
  "junior",
  "senior",
  "master",
  "super_master",
] as const;
export type CategoriaCodigo = (typeof categoriaCodigos)[number];

export const disciplinaCodigos = [
  "fulbito_var",
  "fulbito_dam",
  "voley_mix",
  "basket_var",
] as const;
export type DisciplinaCodigo = (typeof disciplinaCodigos)[number];

export const colegios = ["sjb", "ma"] as const;
export type Colegio = (typeof colegios)[number];

// ── Tables ────────────────────────────────────────────────────────────────────

export const personas = sqliteTable("personas", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  tipoDocumento: text("tipo_documento", { enum: tipoDocumentos })
    .notNull()
    .default("DNI"),
  numeroDocumento: text("numero_documento").notNull().unique(),
  nombres: text("nombres").notNull(),
  apellidos: text("apellidos").notNull(),
  genero: text("genero", { enum: generos }),
  telefono: text("telefono"),
  whatsapp: text("whatsapp"),
  contactoEmergenciaNombre: text("contacto_emergencia_nombre"),
  contactoEmergenciaTelefono: text("contacto_emergencia_telefono"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Persona = typeof personas.$inferSelect;
export type NewPersona = typeof personas.$inferInsert;

export const users = sqliteTable("users", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  personaId: text("persona_id")
    .notNull()
    .references(() => personas.id, { onDelete: "restrict" })
    .unique(),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  rol: text("rol", { enum: userRoles }).notNull().default("responsable"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;

export const sesiones = sqliteTable("sesiones", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  userId: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  tokenHash: text("token_hash").notNull().unique(),
  expiresAt: integer("expires_at", { mode: "timestamp" }).notNull(),
  revokedAt: integer("revoked_at", { mode: "timestamp" }),
  userAgent: text("user_agent"),
  ip: text("ip"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Sesion = typeof sesiones.$inferSelect;
export type NewSesion = typeof sesiones.$inferInsert;

export const promociones = sqliteTable("promociones", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  anio: integer("anio").notNull().unique(),
  colegio: text("colegio", { enum: colegios }).notNull(),
  nombre: text("nombre"),
  activa: integer("activa", { mode: "boolean" }).notNull().default(true),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Promocion = typeof promociones.$inferSelect;
export type NewPromocion = typeof promociones.$inferInsert;

export const disciplinas = sqliteTable("disciplinas", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  codigo: text("codigo", { enum: disciplinaCodigos }).notNull().unique(),
  nombre: text("nombre").notNull(),
  maxJugadores: integer("max_jugadores").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Disciplina = typeof disciplinas.$inferSelect;
export type NewDisciplina = typeof disciplinas.$inferInsert;

export const categorias = sqliteTable("categorias", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  disciplinaId: text("disciplina_id")
    .notNull()
    .references(() => disciplinas.id, { onDelete: "cascade" }),
  codigo: text("codigo", { enum: categoriaCodigos }).notNull(),
  nombre: text("nombre").notNull(),
  anioMin: integer("anio_min").notNull(),
  anioMax: integer("anio_max").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Categoria = typeof categorias.$inferSelect;
export type NewCategoria = typeof categorias.$inferInsert;

export const bases = sqliteTable("bases", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  version: text("version").notNull().unique(),
  aprobadoEn: integer("aprobado_en", { mode: "timestamp" }).notNull(),
  contenidoUrl: text("contenido_url"),
  activo: integer("activo", { mode: "boolean" }).notNull().default(true),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Base = typeof bases.$inferSelect;
export type NewBase = typeof bases.$inferInsert;

export const inscripciones = sqliteTable("inscripciones", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  userId: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "restrict" }),
  promocionId: text("promocion_id")
    .notNull()
    .references(() => promociones.id, { onDelete: "restrict" }),
  fusionPromocionId: text("fusion_promocion_id").references(
    () => promociones.id,
    { onDelete: "restrict" },
  ),
  basesId: text("bases_id")
    .notNull()
    .references(() => bases.id, { onDelete: "restrict" }),
  paqueteMonto: integer("paquete_monto").notNull(),
  teamName: text("team_name"),
  status: text("status", { enum: inscripcionEstados })
    .notNull()
    .default("recibida"),
  observacion: text("observacion"),
  acceptedBases: integer("accepted_bases", { mode: "boolean" })
    .notNull()
    .default(false),
  declaracionJurada: integer("declaracion_jurada", { mode: "boolean" })
    .notNull()
    .default(false),
  fitnessDeclaration: integer("fitness_declaration", { mode: "boolean" })
    .notNull()
    .default(false),
  imageConsent: integer("image_consent", { mode: "boolean" })
    .notNull()
    .default(false),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Inscripcion = typeof inscripciones.$inferSelect;
export type NewInscripcion = typeof inscripciones.$inferInsert;

export const equipos = sqliteTable("equipos", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  inscripcionId: text("inscripcion_id")
    .notNull()
    .references(() => inscripciones.id, { onDelete: "cascade" }),
  disciplinaId: text("disciplina_id")
    .notNull()
    .references(() => disciplinas.id, { onDelete: "restrict" }),
  categoriaId: text("categoria_id")
    .notNull()
    .references(() => categorias.id, { onDelete: "restrict" }),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Equipo = typeof equipos.$inferSelect;
export type NewEquipo = typeof equipos.$inferInsert;

export const deportistas = sqliteTable("deportistas", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  inscripcionId: text("inscripcion_id")
    .notNull()
    .references(() => inscripciones.id, { onDelete: "cascade" }),
  personaId: text("persona_id")
    .notNull()
    .references(() => personas.id, { onDelete: "restrict" }),
  rolDisciplina: text("rol_disciplina", { enum: DeportistaRoles })
    .notNull()
    .default("Jugador"),
  acreditacion: text("acreditacion", { enum: AcreditacionTipos })
    .notNull()
    .default("Verificación en padrón"),
  shirtSize: text("shirt_size"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .default(sql`(unixepoch())`),
});

export type Deportista = typeof deportistas.$inferSelect;
export type NewDeportista = typeof deportistas.$inferInsert;

export const DeportistaEquipos = sqliteTable(
  "deportista_equipos",
  {
    DeportistaId: text("deportista_id")
      .notNull()
      .references(() => deportistas.id, { onDelete: "cascade" }),
    equipoId: text("equipo_id")
      .notNull()
      .references(() => equipos.id, { onDelete: "cascade" }),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`(unixepoch())`),
  },
  (table) => ({
    pk: primaryKey({ columns: [table.DeportistaId, table.equipoId] }),
  }),
);

export type DeportistaEquipo = typeof DeportistaEquipos.$inferSelect;
export type NewDeportistaEquipo = typeof DeportistaEquipos.$inferInsert;
