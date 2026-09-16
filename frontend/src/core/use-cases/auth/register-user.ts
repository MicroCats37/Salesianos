import { hash } from "bcryptjs";
import { ConflictError, ValidationError } from "@/core/errors";
import type {
  SesionRepository,
  UserRepository,
} from "@/core/repositories/user.repository";
import { hashToken, signAccessToken } from "@/infra/auth/jwt";
import type { Genero, TipoDocumento, UserRole } from "@/infra/drizzle/schema";

export interface RegisterUserInput {
  email: string;
  password: string;
  tipoDocumento: TipoDocumento;
  numeroDocumento: string;
  nombres: string;
  apellidos: string;
  genero?: Genero | null;
  telefono?: string | null;
  whatsapp?: string | null;
  emergencyName?: string | null;
  emergencyPhone?: string | null;
}

export interface RegisterUserDeps {
  userRepository: UserRepository;
  sesionRepository: SesionRepository;
  rol?: UserRole;
}

export interface RegisterUserResult {
  user: {
    id: string;
    email: string;
    tipoDocumento: TipoDocumento;
    numeroDocumento: string;
    nombres: string;
    apellidos: string;
    genero: Genero | null;
    telefono: string | null;
    rol: UserRole;
  };
  expiresAt: Date;
  _accessToken: string;
}

const EMAIL_REGEX = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const MIN_PASSWORD_LENGTH = 8;
const MAX_FIELD_LENGTH = 120;

export async function registerUser(
  deps: RegisterUserDeps,
  input: RegisterUserInput,
): Promise<RegisterUserResult> {
  const fieldErrors: Record<string, string[]> = {};

  const normalizedEmail = (input.email ?? "").toLowerCase().trim();
  if (!normalizedEmail || !EMAIL_REGEX.test(normalizedEmail))
    fieldErrors.email = ["Email inválido"];
  if (!input.password || input.password.length < MIN_PASSWORD_LENGTH)
    fieldErrors.password = [
      `La contraseña debe tener al menos ${MIN_PASSWORD_LENGTH} caracteres`,
    ];
  if (!input.nombres?.trim()) fieldErrors.nombres = ["Nombres requeridos"];
  if (!input.apellidos?.trim())
    fieldErrors.apellidos = ["Apellidos requeridos"];
  if (!input.numeroDocumento?.trim())
    fieldErrors.numeroDocumento = ["Número de documento requerido"];
  if (input.tipoDocumento === "DNI" && !/^\d{8}$/.test(input.numeroDocumento))
    fieldErrors.numeroDocumento = ["DNI debe tener 8 dígitos"];
  if (input.tipoDocumento === "CE" && !/^\d{9}$/.test(input.numeroDocumento))
    fieldErrors.numeroDocumento = ["CE debe tener 9 dígitos"];

  if (Object.keys(fieldErrors).length > 0)
    throw new ValidationError("Datos inválidos", fieldErrors);

  const [existingEmail, existingDoc] = await Promise.all([
    deps.userRepository.findByEmail(normalizedEmail),
    deps.userRepository.findByNumeroDocumento(input.numeroDocumento),
  ]);

  if (existingEmail)
    throw new ConflictError("Email ya registrado", { field: "email" });
  if (existingDoc)
    throw new ConflictError("Documento ya registrado", {
      field: "numeroDocumento",
    });

  const passwordHash = await hash(input.password, 12);

  const userWithPersona = await deps.userRepository.create({
    persona: {
      tipoDocumento: input.tipoDocumento,
      numeroDocumento: input.numeroDocumento,
      nombres: input.nombres.trim(),
      apellidos: input.apellidos.trim(),
      genero: input.genero ?? null,
      telefono: input.telefono ?? null,
      whatsapp: input.whatsapp ?? null,
      contactoEmergenciaNombre: input.emergencyName ?? null,
      contactoEmergenciaTelefono: input.emergencyPhone ?? null,
    },
    user: {
      email: normalizedEmail,
      passwordHash,
      rol: deps.rol ?? "responsable",
    },
  });

  const accessToken = await signAccessToken({
    sub: userWithPersona.id,
    email: userWithPersona.email,
    rol: userWithPersona.rol,
  });
  const tokenHash = await hashToken(accessToken);
  const expiresAt = new Date(
    Date.now() +
      Number(process.env.JWT_ACCESS_TOKEN_TTL_SECONDS ?? 60 * 60 * 24 * 7) *
        1000,
  );

  await deps.sesionRepository.create({
    userId: userWithPersona.id,
    tokenHash,
    expiresAt,
  });

  return {
    user: {
      id: userWithPersona.id,
      email: userWithPersona.email,
      tipoDocumento: userWithPersona.persona.tipoDocumento,
      numeroDocumento: userWithPersona.persona.numeroDocumento,
      nombres: userWithPersona.persona.nombres,
      apellidos: userWithPersona.persona.apellidos,
      genero: userWithPersona.persona.genero,
      telefono: userWithPersona.persona.telefono,
      rol: userWithPersona.rol,
    },
    expiresAt,
    _accessToken: accessToken,
  };
}
