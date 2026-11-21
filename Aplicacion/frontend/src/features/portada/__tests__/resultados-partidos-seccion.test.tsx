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

import { ENCUENTROS_PUBLICOS } from "@/features/competencias/publico/__tests__/datos.contract";
import { ResultadosPartidosSection } from "@/features/portada/components/ResultadosPartidosSection";

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
    data: estado === "listo" ? ENCUENTROS_PUBLICOS : undefined,
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
    expect(screen.getByText("Ganó Salesianos B")).toBeInTheDocument();
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
        ...ENCUENTROS_PUBLICOS,
        total: 0,
        en_vivo: [],
        proximos: [],
        finalizados: [],
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
