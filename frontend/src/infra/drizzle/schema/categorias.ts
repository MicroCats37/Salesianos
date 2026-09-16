import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { disciplinas } from './disciplinas';

export const categoriaCodigos = ['junior', 'senior', 'master', 'super_master'] as const;
export type CategoriaCodigo = (typeof categoriaCodigos)[number];

export const categorias = sqliteTable('categorias', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  disciplinaId: text('disciplina_id').notNull().references(() => disciplinas.id, { onDelete: 'cascade' }),
  codigo: text('codigo', { enum: categoriaCodigos }).notNull(),
  nombre: text('nombre').notNull(),
  anioMin: integer('anio_min').notNull(),
  anioMax: integer('anio_max').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Categoria = typeof categorias.$inferSelect;
export type NewCategoria = typeof categorias.$inferInsert;