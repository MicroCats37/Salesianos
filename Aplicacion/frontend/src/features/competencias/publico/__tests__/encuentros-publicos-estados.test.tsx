// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { EncuentrosPublicosView } from "../views/EncuentrosPublicosView";
import { ENCUENTROS_PUBLICOS } from "./datos.contract";

/**
 * The link and the router are shimmed: the suite verifies the PRESENTATION of
 * the public page, not the navigation of the framework.
 */
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>
      {children as ReactNode}
    </a>
  ),
}));

/**
 * The states of the public page of the matches.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 */
describe("partidos - estados de la ruta pública", () => {
  it("espera al servidor mientras lee los partidos", () => {
    render(<EncuentrosPublicosView estado="cargando" />);

    expect(screen.getByText(/Cargando los partidos/i)).toBeInTheDocument();
  });

  it("el error ofrece la acción que lo resuelve", () => {
    render(
      <EncuentrosPublicosView
        estado="error"
        mensajeError="No se pudo leer el estado de los partidos."
        reintentar={() => undefined}
      />,
    );

    expect(
      screen.getByText(/No pudimos cargar los partidos/i),
    ).toBeInTheDocument();
    // El mensaje del servidor se muestra VERBATIM.
    expect(
      screen.getByText("No se pudo leer el estado de los partidos."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Reintentar/i }),
    ).toBeInTheDocument();
  });

  it("dice la verdad cuando todavía no hay partidos publicados", () => {
    render(<EncuentrosPublicosView estado="listo" />);

    expect(
      screen.getByText(/Todavía no hay partidos publicados/i),
    ).toBeInTheDocument();
  });

  it("muestra los TRES cubos que publicó el servidor", () => {
    render(
      <EncuentrosPublicosView
        estado="listo"
        encuentros={ENCUENTROS_PUBLICOS}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /En vivo/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Próximos/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Últimos resultados/i }),
    ).toBeInTheDocument();
  });

  it("dibuja el encuentro de cada cubo", () => {
    render(
      <EncuentrosPublicosView
        estado="listo"
        encuentros={ENCUENTROS_PUBLICOS}
      />,
    );

    // El encuentro en juego, el programado y el finalizado.
    expect(screen.getAllByText("Salesianos A").length).toBeGreaterThan(0);
    expect(screen.getByText(/Set 1: 9-4/)).toBeInTheDocument();
    expect(screen.getByText("Últimos resultados")).toBeInTheDocument();
  });

  it("el ganador es el que publicó el backend, NO el que va ganando", () => {
    render(
      <EncuentrosPublicosView
        estado="listo"
        encuentros={ENCUENTROS_PUBLICOS}
      />,
    );

    // El marcador es 9 a 4 y el ganador es Salesianos B.
    expect(screen.getByText("Ganó Salesianos B")).toBeInTheDocument();
    expect(screen.queryByText("Ganó Salesianos A")).not.toBeInTheDocument();
  });

  it("no inventa un reloj ni un grupo ni una tabla de posiciones", () => {
    render(
      <EncuentrosPublicosView
        estado="listo"
        encuentros={ENCUENTROS_PUBLICOS}
      />,
    );

    expect(screen.queryByText(/tabla de posiciones/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/cancha/i)).not.toBeInTheDocument();
  });

  it("ofrece la vuelta a la portada", () => {
    render(
      <EncuentrosPublicosView
        estado="listo"
        encuentros={ENCUENTROS_PUBLICOS}
      />,
    );

    expect(
      screen.getByRole("link", { name: /Volver a la portada/i }),
    ).toHaveAttribute("href", "/");
  });
});
