import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { AccountTopbar } from "@/components/shell/AccountTopbar";
import { AppShell } from "@/components/shell/AppShell";
import { RouteTransition } from "@/components/shell/RouteTransition";
import { adminEsAdministrador } from "@/features/admin/utils/admin.secciones";
import { getUserSession } from "@/lib/auth/actions";
import { RUTAS } from "@/lib/routes";

/**
 * The account layout.
 *
 * The account area shares the shell of the authenticated product: the same
 * sidebar, the same topbar and the same transition as the administration.
 * The difference is only the CONTENT of the navigation: here there are no
 * administration groups, because the backend never granted them.
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
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[var(--radius-md)] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <AppShell
        usuario={nombre || sesion.email}
        nivel={adminEsAdministrador(sesion) ? "Administrador" : "Responsable"}
        area="Mi cuenta"
        areaHref={RUTAS.cuenta.miCuenta}
        topbar={
          <AccountTopbar
            usuario={nombre || sesion.email}
            esAdmin={adminEsAdministrador(sesion)}
            conMarca={false}
          />
        }
      >
        {/*
          El ancho de la cuenta NO es el de la página pública: la matriz de
          cinco anchos (SH-02 §1.1) da a la cuenta 720 px a 768 y 1100 px
          desde 1024. A 360 y 390 manda la pantalla con su aire; a 1440 el
          contenedor respira más, pero no estira la línea de lectura.
        */}
        <main
          id="contenido"
          className="relative mx-auto w-full max-w-[720px] min-w-0 flex-1 bg-page-gradient px-4 py-8 sm:px-6 sm:py-10 lg:max-w-[1100px] lg:px-10"
        >
          <RouteTransition>{children}</RouteTransition>
        </main>
      </AppShell>
    </>
  );
}
