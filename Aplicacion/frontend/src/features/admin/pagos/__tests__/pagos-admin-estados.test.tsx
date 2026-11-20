// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { detallePagoAdmin, listaPagosAdmin } from "./pago-admin.datos";
import { PagosAdminView } from "../views/PagosAdminView";

/**
 * The renders of this suite happen inside a `QueryClientProvider`: the S-10
 * dialog owns its mutation hook and a hook of TanStack Query needs the
 * provider. The provider is created per render and it NEVER retries: a suite
 * that forces an operation must not wait for a retry.
 */
function renderConProveedor(elemento: ReactNode) {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return render(
    <QueryClientProvider client={cliente}>{elemento}</QueryClientProvider>,
  );
}

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/pagos",
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

describe("ADM-14 — el listado operativo de los pagos", () => {
  it("sin datos muestra el estado honesto y NO una lista inventada", () => {
    renderConProveedor(<PagosAdminView />);

    expect(screen.getByText("Todavía no hay compras cargadas")).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("cada fila tiene UN estado comprensible, el del backend", () => {
    renderConProveedor(
      <PagosAdminView
        estado={{ estado: "listo", datos: listaPagosAdmin }}
      />,
    );

    expect(screen.getByText("Pago pendiente")).toBeDefined();
    expect(
      screen.getByText("El pago todavía no ha sido confirmado."),
    ).toBeDefined();
    // NUNCA el código de la máquina.
    expect(screen.queryByText("PENDIENTE")).toBeNull();
  });

  it("el filtro por estado operativo está EXPUESTO (obligación congelada)", () => {
    renderConProveedor(<PagosAdminView />);

    expect(screen.getByRole("button", { name: /Filtros/ })).toBeDefined();
  });
});

describe("ADM-14 — los tres niveles", () => {
  it("el detalle comercial y el diagnóstico viven en un panel aparte", () => {
    renderConProveedor(
      <PagosAdminView
        estado={{ estado: "listo", datos: listaPagosAdmin }}
        detalles={{ [listaPagosAdmin[0].compra_id]: detallePagoAdmin }}
      />,
    );

    expect(screen.getByRole("button", { name: /Ver compra/ })).toBeDefined();
  });

  it("el diagnóstico está OCULTO por defecto y sólo aparece al abrirlo", () => {
    renderConProveedor(
      <PagosAdminView
        estado={{ estado: "listo", datos: listaPagosAdmin }}
        detalles={{ [listaPagosAdmin[0].compra_id]: detallePagoAdmin }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Ver compra/ }));

    // Nivel 2: el detalle comercial.
    expect(screen.getByText("Estado del pago")).toBeDefined();
    expect(screen.getByText("Lo que obtuvo")).toBeDefined();
    expect(screen.getByText("Siguiente acción permitida")).toBeDefined();

    // Nivel 3: el diagnóstico, detrás de un descriptor.
    const diagnostico = screen.getByRole("button", {
      name: /Diagnóstico y auditoría/,
    });
    expect(diagnostico).toBeDefined();
  });

  it("la capa del proveedor NO hereda el color de un veredicto", () => {
    renderConProveedor(
      <PagosAdminView
        estado={{ estado: "listo", datos: listaPagosAdmin }}
        detalles={{ [listaPagosAdmin[0].compra_id]: detallePagoAdmin }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Ver compra/ }));
    fireEvent.click(
      screen.getByRole("button", { name: /Diagnóstico y auditoría/ }),
    );

    // El estado del intento es TEXTO dentro del diagnóstico, no un chip.
    expect(screen.getByText(/Intento 1 · PENDIENTE/)).toBeDefined();
  });
});

const FUENTES = [
  "components/ListaPagosOperativa.tsx",
  "components/DetalleComercialPago.tsx",
  "components/DialogoAprobarPagoManual.tsx",
  "views/PagosAdminView.tsx",
];

describe("la zona de los pagos no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "pagos", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("el veredicto de un pago NUNCA se deriva de los campos crudos", () => {
  it.each(FUENTES)("%s no cruza compra, orden e intento para decidir", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "pagos", ruta),
      "utf8",
    );

    // Prohibido derivar el veredicto cruzando los estados crudos
    // (`GOV-02-RB-06a` · `contratos/01` §1.4).
    expect(fuente).not.toMatch(/estado_operativo\.codigo\s*===/);
    expect(fuente).not.toMatch(/compra\.estado\s*===/);
    expect(fuente).not.toMatch(/orden\.estado\s*===/);
    expect(fuente).not.toMatch(/intento\.estado\s*===/);
  });
});
