import { PermissionDeniedError } from "@/core/errors";
import type {
  SesionRepository,
  UserRepository,
} from "@/core/repositories/user.repository";
import { getAuthCookie } from "@/infra/auth/cookies";
import { hashToken, verifyAccessToken } from "@/infra/auth/jwt";
import type { UserRole } from "@/infra/drizzle/schema";

export interface GetCurrentUserDeps {
  userRepository: UserRepository;
  sesionRepository: SesionRepository;
}

export interface GetCurrentUserResult {
  user: {
    id: string;
    email: string;
    tipoDocumento: string;
    numeroDocumento: string;
    nombres: string;
    apellidos: string;
    genero: string | null;
    telefono: string | null;
    rol: UserRole;
  };
}

export async function getCurrentUser(
  deps: GetCurrentUserDeps,
): Promise<GetCurrentUserResult> {
  const token = await getAuthCookie();
  if (!token) throw new PermissionDeniedError("No autenticado");

  const payload = await verifyAccessToken(token);
  if (!payload) throw new PermissionDeniedError("No autenticado");

  const tokenHash = await hashToken(token);
  const sesion = await deps.sesionRepository.findByTokenHash(tokenHash);
  if (!sesion || sesion.revokedAt || sesion.expiresAt < new Date()) {
    throw new PermissionDeniedError("No autenticado");
  }

  const user = await deps.userRepository.findById(payload.sub);
  if (!user) throw new PermissionDeniedError("No autenticado");

  return {
    user: {
      id: user.id,
      email: user.email,
      tipoDocumento: user.persona.tipoDocumento,
      numeroDocumento: user.persona.numeroDocumento,
      nombres: user.persona.nombres,
      apellidos: user.persona.apellidos,
      genero: user.persona.genero,
      telefono: user.persona.telefono,
      rol: user.rol,
    },
  };
}
