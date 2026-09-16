import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer, primaryKey } from 'drizzle-orm/sqlite-core';
import { deportistas } from './deportistas';
import { equipos } from './equipos';

export const DeportistaEquipos = sqliteTable('deportista_equipos', {
  DeportistaId: text('deportista_id').notNull().references(() => deportistas.id, { onDelete: 'cascade' }),
  equipoId: text('equipo_id').notNull().references(() => equipos.id, { onDelete: 'cascade' }),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
}, (table) => ({
  pk: primaryKey({ columns: [table.DeportistaId, table.equipoId] }),
}));

export type DeportistaEquipo = typeof DeportistaEquipos.$inferSelect;
export type NewDeportistaEquipo = typeof DeportistaEquipos.$inferInsert;