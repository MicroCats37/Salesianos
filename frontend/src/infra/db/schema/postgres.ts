/**
 * PostgreSQL schema — uses drizzle-orm/postgres-core pgTable.
 * All tables use now() for timestamp defaults and native boolean type.
 */
import { sql } from "drizzle-orm";
import {
  boolean,
  integer,
  pgTable,
  primaryKey,
  text,
  timestamp,
} from "drizzle-orm/pg-core";

// ── Enums (TypeScript only, not baked into PostgreSQL) ────────────────────────

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

export const personas = pgTable("personas", {
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
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
  updatedAt: timestamp("updated_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Persona = typeof personas.$inferSelect;
export type NewPersona = typeof personas.$inferInsert;

export const users = pgTable("users", {
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
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
  updatedAt: timestamp("updated_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;

export const sesiones = pgTable("sesiones", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  userId: text("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  tokenHash: text("token_hash").notNull().unique(),
  expiresAt: timestamp("expires_at", { mode: "date" }).notNull(),
  revokedAt: timestamp("revoked_at", { mode: "date" }),
  userAgent: text("user_agent"),
  ip: text("ip"),
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Sesion = typeof sesiones.$inferSelect;
export type NewSesion = typeof sesiones.$inferInsert;

export const promociones = pgTable("promociones", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  anio: integer("anio").notNull().unique(),
  colegio: text("colegio", { enum: colegios }).notNull(),
  nombre: text("nombre"),
  activa: boolean("activa").notNull().default(true),
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Promocion = typeof promociones.$inferSelect;
export type NewPromocion = typeof promociones.$inferInsert;

export const disciplinas = pgTable("disciplinas", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  codigo: text("codigo", { enum: disciplinaCodigos }).notNull().unique(),
  nombre: text("nombre").notNull(),
  maxJugadores: integer("max_jugadores").notNull(),
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Disciplina = typeof disciplinas.$inferSelect;
export type NewDisciplina = typeof disciplinas.$inferInsert;

export const categorias = pgTable("categorias", {
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
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Categoria = typeof categorias.$inferSelect;
export type NewCategoria = typeof categorias.$inferInsert;

export const bases = pgTable("bases", {
  id: text("id")
    .primaryKey()
    .$defaultFn(() => crypto.randomUUID()),
  version: text("version").notNull().unique(),
  aprobadoEn: timestamp("aprobado_en", { mode: "date" }).notNull(),
  contenidoUrl: text("contenido_url"),
  activo: boolean("activo").notNull().default(true),
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Base = typeof bases.$inferSelect;
export type NewBase = typeof bases.$inferInsert;

export const inscripciones = pgTable("inscripciones", {
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
  acceptedBases: boolean("accepted_bases").notNull().default(false),
  declaracionJurada: boolean("declaracion_jurada").notNull().default(false),
  fitnessDeclaration: boolean("fitness_declaration").notNull().default(false),
  imageConsent: boolean("image_consent").notNull().default(false),
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
  updatedAt: timestamp("updated_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Inscripcion = typeof inscripciones.$inferSelect;
export type NewInscripcion = typeof inscripciones.$inferInsert;

export const equipos = pgTable("equipos", {
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
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Equipo = typeof equipos.$inferSelect;
export type NewEquipo = typeof equipos.$inferInsert;

export const deportistas = pgTable("deportistas", {
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
  createdAt: timestamp("created_at", { mode: "date" })
    .notNull()
    .default(sql`now()`),
});

export type Deportista = typeof deportistas.$inferSelect;
export type NewDeportista = typeof deportistas.$inferInsert;

export const DeportistaEquipos = pgTable(
  "deportista_equipos",
  {
    DeportistaId: text("deportista_id")
      .notNull()
      .references(() => deportistas.id, { onDelete: "cascade" }),
    equipoId: text("equipo_id")
      .notNull()
      .references(() => equipos.id, { onDelete: "cascade" }),
    createdAt: timestamp("created_at", { mode: "date" })
      .notNull()
      .default(sql`now()`),
  },
  (table) => ({
    pk: primaryKey({ columns: [table.DeportistaId, table.equipoId] }),
  }),
);

export type DeportistaEquipo = typeof DeportistaEquipos.$inferSelect;
export type NewDeportistaEquipo = typeof DeportistaEquipos.$inferInsert;
