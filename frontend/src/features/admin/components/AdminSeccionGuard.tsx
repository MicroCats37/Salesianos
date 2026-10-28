import { getAdminSession } from "../services/admin.session.server";
import {
  ADMIN_SECCIONES,
  adminSeccionesVisibles,
} from "../utils/admin.secciones";
import { AdminAccessDenied } from "./AdminAccessDenied";

/**
 * AdminSeccionGuard — the SERVER-SIDE guard of a section of the area.
 *
 * The layout of the area decides WHO may enter; this guard decides WHICH
 * section the caller may open. A direct URL (`/administracion/usuarios`)
 * never reaches a section the caller has no capability for.
 *
 * Rules:
 * - The authority is the BACKEND. The session is the revalidated answer of
 *   `GET /api/auth/me` (`getAdminSession`), never the Zustand store and never
 *   a session cookie: both are client-writable.
 * - It FAILS CLOSED. An unavailable backend, an empty capability set or a
 *   missing section means the children are NOT rendered.
 * - It does NOT duplicate the authority: the backend re-evaluates the
 *   capability on every request and answers 403. This guard only avoids
 *   rendering a page the caller may not open.
 *
 * It is a Server Component on purpose: it must not depend on the client
 * runtime for an authorization decision.
 */
export async function AdminSeccionGuard({
  seccionId,
  children,
}: {
  /** Identifier of the section, as declared in `ADMIN_SECCIONES`. */
  seccionId: string;
  children: React.ReactNode;
}) {
  const session = await getAdminSession();

  if (session.status !== "admin" || !session.esAdmin) {
    // The layout of the area already redirects or denies; the guard never
    // renders anything it cannot verify.
    return null;
  }

  const seccion = ADMIN_SECCIONES.find((item) => item.id === seccionId);

  if (!seccion) {
    return null;
  }

  const capacidades = session.user?.capacidades ?? [];
  const visible = adminSeccionesVisibles(capacidades, [seccion]);

  if (visible.length === 0) {
    return (
      <AdminAccessDenied message="No tienes permisos para abrir esta sección." />
    );
  }

  return <>{children}</>;
}
