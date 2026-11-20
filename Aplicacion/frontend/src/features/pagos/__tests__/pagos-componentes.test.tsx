// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EstadoPagoActivacion } from "../components/EstadoPagoActivacion";
import type { EstadoActivacion } from "../types/pagos.types";
import { veredictoActivacionDesdeEstado } from "../utils/pagos.adaptador.utils";

/**
 * The chip of the ACTIVATION channel (`XCT-03`).
 *
 * The suite proves the four rules the surface depends on:
 *
 * 1. the wording of the backend is printed VERBATIM and the code never
 *    reaches the screen;
 * 2. the explanation appears only when the surface asks for it;
 * 3. an unknown code renders NEUTRALLY and does not break;
 * 4. the colour never travels alone: the icon and the text travel with it.
 */
const ESTADO: EstadoActivacion = {
  codigo: "ACTIVADA",
  etiqueta: "Entrada activada",
  descripcion: "Tu entrada está habilitada y lista para el festival.",
  recuperable: false,
  proxima_accion: "NINGUNA",
};

describe("el chip de la activación de derechos", () => {
  it("muestra la palabra del backend y nunca el código", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    render(<EstadoPagoActivacion veredicto={veredicto} />);

    expect(screen.getByText("Entrada activada")).toBeDefined();
    expect(screen.queryByText("ACTIVADA")).toBeNull();
  });

  it("la explicación del backend aparece sólo cuando se pide", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    const { rerender } = render(<EstadoPagoActivacion veredicto={veredicto} />);

    expect(screen.queryByText(ESTADO.descripcion)).toBeNull();

    rerender(<EstadoPagoActivacion veredicto={veredicto} conDescripcion />);

    expect(screen.getByText(ESTADO.descripcion)).toBeDefined();
  });

  it("un código desconocido se dibuja de forma neutra y no rompe", () => {
    const veredicto = veredictoActivacionDesdeEstado({
      ...ESTADO,
      codigo: "CODIGO_DEL_FUTURO",
    });

    render(<EstadoPagoActivacion veredicto={veredicto} />);

    expect(veredicto.rol).toBe("desconocido");
    expect(screen.getByText("Entrada activada")).toBeDefined();
  });

  it("el color nunca va solo: el chip trae icono y texto", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    const { container } = render(
      <EstadoPagoActivacion veredicto={veredicto} />,
    );

    expect(container.querySelector("svg")).not.toBeNull();
    expect(screen.getByText("Entrada activada")).toBeDefined();
  });

  it("el chip no ofrece una acción que no puede cumplir", () => {
    const veredicto = veredictoActivacionDesdeEstado(ESTADO);

    render(<EstadoPagoActivacion veredicto={veredicto} />);

    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });
});
