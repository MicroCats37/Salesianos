import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { AccountTopbar } from "@/components/shell/AccountTopbar";
import { adminEsAdministrador } from "@/features/admin/utils/admin.secciones";
import { getUserSession } from "@/lib/auth/actions";
import { RUTAS } from "@/lib/routes";

/**
 * The account layout.
 *
 * The responsible has five destinations, so there is no sidebar here: a slim
 * top bar and the menu of the user. `/mi-cuenta` is the hub.
 *
 * The guard is a COURTESY, not a control: the session cookie is writable by
 * the client and the backend re-evaluates every capability on every request.
 */
export default async function CuentaLayout({
  children,
}: {
  children: ReactNode;
}) {
  const sesion = await getUserSession();

  if (!sesion) {
    redirect(
      `${RUTAS.auth.login}?next=${encodeURIComponent(RUTAS.cuenta.miCuenta)}`,
    );
  }

  const nombre = [sesion.nombres, sesion.apellidos]
    .filter(Boolean)
    .join(" ")
    .trim();

  return (
    <div className="flex min-h-svh flex-col">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[--radius-md] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <AccountTopbar
        usuario={nombre || sesion.email}
        esAdmin={adminEsAdministrador(sesion)}
      />

      <main
        id="contenido"
        className="mx-auto w-full max-w-[1100px] flex-1 px-4 py-8 sm:px-6 lg:px-8"
      >
        {children}
      </main>
    </div>
  );
}
