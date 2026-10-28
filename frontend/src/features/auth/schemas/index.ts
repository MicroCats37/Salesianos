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
  /** ID de la persona asociada al usuario (null si no tiene persona vinculada). */
  persona_id?: string | null;
}

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
