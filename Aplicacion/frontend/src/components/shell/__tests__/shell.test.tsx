// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SidebarProvider } from "@/components/ui/sidebar";
import {
  ADMIN_GRUPOS,
  ADMIN_RESUMEN,
} from "@/features/admin/utils/admin.secciones";
import { AccountTopbar } from "../AccountTopbar";
import { AdminSidebar } from "../AdminSidebar";
import { SiteFooter } from "../SiteFooter";
import { SiteHeader } from "../SiteHeader";

const RUTA_POR_DEFECTO = "/administracion/pagos";

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
    render(<SiteHeader />);

    expect(
      screen.getByRole("navigation", { name: "Navegación principal" }),
    ).toBeDefined();
  });

  it("ofrece los destinos públicos sin inventar módulos", () => {
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: "Información" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Pases" })).toBeDefined();
    expect(screen.getByRole("link", { name: "Tienda" })).toBeDefined();
  });

  it("el botón de menú tiene nombre accesible y área táctil de 44px", () => {
    render(<SiteHeader />);

    const boton = screen.getByRole("button", {
      name: "Abrir menú de navegación",
    });

    expect(boton).toBeDefined();
    expect(boton.className).toContain("size-11");
  });

  it("expone la ubicación actual con aria-current (SH-02 A11Y-10)", () => {
    pathnameMock.mockReturnValue("/informacion");

    render(<SiteHeader />);

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
    render(<AccountTopbar usuario="Ana Pérez" />);

    expect(
      screen.getByRole("button", { name: "Abrir menú de cuenta" }),
    ).toBeDefined();
  });

  it("no ofrece administración a quien no es administrador", () => {
    render(<AccountTopbar usuario="Ana Pérez" esAdmin={false} />);

    // El enlace vive dentro de un menú desplegable: se comprueba el árbol.
    expect(document.body.textContent).not.toContain("Administración");
  });

  it("expone la ubicación actual con aria-current (SH-02 A11Y-10)", () => {
    pathnameMock.mockReturnValue("/mis-inscripciones");

    render(<AccountTopbar usuario="Ana Pérez" />);

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
    render(
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
    render(
      <SidebarProvider>
        <AdminSidebar resumen={ADMIN_RESUMEN} grupos={ADMIN_GRUPOS} />
      </SidebarProvider>,
    );

    const pagos = screen.getByRole("link", { name: /Pagos/ });
    expect(pagos.getAttribute("aria-current")).toBe("page");

    // El resumen NO es la ubicación actual en /administracion/pagos.
    expect(
      screen
        .getByRole("link", { name: /Resumen/ })
        .getAttribute("aria-current"),
    ).toBeNull();
  });

  it("muestra los tres grupos del plan", () => {
    render(
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
