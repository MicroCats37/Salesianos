import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { getUserSession } from "@/lib/auth/actions";
import { RUTAS } from "@/lib/routes";

/**
 * The layout of the registration.
 *
 * It is a layout of its OWN, outside the account family, because the form is
 * a FULL PAGE: the previous frontend gave it the whole width with the brand
 * lockup centered and nothing else around it. Inside the sidebar of the
 * account area the form was squeezed into a column and the page read as a
 * panel inside a panel.
 *
 * The session is still required: a registration belongs to a responsible.
 */
export default async function InscripcionLayout({
  children,
}: {
  children: ReactNode;
}) {
  const sesion = await getUserSession();

  if (!sesion) {
    redirect(
      `${RUTAS.auth.login}?next=${encodeURIComponent(RUTAS.cuenta.inscripcion)}`,
    );
  }

  return <>{children}</>;
}
