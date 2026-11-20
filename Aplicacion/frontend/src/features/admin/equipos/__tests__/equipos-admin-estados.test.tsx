// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  equipoAdminDetalle,
  listaEquiposAdmin,
} from "./equipo-admin.datos";
import { EquipoAdminDetalleView } from "../views/EquipoAdminDetalleView";
import { EquiposAdminView } from "../views/EquiposAdminView";

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/equipos",
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

describe("ADM-07 — el listado de los equipos", () => {
  it("sin datos muestra el estado honesto y NO una lista inventada", () => {
    render(<EquiposAdminView />);

    expect(screen.getByText("Todavía no hay equipos cargados")).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("cada equipo explica por qué puede o no competir", () => {
    render(
      <EquiposAdminView
        estado={{ estado: "listo", datos: listaEquiposAdmin }}
      />,
    );

    // La etiqueta del backend y su descripción; NUNCA el código.
    expect(screen.getByText("Falta 1 jugador")).toBeDefined();
    expect(
      screen.getByText("Se necesita al menos 7 jugadores para competir"),
    ).toBeDefined();
    expect(screen.queryByText("INCOMPLETO")).toBeNull();
  });

  it("el roster se muestra como los tres hechos que es", () => {
    render(
      <EquiposAdminView
        estado={{ estado: "listo", datos: listaEquiposAdmin }}
      />,
    );

    // 6 registradas, mínimo 7, máximo 10: la cifra visible es "6 / 7–10" y
    // la frase completa la lleva un lector de pantalla.
    expect(screen.getByText(/6\s*\/ 7–10/)).toBeDefined();
    expect(
      screen.getByText("6 jugadores registrados; mínimo 7; máximo 10"),
    ).toBeDefined();
  });

  it("la fila ofrece la acción «Ver equipo»", () => {
    render(
      <EquiposAdminView
        estado={{ estado: "listo", datos: listaEquiposAdmin }}
      />,
    );

    expect(screen.getByRole("link", { name: /Ver equipo/ })).toBeDefined();
  });
});

describe("ADM-08 — el detalle del equipo", () => {
  it("sin datos muestra el estado honesto", () => {
    render(<EquipoAdminDetalleView id="equipo-1" />);

    expect(screen.getByText("No se pudo cargar este equipo")).toBeDefined();
  });

  it("la elegibilidad reproduce el veredicto del backend con su motivo", () => {
    render(
      <EquipoAdminDetalleView
        id="equipo-1"
        estado={{ estado: "listo", datos: equipoAdminDetalle }}
      />,
    );

    expect(screen.getByText("Sin cupo deportivo disponible")).toBeDefined();
    expect(
      screen.getByText(
        "No hay cupos deportivos disponibles en esta inscripción para sumar a otra persona.",
      ),
    ).toBeDefined();
  });

  it("la nómina muestra el documento y el estado de cada persona", () => {
    render(
      <EquipoAdminDetalleView
        id="equipo-1"
        estado={{ estado: "listo", datos: equipoAdminDetalle }}
      />,
    );

    expect(screen.getByText("PERSONA DE EJEMPLO")).toBeDefined();
    expect(screen.getByText("00000000")).toBeDefined();
    expect(screen.getByText("ACTIVA")).toBeDefined();
  });

  it("las acciones proyectadas se muestran pero NO se pueden ejecutar", () => {
    render(
      <EquipoAdminDetalleView
        id="equipo-1"
        estado={{ estado: "listo", datos: equipoAdminDetalle }}
      />,
    );

    expect(
      screen.getByRole("button", { name: /Agregar jugador/ }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /Ver participantes/ }),
    ).toBeDisabled();
  });
});

const FUENTES = [
  "components/PlantillaEquipo.tsx",
  "components/PanelPlantillaEquipo.tsx",
  "views/EquiposAdminView.tsx",
  "views/EquipoAdminDetalleView.tsx",
];

describe("la zona de los equipos no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "equipos", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});

describe("la zona de los equipos NO deduce la incompletitud en el navegador", () => {
  it.each(FUENTES)("%s no compara el roster con el mínimo", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "equipos", ruta),
      "utf8",
    );

    // Prohibido cruzar `registrados` con `minimo`/`maximo`: el veredicto es
    // del backend (`contratos/01` §7).
    expect(fuente).not.toMatch(/registrados\s*[<>=!]=?\s*(plantilla\.)?minimo/);
    expect(fuente).not.toMatch(/minimo\s*[<>=!]=?\s*(plantilla\.)?registrados/);
    expect(fuente).not.toMatch(/maximo\s*-\s*registrados/);
  });
});
