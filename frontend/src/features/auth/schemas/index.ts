export interface MeResponse {
  id: string;
  email: string;
  nombres?: string;
  apellidos?: string;
  rol?: string;
  /** ID de la persona asociada al usuario (null si no tiene persona vinculada). */
  persona_id?: string | null;
}

export {
  LoginUsernameFormSchema,
  LoginDniFormSchema,
  LoginEmailFormSchema,
} from "./login.schema";
export type {
  LoginUsernameFormData,
  LoginDniFormData,
  LoginEmailFormData,
} from "./login.schema";

export {
  RegisterFormSchema,
  type RegisterFormData,
  type RegisterResponse,
} from "./register.schema";
