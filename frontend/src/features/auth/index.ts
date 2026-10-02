// Auth feature module barrel
// UI
export { LoginClientShell } from "./views";
export { RegisterClientShell } from "./views";
export { RegisterForm } from "./components";

// Schemas
export {
  LoginUsernameFormSchema,
  LoginDniFormSchema,
  LoginEmailFormSchema,
  RegisterFormSchema,
  type LoginUsernameFormData,
  type LoginDniFormData,
  type LoginEmailFormData,
  type RegisterFormData,
  type RegisterResponse,
  type MeResponse,
} from "./schemas";

// Store
export {
  useAuthStore,
  useAuthUser,
  type AuthUser,
  type AuthSlice,
} from "./store/auth.store";

// Hooks
export { useLogin } from "./hooks";
export { useRegister } from "./hooks";

// Constants
export { TIPO_ACEPTACION, TIPO_DOCUMENTO, GENERO } from "./constants/tipo-aceptacion";
