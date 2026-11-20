// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SidebarProvider } from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  ADMIN_GRUPOS,
  ADMIN_RESUMEN,
} from "@/features/admin/utils/admin.secciones";
import { AccountTopbar } from "../AccountTopbar";
import { AdminSidebar } from "../AdminSidebar";
import { SiteFooter } from "../SiteFooter";
import { SiteHeader } from "../SiteHeader";

const RUTA_POR_DEFECTO = "/administracion/pagos";

/**
 * The shell renders INSIDE the providers of the application: the tooltips of
 * the theme switch (`ThemeToggle`) and of the sidebar (`AppSidebar`) need
 * `TooltipProvider`, which `src/providers/AppProviders.tsx` mounts.
 *
 * The harness mounts the SAME provider: without it every render of the shell
 * dies with "`Tooltip` must be used within `TooltipProvider`" and the
 * assertions never run.
 */
function renderShell(ui: React.ReactElement) {
  return render(
    <TooltipProvider delayDuration={0} skipDelayDuration={0}>
      {ui}
    </TooltipProvider>,
  );
}

const pathnameMock = vi.fn(() => RUTA_POR_DEFECTO);

// Cada prueba arranca en la misma ruta: una prueba que cambia la ruta no
// puede filtrationarla a la siguiente.
beforeEach(() => {
  pathnameMock.mockReturnValue(RUTA_POR_DEFECTO);
});

vi.mock("next/navigation", () => ({
  usePathname: () => pathnameMock(),
}));

/**
 * The shell tests.
 *
 * They freeze the three things the shell owns and the UI-0x packets cannot
 * change: the destinations that are offered, the name of the navigation for
 * assistive technology, and the marking of the current location.
 */
describe("shell — SiteHeader", () => {
  it("expone la navegación con nombre accesible", () => {
    renderShell(<SiteHeader />);

    expect(
      screen.getByRole("navigation", { name: "Navegación principal" }),
    ).toBeDefined();
  });

  it("ofrece los destinos públicos sin inventar módulos", () => {
    renderShell(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Información" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Pases" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Tienda" })).toBeDefined();
  });

  it("el botón de menú tiene nombre accesible y área táctil de 44px", () => {
    renderShell(<SiteHeader />);

    const boton = screen.getByRole("button", {
      name: "Abrir menú de navegación",
    });

    expect(boton).toBeDefined();
    expect(boton.className).toContain("size-11");
  });

  it("expone la ubicación actual con aria-current (SH-02 A11Y-10)", () => {
    pathnameMock.mockReturnValue("/informacion");

    renderShell(<SiteHeader />);

    const actual = screen.getByRole("link", { name: "Información" });
    expect(actual.getAttribute("aria-current")).toBe("page");

    // Los demás destinos NO se marcan: sólo uno es la ubicación actual.
    expect(
      screen.getByRole("link", { name: "Pases" }).getAttribute("aria-current"),
    ).toBeNull();
  });
});

describe("shell — AccountTopbar", () => {
  it("ofrece los destinos de la cuenta", () => {
    renderShell(<AccountTopbar usuario="Ana Pérez" />);

    expect(
      screen.getByRole("button", { name: "Abrir menú de cuenta" }),
    ).toBeDefined();
  });

  it("no ofrece administración a quien no es administrador", () => {
    renderShell(<AccountTopbar usuario="Ana Pérez" esAdmin={false} />);

    // El enlace vive dentro de un menú desplegable: se comprueba el árbol.
    expect(document.body.textContent).not.toContain("Administración");
  });

  it("expone la ubicación actual con aria-current (SH-02 A11Y-10)", () => {
    pathnameMock.mockReturnValue("/mis-inscripciones");

    renderShell(<AccountTopbar usuario="Ana Pérez" />);

    // El menú desplegable sólo existe en el DOM cuando está abierto.
    // jsdom no implementa PointerEvent, así que el menú se abre con el
    // teclado: Radix abre el menú con Enter sobre el disparador.
    fireEvent.keyDown(
      screen.getByRole("button", { name: "Abrir menú de cuenta" }),
      { key: "Enter" },
    );

    const actual = screen.getByRole("menuitem", { name: "Mis inscripciones" });
    expect(actual.getAttribute("aria-current")).toBe("page");

    expect(
      screen
        .getByRole("menuitem", { name: "Mi cuenta" })
        .getAttribute("aria-current"),
    ).toBeNull();
  });
});

describe("shell — AdminSidebar", () => {
  it("marca el destino activo con el veredicto de la ruta", () => {
    renderShell(
      <SidebarProvider>
        <AdminSidebar resumen={ADMIN_RESUMEN} grupos={ADMIN_GRUPOS} />
      </SidebarProvider>,
    );

    // La navegación es un conjunto de enlaces; el activo es "Pagos".
    const pagos = screen.getByRole("link", { name: /Pagos/ });
    expect(pagos).toBeDefined();
    expect(pagos.className).toContain("border-l-2");
  });

  it("expone la ubicación actual con aria-current (SH-02 A11Y-10)", () => {
    renderShell(
      <SidebarProvider>
        <AdminSidebar resumen={ADMIN_RESUMEN} grupos={ADMIN_GRUPOS} />
      </SidebarProvider>,
    );

    const pagos = screen.getByRole("link", { name: /Pagos/ });
    expect(pagos.getAttribute("aria-current")).toBe("page");

    // El resumen NO es la ubicación actual en /administracion/pagos.
    // El sidebar publica el resumen en la cabecera del grupo y en su
    // destino: la aserción mira TODOS los enlaces que lo nombran, para no
    // depender de cuál aparece primero en el DOM.
    for (const enlace of screen.getAllByRole("link", { name: /Resumen/ })) {
      expect(enlace.getAttribute("aria-current")).toBeNull();
    }
  });

  it("muestra los tres grupos del plan", () => {
    renderShell(
      <SidebarProvider>
        <AdminSidebar resumen={ADMIN_RESUMEN} grupos={ADMIN_GRUPOS} />
      </SidebarProvider>,
    );

    expect(screen.getByText("Deportivo")).toBeDefined();
    expect(screen.getByText("Ventas y entradas")).toBeDefined();
    expect(screen.getByText("Personas y configuración")).toBeDefined();
  });
});

describe("shell — SiteFooter", () => {
  it("expone la marca con nombre accesible", () => {
    render(<SiteFooter />);

    // La marca es una IMAGEN con alt real: es lo que la pauta exige para el
    // escudo y el wordmark. Si el módulo de marca no resuelve, el pie no
    // llega a renderizar y esta aserción falla antes de tiempo.
    expect(screen.getByAltText("Salesianos FEST")).toBeDefined();
  });

  it("el pie ofrece los enlaces de la edición", () => {
    render(<SiteFooter />);

    expect(
      screen.getByRole("navigation", { name: "Enlaces del pie" }),
    ).toBeDefined();
  });
});

/**
 * The chrome of every family of routes is the same CONTRACT, not the same
 * drawing: a landmark for the content and a link that jumps to it. The
 * administration area has the longest navigation of the product: without the
 * skip link a keyboard has to walk its fourteen destinations on every page
 * (WCAG 2.4.1).
 */
describe("shell — el chrome de cada familia de rutas", () => {
  const LAYOUTS = [
    "src/app/(public)/layout.tsx",
    "src/app/(auth)/layout.tsx",
    "src/app/(cuenta)/layout.tsx",
    "src/app/(administracion)/layout.tsx",
  ];

  it.each(LAYOUTS)("%s abre el contenido y ofrece el salto", (ruta) => {
    const fuente = readFileSync(join(process.cwd(), ruta), "utf8");

    expect(fuente).toContain('id="contenido"');
    expect(fuente).toContain("Saltar al contenido");
  });
});

/**
 * The logout of the account bar is a plain LINK: a link is a GET. The
 * handler used to answer POST only, so "Cerrar sesión" answered `405 Method
 * Not Allowed` and the session stayed alive.
 */
describe("shell — la salida de sesión", () => {
  it("el enlace de la cuenta apunta a un manejador que responde GET", () => {
    const barra = readFileSync(
      join(process.cwd(), "src/components/shell/AccountTopbar.tsx"),
      "utf8",
    );
    const manejador = readFileSync(
      join(process.cwd(), "src/app/api/auth/logout/route.ts"),
      "utf8",
    );

    expect(barra).toContain('href="/api/auth/logout"');
    expect(manejador).toContain("export async function GET");
    expect(manejador).toContain("export async function POST");
  });
});
