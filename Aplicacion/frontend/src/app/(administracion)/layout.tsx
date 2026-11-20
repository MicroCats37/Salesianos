import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { RouteTransition } from "@/components/shell/RouteTransition";
import { adminNivelLabel as nivelLabel } from "@/features/admin/utils/admin.capacidades";
import {
  ADMIN_RESUMEN,
  adminEsAdministrador,
  adminGruposVisibles,
} from "@/features/admin/utils/admin.secciones";
import { getUserSession } from "@/lib/auth/actions";
import { RUTAS } from "@/lib/routes";

/**
 * The administration layout.
 *
 * The session is read HERE, on the server, and the visible destinations are
 * computed from the capabilities the backend granted. The client receives an
 * already filtered list: it never decides what an administrator may open.
 *
 * Hiding a destination is a courtesy. The control is the 403 of the backend.
 */
export default async function AdministracionLayout({
  children,
}: {
  children: ReactNode;
}) {
  const sesion = await getUserSession();

  if (!sesion) {
    redirect(
      `${RUTAS.auth.login}?next=${encodeURIComponent(RUTAS.administracion.resumen)}`,
    );
  }

  if (!adminEsAdministrador(sesion)) {
    redirect(RUTAS.cuenta.miCuenta);
  }

  const capacidades = sesion.capacidades ?? [];
  const grupos = adminGruposVisibles(capacidades);

  const nombre = [sesion.nombres, sesion.apellidos]
    .filter(Boolean)
    .join(" ")
    .trim();

  return (
    <>
      {/*
        El salto al contenido. El área de administración tiene la navegación
        más larga del producto: sin este enlace, un teclado debe recorrer
        los catorce destinos del sidebar en cada página (WCAG 2.4.1).
        Es el mismo enlace que usan las familias pública y de cuenta.
      */}
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[var(--radius-md)] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <AppShell
        resumen={ADMIN_RESUMEN}
        grupos={grupos}
        usuario={nombre || sesion.email}
        nivel={nivelLabel(sesion.nivel)}
        superusuario={nivelLabel(sesion.nivel) === "Superusuario"}
        area="Administración"
        areaHref={RUTAS.administracion.resumen}
      >
        <main
          id="contenido"
          className="relative min-w-0 flex-1 surface-page-gradient p-4 lg:p-6"
        >
          <RouteTransition>{children}</RouteTransition>
        </main>
      </AppShell>
    </>
  );
}
