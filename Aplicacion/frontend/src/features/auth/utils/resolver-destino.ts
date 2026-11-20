import { getUserSession } from "@/lib/auth/actions";
import { consumePostAuthRedirect } from "@/lib/post-auth-redirect";
import { RUTAS } from "@/lib/routes";

export const DESTINO_ADMIN = RUTAS.administracion.resumen;
export const DESTINO_POR_DEFECTO = RUTAS.cuenta.miCuenta;

/**
 * Decide a donde va la persona despues de autenticarse.
 *
 * La sesion la lee el servidor (`getUserSession`): el destino por defecto es
 * la cuenta, y la administracion solo cuando el backend confirma `es_admin`.
 * Un adminsitrador puede llevar a una persona a un sitio al que no tiene
 * acceso, asi que el filtro de la sesion manda.
 */
export async function resolverDeDestino(
  postAuth: string | null = consumePostAuthRedirect(),
): Promise<string> {
  if (postAuth) {
    return postAuth;
  }

  try {
    const sesion = await getUserSession();

    if (sesion?.es_admin || sesion?.is_staff || sesion?.is_superuser) {
      return DESTINO_ADMIN;
    }

    return DESTINO_POR_DEFECTO;
  } catch {
    return DESTINO_POR_DEFECTO;
  }
}
