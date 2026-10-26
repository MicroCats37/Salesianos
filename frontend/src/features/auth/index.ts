// Auth feature module barrel
// UI

export { RegisterForm } from "./components";
// Constants
export {
  GENERO,
  TIPO_ACEPTACION,
  TIPO_DOCUMENTO,
} from "./constants/tipo-aceptacion";
// Hooks
export { useLogin, useRegister } from "./hooks";
// Schemas
export {
  type LoginDniFormData,
  LoginDniFormSchema,
  type LoginEmailFormData,
  LoginEmailFormSchema,
  type LoginUsernameFormData,
  LoginUsernameFormSchema,
  type MeResponse,
  type RegisterFormData,
  RegisterFormSchema,
  type RegisterResponse,
} from "./schemas";
// Store
export {
  type AuthSlice,
  type AuthUser,
  useAuthStore,
  useAuthUser,
} from "./store/auth.store";
// Utils
export {
  DESTINO_ADMIN,
  DESTINO_POR_DEFECTO,
  resolverDeDestino,
} from "./utils/resolver-destino";
export { LoginClientShell, RegisterClientShell } from "./views";
