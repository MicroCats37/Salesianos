import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const colegios = ['sjb', 'ma'] as const;
export type Colegio = (typeof colegios)[number];

export const promociones = sqliteTable('promociones', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  anio: integer('anio').notNull().unique(),
  colegio: text('colegio', { enum: colegios }).notNull(),
  nombre: text('nombre'),
  activa: integer('activa', { mode: 'boolean' }).notNull().default(true),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Promocion = typeof promociones.$inferSelect;
export type NewPromocion = typeof promociones.$inferInsert;