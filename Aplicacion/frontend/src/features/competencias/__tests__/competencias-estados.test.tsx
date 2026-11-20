// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes, ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
  COMPETENCIA,
  DETALLE,
  ENCUENTRO,
  RONDA,
  VISTA_PREVIA_AVANCE,
  VISTA_PREVIA_CORRECCION,
} from "./datos.contract";
import { AgendaCompetenciasView } from "../views/AgendaCompetenciasView";
import { CompetenciaCuadroView } from "../views/CompetenciaCuadroView";
import { CompetenciaDetalleView } from "../views/CompetenciaDetalleView";
import { CompetenciasListaView } from "../views/CompetenciasListaView";

/**
 * The link and the router are shimmed: the suites verify the PRESENTATION of
 * the area, not the navigation of the framework.
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

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/competencias",
}));

/**
 * The states of the competitions area.
 *
 * **The suites of this packet have NEVER RUN.** They are written and the
 * execution is deferred to the verification phase (the standing preference
 * of the project). Nothing here may be read as a green result.
 */
describe("competencias - estados de las rutas", () => {
  it("ADM-10 muestra el estado honesto mientras el servicio no existe", () => {
    render(<CompetenciasListaView />);

    expect(
      screen.getByText("Todavía no hay competencias que mostrar"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/todavía no está disponible en el backend/i),
    ).toBeInTheDocument();
  });

  it("ADM-10 no dibuja ninguna competencia inventada", () => {
    render(<CompetenciasListaView />);

    expect(screen.queryByText("Copa Salesianos")).not.toBeInTheDocument();
  });

  it("ADM-10 lista la competencia con sus tres entradas cuando hay datos", () => {
    render(
      <CompetenciasListaView estado="listo" competencias={[COMPETENCIA]} />,
    );

    expect(screen.getAllByText("Copa Salesianos").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Planificada").length).toBeGreaterThan(0);

    // Los tres puntos de entrada son enlaces DISTINTOS y con nombre propio.
    expect(screen.getAllByRole("link", { name: /ver el detalle/i }).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /operar el cuadro/i }).length)
      .toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /ver la agenda/i }).length)
      .toBeGreaterThan(0);
  });

  it("ADM-10 explica el filtro vacío sin borrar los filtros", () => {
    render(
      <CompetenciasListaView
        estado="listo"
        competencias={[]}
        filtroEstado="PLANIFICADA"
      />,
    );

    expect(
      screen.getByRole("link", { name: /quitar el filtro/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/estado de la competencia/i)).toHaveValue(
      "PLANIFICADA",
    );
  });

  it("ADM-11 ofrece un equipo concreto cuando no hay ninguno", () => {
    render(<CompetenciaDetalleView id="7c1f0a52" estado="listo" />);

    expect(
      screen.getByText("Todavía no hay equipos en esta competencia"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Añade un equipo elegible/i),
    ).toBeInTheDocument();
  });

  it("ADM-11 nombra a los equipos y a los encuentros de la competencia", () => {
    render(
      <CompetenciaDetalleView
        id="7c1f0a52"
        estado="listo"
        detalle={DETALLE}
      />,
    );

    expect(screen.getByText("Colegio Norte")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Colegio Norte 2, Colegio Sur 1/ }),
    ).toBeInTheDocument();
  });

  it("ADM-12 pinta una columna por ronda y un botón por encuentro", () => {
    render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Octavos de final" }),
    ).toBeInTheDocument();

    const tarjeta = screen.getByRole("button", {
      name: /Colegio Norte 2, Colegio Sur 1/,
    });
    expect(tarjeta).toBeInTheDocument();
  });

  it("el cuadro se desplaza en horizontal dentro de su propio contenedor", () => {
    render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
      />,
    );

    const region = screen.getByRole("region", {
      name: /desplazable en horizontal/i,
    });
    expect(region.className).toContain("overflow-x-auto");
    expect(region).toHaveAttribute("tabindex", "0");
  });

  it("la tarjeta y la agenda abren EL MISMO detalle del encuentro", () => {
    const { unmount } = render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Colegio Norte 2, Colegio Sur 1/,
      }),
    );

    const panel = screen.getByRole("dialog");
    expect(panel).toBeInTheDocument();
    expect(
      screen.getByText(/Colegio Norte contra Colegio Sur/),
    ).toBeInTheDocument();
    unmount();

    render(
      <AgendaCompetenciasView
        estado="listo"
        agenda={{
          edicion_id: "0a1b2c3d",
          edicion_nombre: "Salesianos FEST 2026",
          fecha: "2026-11-21",
          total: 1,
          encuentros: [ENCUENTRO],
        }}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Colegio Norte 2, Colegio Sur 1/,
      }),
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(
      screen.getByText(/Colegio Norte contra Colegio Sur/),
    ).toBeInTheDocument();
  });

  it("la vista previa del avance dice que no escribe nada", () => {
    render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
        vistaPreviaAvancePorEncuentro={{
          [ENCUENTRO.id]: VISTA_PREVIA_AVANCE,
        }}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Colegio Norte 2, Colegio Sur 1/,
      }),
    );

    expect(
      screen.getByText(/Esta vista previa no escribe nada/),
    ).toBeInTheDocument();
    expect(screen.getByText("Colegio Norte")).toBeInTheDocument();
  });

  it("la vista previa de la corrección nombra a los descendientes afectados", () => {
    render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
        vistaPreviaCorreccionPorEncuentro={{
          [ENCUENTRO.id]: VISTA_PREVIA_CORRECCION,
        }}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Colegio Norte 2, Colegio Sur 1/,
      }),
    );

    expect(
      screen.getByText(/Vista previa de la corrección/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Esta vista previa no escribe nada/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Cambia de verdad: sí/)).toBeInTheDocument();
  });

  it("el panel nombra las acciones que el servidor admite", () => {
    render(
      <CompetenciaCuadroView
        id="7c1f0a52"
        estado="listo"
        rondas={[RONDA]}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: /Colegio Norte 2, Colegio Sur 1/,
      }),
    );

    expect(screen.getByText("Corregir el resultado")).toBeInTheDocument();
    expect(screen.getByText("Confirmar el avance")).toBeInTheDocument();
  });

  it("el bracket vacío ofrece la acción concreta, no un hueco genérico", () => {
    render(<CompetenciaCuadroView id="7c1f0a52" estado="listo" rondas={[]} />);

    expect(
      screen.getByText("Todavía no hay rondas en esta competencia"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Añade la primera ronda/i),
    ).toBeInTheDocument();
  });

  it("el estado de permiso y el error recuperable son estados distintos", () => {
    const { unmount } = render(
      <CompetenciasListaView estado="sin-permiso" />,
    );
    expect(
      screen.getByText(/No tienes permiso para ver esta sección/),
    ).toBeInTheDocument();
    unmount();

    render(<CompetenciasListaView estado="error" />);
    expect(
      screen.getByText("No pudimos cargar las competencias"),
    ).toBeInTheDocument();
  });

  it("ninguna presentación usa un color literal ni un tono de paleta", () => {
    const { container } = render(
      <CompetenciasListaView estado="listo" competencias={[COMPETENCIA]} />,
    );

    const html = container.innerHTML;
    expect(html).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(html).not.toMatch(/\b(bg|text|border)-(red|blue|green|yellow|slate|gray|zinc|neutral|stone)-\d{2,3}\b/);
  });
});
