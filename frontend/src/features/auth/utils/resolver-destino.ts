import { getAdminMe } from "@/features/admin/services/admin.me.service";
import { consumePostAuthRedirect } from "@/lib/post-auth-redirect";

export const DESTINO_ADMIN = "/administracion";
export const DESTINO_POR_DEFECTO = "/dashboard";

export async function resolverDeDestino(
  postAuth: string | null = consumePostAuthRedirect(),
): Promise<string> {
  if (postAuth) {
    return postAuth;
  }

  try {
    const envelope = await getAdminMe();

    if (envelope.success && envelope.data?.es_admin === true) {
      return DESTINO_ADMIN;
    }

    return DESTINO_POR_DEFECTO;
  } catch {
    return DESTINO_POR_DEFECTO;
  }
}
