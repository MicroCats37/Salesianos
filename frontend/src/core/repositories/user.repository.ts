import type {
  NewPersona,
  NewUser,
  Persona,
  User,
  UserRole,
} from "@/infra/drizzle/schema";

export type UserWithPersona = User & { persona: Persona };

export interface CreateUserInput {
  persona: Omit<NewPersona, "id" | "createdAt" | "updatedAt">;
  user: Omit<NewUser, "id" | "personaId" | "createdAt" | "updatedAt">;
}

export interface UserRepository {
  findById(id: string): Promise<UserWithPersona | null>;
  findByEmail(email: string): Promise<UserWithPersona | null>;
  findByNumeroDocumento(
    numeroDocumento: string,
  ): Promise<UserWithPersona | null>;
  create(data: CreateUserInput): Promise<UserWithPersona>;
  updateRol(id: string, rol: UserRole): Promise<UserWithPersona>;
  delete(id: string): Promise<void>;
}
// Keep SesionRepository as is.
export interface SesionRepository {
  create(data: {
    userId: string;
    tokenHash: string;
    expiresAt: Date;
    userAgent?: string | null;
    ip?: string | null;
  }): Promise<{ id: string }>;
  findByTokenHash(tokenHash: string): Promise<{
    id: string;
    userId: string;
    expiresAt: Date;
    revokedAt: Date | null;
  } | null>;
  revoke(id: string): Promise<void>;
  revokeAllForUser(userId: string): Promise<void>;
  deleteExpired(): Promise<number>;
}
