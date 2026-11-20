import type { ReactNode } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import type {
  AdminDestino,
  AdminGrupo,
} from "@/features/admin/utils/admin.secciones";
import { AppSidebar } from "./AppSidebar";
import { AppTopbar } from "./AppTopbar";

export interface AppShellProps {
  children: ReactNode;
  /** The groups of administration, already filtered by capability. */
  grupos?: AdminGrupo[];
  /** The summary of the administration area, when it exists. */
  resumen?: AdminDestino;
  /** Label of the signed-in account, shown in the footer. */
  usuario?: string;
  /** The tier of the account, shown in the topbar and in the footer. */
  nivel: string;
  /** Whether the account holds the break-glass tier. */
  superusuario?: boolean;
  /** The name of the area, under the logo and in the breadcrumb. */
  area: string;
  /** The route of the area, the first crumb of the breadcrumb. */
  areaHref: string;
  /**
   * The chrome of the area, when it is not the shared topbar.
   *
   * The account area uses its own bar because its menu carries the links
   * that only exist for a signed-in account; the rest of the chrome is
   * identical.
   */
  topbar?: ReactNode;
}

/**
 * AppShell - the chrome of the AUTHENTICATED product.
 *
 * There is ONE shell for the whole authenticated product: the account area
 * and the administration area share the sidebar, the topbar and the
 * transition. The difference between them is the CONTENT of the sidebar: the
 * groups of administration appear only when the backend granted the
 * capability that opens them.
 *
 * The area is a console: the surface of the content is the page, and the
 * chrome stays where it is while the content changes.
 *
 * The `<main>` belongs to the layout, not to the shell: each area decides
 * how wide its content is, and the landmark with its skip link stays in the
 * file that owns it.
 */
export function AppShell({
  children,
  grupos = [],
  resumen,
  usuario,
  nivel,
  superusuario = false,
  area,
  areaHref,
  topbar,
}: AppShellProps) {
  const destinos = resumen
    ? [resumen, ...grupos.flatMap((grupo) => grupo.destinos)]
    : [];

  return (
    <SidebarProvider>
      <AppSidebar
        grupos={grupos}
        resumen={resumen}
        usuario={usuario}
        nivel={nivel}
        superusuario={superusuario}
        area={area}
      />

      {/*
        El contenido del área.

        El shell NO es dueño del `<main>`: cada layout declara su propio
        `<main id="contenido">`, con su enlace de salto, y así el área
        cuenta con UN SOLO landmark de contenido. Por eso el contenedor del
        shell es una `div` y no el `SidebarInset` de shadcn, que es un
        `<main>`: usarlo aquí anidaría dos `main` y rompería la estructura
        de landmarks que el layout publica.

        El tratamiento visual del inset (el margen, la esquina redondeada y
        la sombra de la variante `inset`) sí es el del producto, y por eso
        se replica aquí con los mismos roles.
      */}
      <div
        data-slot="sidebar-inset"
        className="relative flex w-full min-w-0 flex-1 flex-col bg-background md:peer-data-[variant=inset]:m-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-[var(--radius-xl)] md:peer-data-[variant=inset]:shadow-sm md:peer-data-[variant=inset]:peer-data-[state=collapsed]:ml-2"
      >
        {topbar ?? (
          <AppTopbar
            nivel={nivel}
            usuario={usuario}
            area={area}
            areaHref={areaHref}
            destinos={destinos}
          />
        )}

        {children}
      </div>
    </SidebarProvider>
  );
}
