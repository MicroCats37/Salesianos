import { eq } from "drizzle-orm";
import { db, schema } from "@/infra/drizzle/client";
import type { UserRepository, UserWithPersona, CreateUserInput } from "@/core/repositories/user.repository";
import type { SesionRepository } from "@/core/repositories/user.repository";
import type { UserRole } from "@/infra/drizzle/schema";

export class DrizzleUserRepository implements UserRepository {
  async findById(id: string): Promise<UserWithPersona | null> {
    const rows = await db
      .select()
      .from(schema.users)
      .innerJoin(schema.personas, eq(schema.users.personaId, schema.personas.id))
      .where(eq(schema.users.id, id))
      .limit(1);
    if (!rows[0]) return null;
    return { ...rows[0].users, persona: rows[0].personas };
  }

  async findByEmail(email: string): Promise<UserWithPersona | null> {
    const rows = await db
      .select()
      .from(schema.users)
      .innerJoin(schema.personas, eq(schema.users.personaId, schema.personas.id))
      .where(eq(schema.users.email, email.toLowerCase()))
      .limit(1);
    if (!rows[0]) return null;
    return { ...rows[0].users, persona: rows[0].personas };
  }

  async findByNumeroDocumento(numeroDocumento: string): Promise<UserWithPersona | null> {
    const rows = await db
      .select()
      .from(schema.users)
      .innerJoin(schema.personas, eq(schema.users.personaId, schema.personas.id))
      .where(eq(schema.personas.numeroDocumento, numeroDocumento))
      .limit(1);
    if (!rows[0]) return null;
    return { ...rows[0].users, persona: rows[0].personas };
  }

  async create(data: CreateUserInput): Promise<UserWithPersona> {
    return db.transaction(async (tx: any) => {
      const [persona] = await tx
        .insert(schema.personas)
        .values(data.persona)
        .returning();
      const [user] = await tx
        .insert(schema.users)
        .values({
          ...data.user,
          personaId: persona.id,
          email: data.user.email.toLowerCase(),
        })
        .returning();
      return { ...user, persona };
    });
  }

  async updateRol(id: string, rol: UserRole): Promise<UserWithPersona> {
    const [user] = await db
      .update(schema.users)
      .set({ rol, updatedAt: new Date() })
      .where(eq(schema.users.id, id))
      .returning();
    if (!user) throw new Error(`User ${id} not found`);
    const [persona] = await db
      .select()
      .from(schema.personas)
      .where(eq(schema.personas.id, user.personaId));
    return { ...user, persona };
  }

  async delete(id: string): Promise<void> {
    await db.delete(schema.users).where(eq(schema.users.id, id));
  }
}

export class DrizzleSesionRepository implements SesionRepository {
  async create(data: {
    userId: string;
    tokenHash: string;
    expiresAt: Date;
    userAgent?: string | null;
    ip?: string | null;
  }): Promise<{ id: string }> {
    const rows = await db
      .insert(schema.sesiones)
      .values(data)
      .returning({ id: schema.sesiones.id });
    return rows[0];
  }

  async findByTokenHash(tokenHash: string) {
    const rows = await db
      .select({
        id: schema.sesiones.id,
        userId: schema.sesiones.userId,
        expiresAt: schema.sesiones.expiresAt,
        revokedAt: schema.sesiones.revokedAt,
      })
      .from(schema.sesiones)
      .where(eq(schema.sesiones.tokenHash, tokenHash))
      .limit(1);
    return rows[0] ?? null;
  }

  async revoke(id: string): Promise<void> {
    await db
      .update(schema.sesiones)
      .set({ revokedAt: new Date() })
      .where(eq(schema.sesiones.id, id));
  }

  async revokeAllForUser(userId: string): Promise<void> {
    await db
      .update(schema.sesiones)
      .set({ revokedAt: new Date() })
      .where(eq(schema.sesiones.userId, userId));
  }

  async deleteExpired(): Promise<number> {
    const result = await db
      .delete(schema.sesiones)
      .where(eq(schema.sesiones.expiresAt, new Date(0)))
      .returning();
    return result.length;
  }
}
