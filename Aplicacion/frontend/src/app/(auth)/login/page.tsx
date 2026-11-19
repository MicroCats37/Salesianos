import { LoginClientShell } from "@/features/auth/views/LoginClientShell";

/**
 * AUTH-01 — Iniciar sesión en tu cuenta
 *
 * La ENVOLVENTE es de la feature de auth (`AuthShell`): banda de marca +
 * tarjeta de cristal. El formulario valida en cliente y el envío va al
 * endpoint congelado de autenticación.
 */
export default function LoginPage() {
  return <LoginClientShell />;
}
