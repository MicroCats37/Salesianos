import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { AdminSidebar } from "@/components/shell/AdminSidebar";
import { Button } from "@/components/ui/button";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
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
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[--radius-md] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <SidebarProvider>
        <AdminSidebar
          resumen={ADMIN_RESUMEN}
          grupos={grupos}
          usuario={nombre || sesion.email}
          superusuario={nivelLabel(sesion.nivel) === "Superusuario"}
        />

        <SidebarInset className="min-w-0">
          <header className="sticky top-0 z-(--z-sticky) flex h-16 items-center gap-3 border-b border-border bg-background/90 px-4 backdrop-blur sm:px-6">
            <SidebarTrigger className="size-11" aria-label="Abrir navegación" />
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-semibold text-foreground">
                Administración
              </span>
              <span className="truncate text-xs text-muted-foreground">
                {nivelLabel(sesion.nivel)}
              </span>
            </div>
            <Button variant="outline" size="sm" asChild className="ml-auto">
              <a href={RUTAS.cuenta.miCuenta}>Volver a mi cuenta</a>
            </Button>
          </header>

          <main id="contenido" className="min-w-0 flex-1 p-4 lg:p-6">
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
    </>
  );
}
