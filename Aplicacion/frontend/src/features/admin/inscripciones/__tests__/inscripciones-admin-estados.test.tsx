// @vitest-environment jsdom

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { PanelPoolInscripcion } from "../components/PanelPoolInscripcion";
import {
  inscripcionAdminDetalle,
  listaInscripcionesAdmin,
  poolDeInscripcion,
} from "./inscripcion-admin.datos";
import { InscripcionAdminDetalleView } from "../views/InscripcionAdminDetalleView";
import { InscripcionesAdminView } from "../views/InscripcionesAdminView";

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
  usePathname: () => "/administracion/inscripciones",
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

describe("ADM-05 — el listado de las inscripciones", () => {
  it("sin datos muestra el estado honesto y NO una lista inventada", () => {
    renderConProveedor(<InscripcionesAdminView />);

    expect(
      screen.getByText("Todavía no hay inscripciones cargadas"),
    ).toBeDefined();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("con datos publica una fila por inscripción y el estado con su causa", () => {
    renderConProveedor(
      <InscripcionesAdminView
        estado={{ estado: "listo", datos: listaInscripcionesAdmin }}
      />,
    );

    expect(screen.getByRole("table")).toBeDefined();
    expect(screen.getByText("RESPONSABLE DE EJEMPLO")).toBeDefined();
    // La etiqueta del backend y su descripción; NUNCA el código.
    expect(screen.getByText("Inscripción creada")).toBeDefined();
    expect(screen.queryByText("CREADA")).toBeNull();
  });

  it("los tres cupos son tres hechos y no una fracción", () => {
    renderConProveedor(
      <InscripcionesAdminView
        estado={{ estado: "listo", datos: listaInscripcionesAdmin }}
      />,
    );

    expect(screen.getByText("Cupos adquiridos")).toBeDefined();
    expect(screen.getByText("Cupos asignados")).toBeDefined();
    expect(screen.getByText("Cupos disponibles")).toBeDefined();
  });
});

describe("ADM-06 — el detalle de la inscripción", () => {
  it("publica las cinco pestañas del plan", () => {
    renderConProveedor(<InscripcionAdminDetalleView id="inscripcion-1" />);

    expect(screen.getByRole("tab", { name: "Resumen" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Equipos" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Pool y personas" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Compras de cupos" })).toBeDefined();
    expect(screen.getByRole("tab", { name: "Historial" })).toBeDefined();
  });

  it("el resumen muestra los tres cupos y el estado con su motivo", () => {
    renderConProveedor(
      <InscripcionAdminDetalleView
        id="inscripcion-1"
        estado={{ estado: "listo", datos: inscripcionAdminDetalle }}
      />,
    );

    expect(screen.getByText("Adquiridos")).toBeDefined();
    expect(screen.getByText("Asignados")).toBeDefined();
    expect(screen.getByText("Disponibles")).toBeDefined();
  });
});

describe("ADM-06 — la retirada de una persona (S-10)", () => {
  it("la confirmación nombra el efecto, pide un motivo y no se puede ejecutar", () => {
    renderConProveedor(
      <PanelPoolInscripcion
        pool={poolDeInscripcion}
        personas={[
          {
            equipo: "EQUIPO DE EJEMPLO",
            participante: {
              id: "participacion-1",
              persona_id: "persona-1",
              nombre: "PERSONA DE EJEMPLO",
              documento: "00000000",
              rol: "JUGADOR",
              estado: "ACTIVA",
            },
          },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /retirar/i }));

    expect(
      screen.getByText(
        "Retirar participante libera su cupo en esta inscripción; no genera devolución.",
      ),
    ).toBeDefined();
    expect(screen.getByLabelText("Motivo de la retirada")).toBeDefined();
    expect(
      screen.getByRole("button", { name: "Retirar participante" }),
    ).toBeDisabled();
  });
});

const FUENTES = [
  "components/PanelPoolInscripcion.tsx",
  "components/DialogoRetirarParticipante.tsx",
  "views/InscripcionesAdminView.tsx",
  "views/InscripcionAdminDetalleView.tsx",
];

describe("la zona de las inscripciones no inventa colores literales (T-01)", () => {
  it.each(FUENTES)("%s no lleva un color literal", (ruta) => {
    const fuente = readFileSync(
      join(process.cwd(), "src", "features", "admin", "inscripciones", ruta),
      "utf8",
    );

    expect(fuente).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(fuente).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/);
    expect(fuente).not.toMatch(
      /\b(text|bg|border)-(red|blue|green|yellow|amber|emerald|slate|gray|zinc|neutral|stone)-[0-9]{2,3}\b/,
    );
  });
});
