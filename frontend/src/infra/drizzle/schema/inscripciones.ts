import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { users } from './users';
import { promociones } from './promociones';
import { bases } from './bases';

export const inscripcionEstados = [
  'recibida',
  'en_revision',
  'observada',
  'validada',
  'pago_pendiente',
  'pagada',
  'confirmada',
  'rechazada',
] as const;
export type InscripcionEstado = (typeof inscripcionEstados)[number];

export const inscripciones = sqliteTable('inscripciones', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'restrict' }),
  promocionId: text('promocion_id').notNull().references(() => promociones.id, { onDelete: 'restrict' }),
  fusionPromocionId: text('fusion_promocion_id').references(() => promociones.id, { onDelete: 'restrict' }),
  basesId: text('bases_id').notNull().references(() => bases.id, { onDelete: 'restrict' }),
  paqueteMonto: real('paquete_monto').notNull(),
  teamName: text('team_name'),
  status: text('status', { enum: inscripcionEstados }).notNull().default('recibida'),
  observacion: text('observacion'),
  acceptedBases: integer('accepted_bases', { mode: 'boolean' }).notNull().default(false),
  declaracionJurada: integer('declaracion_jurada', { mode: 'boolean' }).notNull().default(false),
  fitnessDeclaration: integer('fitness_declaration', { mode: 'boolean' }).notNull().default(false),
  imageConsent: integer('image_consent', { mode: 'boolean' }).notNull().default(false),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type Inscripcion = typeof inscripciones.$inferSelect;
export type NewInscripcion = typeof inscripciones.$inferInsert;