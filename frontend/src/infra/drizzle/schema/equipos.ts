import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { inscripciones } from './inscripciones';
import { disciplinas } from './disciplinas';
import { categorias } from './categorias';

export const equipos = sqliteTable('equipos', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  inscripcionId: text('inscripcion_id').notNull().references(() => inscripciones.id, { onDelete: 'cascade' }),
  disciplinaId: text('disciplina_id').notNull().references(() => disciplinas.id, { onDelete: 'restrict' }),
  categoriaId: text('categoria_id').notNull().references(() => categorias.id, { onDelete: 'restrict' }),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Equipo = typeof equipos.$inferSelect;
export type NewEquipo = typeof equipos.$inferInsert;