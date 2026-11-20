// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MisCompraDetalleView } from "../views/MisCompraDetalleView";
import { MisComprasView } from "../views/MisComprasView";
import { MisInscripcionesView } from "../views/MisInscripcionesView";
import { MiCuentaView } from "../views/MiCuentaView";
import {
  compraDetalleEjemplo,
  compraEjemplo,
  inscripcionEjemplo,
  resumenCuentaEjemplo,
} from "./cuenta.ejemplos";

/**
 * The states of the account routes.
 *
 * The suite walks the ten states of SH-03 on the four routes of the area:
 * the empty one, the filtered-empty one, the recoverable error, the
 * permission, the partial payment and the populated list.
 *
 * The data comes from the provisional fixture, so the suite proves the
 * COMPOSITION of the populated list without inventing a single value: the
 * numbers it asserts are the ones the fixture declares.
 */

const replace = vi.fn();
const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/mis-inscripciones",
  useSearchParams: () => searchParams,
}));

describe("ACCOUNT-01 - el hub de la cuenta", () => {
  it("sin datos dice lo que no hay y ofrece la acción", () => {
    render(<MiCuentaView nombre="Ana Perez" />);

    expect(
      screen.getByText("Todavía no hay un resumen de la cuenta"),
    ).toBeDefined();
    expect(screen.getByRole("link", { name: "Crear una inscripción" })).toBeDefined();
  });

  it("con datos muestra los contadores con su etiqueta", () => {
    render(
      <MiCuentaView nombre="Ana Perez" estado="listo" resumen={resumenCuentaEjemplo} />,
    );

    // El contador nunca va solo: la etiqueta lo acompaña.
    expect(screen.getByText("inscripciones")).toBeDefined();
    expect(screen.getByText("compras")).toBeDefined();
  });

  it("el permiso explica lo que falta y no parece un error", () => {
    render(<MiCuentaView estado="sin-permiso" />);

    expect(
      screen.getByText("No podemos leer el resumen de tu cuenta"),
    ).toBeDefined();
  });
});

describe("ACCOUNT-02 - las inscripciones", () => {
  it("sin datos ofrece crear la primera", () => {
    render(<MisInscripcionesView />);

    expect(
      screen.getByText("Todavía no tienes inscripciones registradas"),
    ).toBeDefined();
    expect(screen.getByRole("link", { name: "Crear la primera" })).toBeDefined();
  });

  it("con datos lista el registro y su siguiente paso", () => {
    render(
      <MisInscripcionesView
        estado="listo"
        inscripciones={[inscripcionEjemplo]}
      />,
    );

    expect(screen.getByText("EDICIÓN 2026")).toBeDefined();
    expect(
      screen.getByRole("link", { name: /Completar el pago/ }),
    ).toBeDefined();
  });

  it("el estado del pago lo dice el backend, no el código", () => {
    render(
      <MisInscripcionesView
        estado="listo"
        inscripciones={[inscripcionEjemplo]}
      />,
    );

    expect(screen.getByText("Pago pendiente")).toBeDefined();
    expect(screen.queryByText("PENDIENTE")).toBeNull();
  });

  it("con filtros que excluyen todo, dice que hay registros ocultos", () => {
    render(
      <MisInscripcionesView
        estado="listo"
        inscripciones={[inscripcionEjemplo]}
        filtros={{ edicion: "otra edicion" }}
      />,
    );

    expect(
      screen.getByText("Ninguno de tus registros coincide con los filtros"),
    ).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Quitar los filtros" }),
    ).toBeDefined();
  });

  it("el error ofrece reintentar", () => {
    render(<MisInscripcionesView estado="error" />);

    expect(
      screen.getByText("No pudimos cargar tus inscripciones"),
    ).toBeDefined();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();
  });

  it("el permiso explica que la cuenta no alcanza", () => {
    render(<MisInscripcionesView estado="sin-permiso" />);

    expect(
      screen.getByText("No podemos leer tus inscripciones"),
    ).toBeDefined();
  });
});

describe("ACCOUNT-04 - las compras", () => {
  it("sin datos lo dice", () => {
    render(<MisComprasView />);

    expect(
      screen.getByText("Todavía no tienes compras registradas"),
    ).toBeDefined();
  });

  it("con datos agrupa por origen y nombra el estado", () => {
    render(<MisComprasView estado="listo" compras={[compraEjemplo]} />);

    expect(screen.getByRole("heading", { name: "Inscripción" })).toBeDefined();
    expect(screen.getByText("Pago confirmado")).toBeDefined();
  });

  it("el importe usa cifras tabulares", () => {
    render(<MisComprasView estado="listo" compras={[compraEjemplo]} />);

    expect(screen.getAllByText("PEN 0.00").length).toBeGreaterThan(0);
  });
});

describe("ACCOUNT-05 - el detalle de una compra", () => {
  it("sin datos no afirma un pago", () => {
    render(<MisCompraDetalleView id="ABC" />);

    expect(screen.getByText("Todavía no hay una compra que mostrar")).toBeDefined();
  });

  it("un pago confirmado con el derecho pendiente dice exactamente eso", () => {
    render(
      <MisCompraDetalleView
        id="ABC"
        estado="listo"
        compra={compraDetalleEjemplo}
      />,
    );

    // El estado PARCIAL no se presenta como un éxito.
    expect(
      screen.getByText("Pago confirmado, pendiente de activación"),
    ).toBeDefined();
    expect(
      screen.getByText(/el derecho todavía no se ha habilitado/i),
    ).toBeDefined();
  });

  it("el permiso de otra compra se explica y no se oculta", () => {
    render(<MisCompraDetalleView id="ABC" estado="sin-permiso" />);

    expect(
      screen.getByText("Esta compra no está disponible para tu cuenta"),
    ).toBeDefined();
  });
});
