// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { listaParticipantesAdmin } from "./participante-admin.datos";
import { ParticipantesAdminView } from "../views/ParticipantesAdminView";

vi.mock("next/navigation", () => ({
  usePathname: () => "/administracion/participantes",
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

describe("ADM-09 — la búsqueda de personas y participaciones", () => {
  it("sin búsqueda muestra un AVISO, no una tabla vacía", () => {
    render(<ParticipantesAdminView />);

    expect(
      screen.getByText("Busca a una persona para empezar"),
    ).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("con búsqueda y sin datos muestra el estado honesto", () => {
    render(<ParticipantesAdminView parametros={{ q: "00000000" }} />);

    expect(screen.getByText("No se pudo cargar esta búsqueda")).toBeDefined();
  });

  it("con datos publica las participaciones y el motivo del conflicto", () => {
    render(
      <ParticipantesAdminView
        parametros={{ q: "00000000" }}
        estado={{ estado: "listo", datos: listaParticipantesAdmin }}
      />,
    );

    expect(screen.getByText("PERSONA DE EJEMPLO")).toBeDefined();
    expect(
      screen.getByText("Esta persona ya participa en la misma disciplina en este equipo."),
    ).toBeDefined();
  });

  it("publica los tres agrupamientos del plan", () => {
    render(
      <ParticipantesAdminView
        parametros={{ q: "00000000" }}
        estado={{ estado: "listo", datos: listaParticipantesAdmin }}
      />,
    );

    expect(screen.getByRole("tab", { name: "Por evento" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Por equipo" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Por disciplina" })).toBeDefined();
  });
});

const FUENTES = ["views/ParticipantesAdminView.tsx"];

describe("la zona de los participantes no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "participantes", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});
