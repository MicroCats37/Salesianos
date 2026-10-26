import { redirect } from "next/navigation";
import { AdminAccessDenied, AdminShell } from "@/features/admin/components";
import { revalidateAdminSession } from "@/features/admin/services/admin.guard.service";

/**
 * Layout of the `/administracion` area — the server-side admin guard.
 *
 * The guard is ADVISORY for the user experience but AUTHORITATIVE for the
 * access decision: it asks the backend who the caller is
 * (`GET /api/auth/me`) and reads the `es_admin` flag the backend computes
 * with the rule `admin = is_staff OR is_superuser` — the very same rule the
 * `RequireAdmin` permission applies to every admin endpoint.
 *
 * The `USER_SESSION` cookie is NEVER trusted as authority: it is a
 * client-writable snapshot that nothing revalidates
 * (`sdd/administracion-operativa-fest/admin-surface` §6).
 *
 * Outcomes:
 * - `admin` → the shell of the area is rendered.
 * - `forbidden` → "Acceso denegado" screen; the children are never rendered.
 * - `unauthenticated` → the caller has no usable access token → `/login`.
 * - `unavailable` → the backend could not confirm anything → the area FAILS
 *   CLOSED and the caller is sent back to the panel of the team.
 */
export default async function AdministracionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await revalidateAdminSession();

  if (session.status === "unauthenticated") {
    redirect("/login");
  }

  if (session.status === "unavailable") {
    redirect("/dashboard");
  }

  if (!session.esAdmin) {
    return <AdminAccessDenied />;
  }

  return <AdminShell>{children}</AdminShell>;
}
