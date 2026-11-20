/**
 * Identity contract consumed by the shell and by the auth feature.
 *
 * These fields are the SESSION verdict the backend publishes. The shell reads
 * them; it never derives them. `es_admin` and `capacidades` are the backend's
 * answer, not a frontend decision.
 */
export interface MeResponse {
  id: string;
  email: string;
  nombres?: string;
  apellidos?: string;
  rol?: string;
  /** El usuario es administrador del evento (`is_staff OR is_superuser`). */
  es_admin?: boolean;
  /** El usuario es administrador operativo (`is_staff`). */
  is_staff?: boolean;
  /** El usuario tiene el nivel de break-glass (`is_superuser`). */
  is_superuser?: boolean;
  /** Nivel de privilegio del usuario: `usuario`, `staff` o `superusuario`. */
  nivel?: string;
  /** Capacidades administrativas del usuario (espejo de `core/capacidades.py`). */
  capacidades?: string[];
  /** ID de la persona asociada al usuario (null si el usuario no tiene persona vinculada). */
  persona_id?: string | null;
}

/**
 * The Zod mirrors of the identity dataset (`RT-ID-01`…`RT-ID-03`).
 *
 * They are the exact mirrors of the presenters of the `usuarios` module and
 * they replace the ad-hoc interfaces the feature carried before API-01.
 */
export {
  type DocumentoConsulta,
  DocumentoConsultaSchema,
  type Persona,
  type PersonaConfirmarIn,
  PersonaConfirmarInSchema,
  PersonaDatosSchema,
  PersonaIdentidadSchema,
  PersonaResolverInSchema,
  type PersonaResuelta,
  PersonaResueltaSchema,
  PersonaSchema,
} from "./identidad.schema";
export type {
  LoginDniFormData,
  LoginEmailFormData,
  LoginUsernameFormData,
} from "./login.schema";
export {
  LoginDniFormSchema,
  LoginEmailFormSchema,
  LoginUsernameFormSchema,
} from "./login.schema";
export {
  type RegisterFormData,
  RegisterFormSchema,
  type RegisterResponse,
} from "./register.schema";

/**
 * The Zod mirror of the session (`GET /auth/me`).
 */
export {
  SesionCuentaSchema,
  SesionIdentidadSchema,
  SesionRolSchema,
  type SesionUsuario,
  SesionUsuarioSchema,
} from "./sesion.schema";
