import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const tipoDocumentos = ['DNI', 'CE', 'PAS'] as const;
export type TipoDocumento = (typeof tipoDocumentos)[number];

export const generos = ['V', 'M'] as const;
export type Genero = (typeof generos)[number];

export const personas = sqliteTable('personas', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  tipoDocumento: text('tipo_documento', { enum: tipoDocumentos }).notNull().default('DNI'),
  numeroDocumento: text('numero_documento').notNull().unique(),
  nombres: text('nombres').notNull(),
  apellidos: text('apellidos').notNull(),
  genero: text('genero', { enum: generos }),
  telefono: text('telefono'),
  whatsapp: text('whatsapp'),
  contactoEmergenciaNombre: text('contacto_emergencia_nombre'),
  contactoEmergenciaTelefono: text('contacto_emergencia_telefono'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Persona = typeof personas.$inferSelect;
export type NewPersona = typeof personas.$inferInsert;