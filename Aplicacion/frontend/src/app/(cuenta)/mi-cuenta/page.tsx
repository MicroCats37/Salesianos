import { PanelSesion } from "@/features/cuenta/components";
import { MiCuentaView } from "@/features/cuenta/views";
import { getUserSession } from "@/lib/auth/actions";

/**
 * ACCOUNT-01 - Ver el resumen de tus operaciones
 *
 * El saludo se lee EN EL SERVIDOR: la sesión es de confianza y el nombre no
 * se pide al cliente.
 *
 * La guardia de la sesión se lee del BACKEND (`GET /auth/me`): la cookie puede
 * haber sobrevivido al token, y sólo el backend sabe si la sesión sigue viva.
 */
export default async function Page() {
  const sesion = await getUserSession();

  const nombre = [sesion?.nombres, sesion?.apellidos]
    .filter(Boolean)
    .join(" ")
    .trim();

  return (
    <div className="flex flex-col gap-6">
      <PanelSesion activo={Boolean(sesion)} />
      <MiCuentaView nombre={nombre || sesion?.email} />
    </div>
  );
}
