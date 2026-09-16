import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const bases = sqliteTable('bases', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  version: text('version').notNull().unique(),
  aprobadoEn: integer('aprobado_en', { mode: 'timestamp' }).notNull(),
  contenidoUrl: text('contenido_url'),
  activo: integer('activo', { mode: 'boolean' }).notNull().default(true),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Base = typeof bases.$inferSelect;
export type NewBase = typeof bases.$inferInsert;