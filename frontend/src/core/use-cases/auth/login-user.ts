import { compare } from "bcryptjs";
import { PermissionDeniedError, ValidationError } from "@/core/errors";
import type {
  SesionRepository,
  UserRepository,
} from "@/core/repositories/user.repository";
import { hashToken, signAccessToken } from "@/infra/auth/jwt";
import type { UserRole } from "@/infra/drizzle/schema";

export interface LoginUserInput {
  identifier: string;
  password: string;
}

export interface LoginUserDeps {
  userRepository: UserRepository;
  sesionRepository: SesionRepository;
}

export interface LoginUserResult {
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
  expiresAt: Date;
  _accessToken: string;
}

export async function loginUser(
  deps: LoginUserDeps,
  input: LoginUserInput,
): Promise<LoginUserResult> {
  const fieldErrors: Record<string, string[]> = {};
  if (!input.identifier?.trim()) {
    fieldErrors.identifier = ["Email o número de documento requerido"];
  }
  if (!input.password) {
    fieldErrors.password = ["Contraseña requerida"];
  }
  if (Object.keys(fieldErrors).length > 0) {
    throw new ValidationError("Datos inválidos", fieldErrors);
  }

  const identifier = input.identifier.toLowerCase().trim();
  const user =
    (await deps.userRepository.findByEmail(identifier)) ??
    (await deps.userRepository.findByNumeroDocumento(identifier));

  if (!user || !(await compare(input.password, user.passwordHash))) {
    throw new PermissionDeniedError("Credenciales inválidas");
  }

  const accessToken = await signAccessToken({
    sub: user.id,
    email: user.email,
    rol: user.rol,
  });
  const tokenHash = await hashToken(accessToken);
  const expiresAt = new Date(
    Date.now() +
      Number(process.env.JWT_ACCESS_TOKEN_TTL_SECONDS ?? 60 * 60 * 24 * 7) *
        1000,
  );

  await deps.sesionRepository.create({
    userId: user.id,
    tokenHash,
    expiresAt,
  });

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
    expiresAt,
    _accessToken: accessToken,
  };
}
