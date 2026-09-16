import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { inscripciones } from './inscripciones';
import { personas } from './personas';

export const DeportistaRoles = ['Capitán', 'Delegado', 'Jugador'] as const;
export type DeportistaRol = (typeof DeportistaRoles)[number];

export const AcreditacionTipos = ['Verificación en padrón', 'Excepción aprobada'] as const;
export type AcreditacionTipo = (typeof AcreditacionTipos)[number];

export const TallaCamisetas = ['XS', 'S', 'M', 'L', 'XL', 'XXL'] as const;
export type TallaCamiseta = (typeof TallaCamisetas)[number];

export const deportistas = sqliteTable('deportistas', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  inscripcionId: text('inscripcion_id').notNull().references(() => inscripciones.id, { onDelete: 'cascade' }),
  personaId: text('persona_id').notNull().references(() => personas.id, { onDelete: 'restrict' }),
  rolDisciplina: text('rol_disciplina', { enum: DeportistaRoles }).notNull().default('Jugador'),
  acreditacion: text('acreditacion', { enum: AcreditacionTipos }).notNull().default('Verificación en padrón'),
  shirtSize: text('shirt_size'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Deportista = typeof deportistas.$inferSelect;
export type NewDeportista = typeof deportistas.$inferInsert;