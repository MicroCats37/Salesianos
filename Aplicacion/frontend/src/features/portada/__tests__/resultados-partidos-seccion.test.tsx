// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { useEncuentrosPublicos } = vi.hoisted(() => ({
  useEncuentrosPublicos: vi.fn(),
}));

vi.mock("@/features/competencias/publico/hooks/useEncuentrosPublicos", () => ({
  useEncuentrosPublicos,
}));
vi.mock(
  "@/features/competencias/publico/hooks/useEncuentrosPublicosRealtime",
  () => ({ useEncuentrosPublicosRealtime: vi.fn() }),
);

/**
 * The shell of the landing is not the subject of this suite: the section is
 * verified with its own content and its own link.
 */
vi.mock("@/features/portada/components/PortadaSection", () => ({
  PortadaSection: ({ children }: { children: ReactNode }) => (
    <section>{children}</section>
  ),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: ReactNode;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import { ResultadosPartidosSection } from "@/features/portada/components/ResultadosPartidosSection";

const partido = (id: string, status: "live" | "scheduled" | "final") => ({
  id,
  group_id: "A",
  stage: "group" as const,
  position: 0,
  home_id: "1999",
  away_id: "2007",
  home_name: "Salesianos A",
  away_name: "Salesianos B",
  scheduled_at: "2026-11-21T14:00:00Z",
  court: "A",
  duration_minutes: 30,
  status,
  home_score: status === "scheduled" ? null : 1,
  away_score: status === "scheduled" ? null : 2,
  home_penalties: null,
  away_penalties: null,
  winner_id: status === "final" ? "2007" : null,
  decision: status === "final" ? "score" : null,
  elapsed_seconds: 0,
  running: status === "live",
  segment: "regular",
  live_points: { home: 0, away: 3 },
});

const TORNEO_PUBLICO = {
  ready: true,
  tournament: "Salesianos FEST 2026",
  discipline: "Fulbito",
  category: "Interpromociones",
  server_time: "2026-11-21T14:00:00Z",
  groups: [
    {
      id: "A",
      revision: 0,
      teams: [
        { id: "1999", name: "Salesianos A", group_id: "A" },
        { id: "2007", name: "Salesianos B", group_id: "A" },
      ],
      table: [],
      matches: [
        partido("live", "live"),
        partido("next", "scheduled"),
        partido("final", "final"),
      ],
    },
  ],
  knockout: [],
  teams: [],
};

/**
 * The compact summary of the matches on the landing.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 */
beforeEach(() => {
  useEncuentrosPublicos.mockReset();
});

function lectura(estado: "listo" | "cargando" | "error") {
  useEncuentrosPublicos.mockReturnValue({
    data: estado === "listo" ? TORNEO_PUBLICO : undefined,
    isPending: estado === "cargando",
    isError: estado === "error",
  });
}

describe("portada - el resumen de los partidos", () => {
  it("enlaza con la página dedicada de los partidos", () => {
    lectura("listo");

    render(<ResultadosPartidosSection />);

    expect(
      screen.getByRole("link", { name: /VER TODOS LOS PARTIDOS/i }),
    ).toHaveAttribute("href", "/partidos");
  });

  it("resume el estado real de los partidos", () => {
    lectura("listo");

    render(<ResultadosPartidosSection />);

    // Los tres cubos, con el nombre de los equipos que el servidor publicó.
    expect(
      screen.getByRole("heading", { name: "En vivo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Próximos" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Últimos resultados" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Salesianos A").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Salesianos B").length).toBeGreaterThan(0);
  });

  it("NO confunde un partido en juego con una transmisión", () => {
    lectura("listo");

    render(<ResultadosPartidosSection />);

    // El resumen habla de PARTIDOS: la señal es otra sección y otra ruta.
    expect(screen.queryByText(/señal/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/transmisión/i)).not.toBeInTheDocument();
  });

  it("espera al servidor sin inventar partidos", () => {
    lectura("cargando");

    render(<ResultadosPartidosSection />);

    expect(
      screen.getByText(/Cargando el estado de los partidos/i),
    ).toBeInTheDocument();
    expect(screen.queryByText("Salesianos A")).not.toBeInTheDocument();
  });

  it("dice la verdad cuando todavía no hay partidos publicados", () => {
    lectura("listo");
    useEncuentrosPublicos.mockReturnValue({
      data: {
        ...TORNEO_PUBLICO,
        groups: [],
        knockout: [],
      },
      isPending: false,
      isError: false,
    });

    render(<ResultadosPartidosSection />);

    expect(
      screen.getByText(/Los partidos se publicarán aquí/i),
    ).toBeInTheDocument();
  });

  it("una lectura fallida no rompe la portada", () => {
    lectura("error");

    render(<ResultadosPartidosSection />);

    expect(
      screen.getByText(/No pudimos leer el estado de los partidos/i),
    ).toBeInTheDocument();
    // El enlace a la página dedicada SIGUE disponible: la sección es un
    // resumen, no una puerta.
    expect(
      screen.getByRole("link", { name: /VER TODOS LOS PARTIDOS/i }),
    ).toBeInTheDocument();
  });
});
