import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const disciplinaCodigos = ['fulbito_var', 'fulbito_dam', 'voley_mix', 'basket_var'] as const;
export type DisciplinaCodigo = (typeof disciplinaCodigos)[number];

export const disciplinas = sqliteTable('disciplinas', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  codigo: text('codigo', { enum: disciplinaCodigos }).notNull().unique(),
  nombre: text('nombre').notNull(),
  maxJugadores: integer('max_jugadores').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Disciplina = typeof disciplinas.$inferSelect;
export type NewDisciplina = typeof disciplinas.$inferInsert;