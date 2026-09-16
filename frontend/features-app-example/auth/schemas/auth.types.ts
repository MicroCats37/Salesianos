/**
 * Auth types for Mesa de Partes — CIP
 * Endpoints: login username, login dni, login email
 */

// ── Login Mode ────────────────────────────────────────────────────────────────

/** Discriminated union for login mode */
export type LoginMode = "username" | "dni" | "email";

// ── Login Response ───────────────────────────────────────────────────────────

export interface LoginTokens {
  access_token: string;
  refresh_token: string;
  expires_at: string;
}

/**
 * User basic data (datos) returned from login and /auth/me/ endpoint.
 */
export interface UserDatos {
  id: string;
  username: string;
  dni: string | null;
  email: string | null;
  nombres: string | null;
  apellidos: string | null;
  is_staff: boolean;
  is_superuser: boolean;
}

/**
 * Area assigned to the user (vigente/active).
 */
export interface AreaAsignada {
  id: string;
  area_id: string;
  area_nombre: string;
  cargo_id: string;
  cargo_nombre: string;
}

/**
 * User info returned from login and /auth/me/ endpoint.
 * Nested structure with datos and areas_asignadas_vigentes.
 */
export interface MeResponse {
  datos: UserDatos;
  areas_asignadas_vigentes: AreaAsignada[];
}

/**
 * Respuesta de login del backend: access_token + refresh_token + expires_at + user
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_at: string;
  user: MeResponse;
}
