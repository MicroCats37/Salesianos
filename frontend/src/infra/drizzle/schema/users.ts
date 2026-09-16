import { sql } from 'drizzle-orm';
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { personas } from './personas';

export const userRoles = ['responsable', 'admin_comite', 'admin_finanzas'] as const;
export type UserRole = (typeof userRoles)[number];

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  personaId: text('persona_id').notNull().references(() => personas.id, { onDelete: 'restrict' }).unique(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  rol: text('rol', { enum: userRoles }).notNull().default('responsable'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;