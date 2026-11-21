// @vitest-environment jsdom

import { fireEvent, render, screen, within } from "@testing-library/react";
import type { FormEvent, ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  guardarGrupo: vi.fn(),
  guardarGrupoCompleto: vi.fn(),
  guardarLlave: vi.fn(),
  controlarPartido: vi.fn(),
}));

vi.mock("../hooks/useEncuentrosPublicos", () => ({
  useEncuentrosPublicos: () => ({ data: TORNEO, isPending: false }),
}));

vi.mock("../hooks/useEncuentrosPublicosRealtime", () => ({
  useEncuentrosPublicosRealtime: () => ({ estado: "conectado" }),
}));

vi.mock("../hooks/useTorneoAdmin", () => ({
  useGuardarGrupoTorneo: () => ({
    isPending: false,
    mutate: mocks.guardarGrupoCompleto,
    mutateAsync: mocks.guardarGrupo,
  }),
  useGuardarLlaveTorneo: () => ({
    isPending: false,
    mutate: vi.fn(),
    mutateAsync: mocks.guardarLlave,
  }),
  useControlarPartidoTorneo: () => ({
    isPending: false,
    mutateAsync: mocks.controlarPartido,
  }),
}));

vi.mock("@/components/genericForm/GenericForm", () => ({
  GenericForm: ({
    children,
    initialData,
    onSubmit,
  }: {
    children: (state: {
      isSubmitting: boolean;
      submissionMessage: null;
    }) => ReactNode;
    initialData: unknown;
    onSubmit: (data: unknown) => Promise<unknown>;
  }) => (
    <form
      onSubmit={(event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        void onSubmit(initialData);
      }}
    >
      {children({ isSubmitting: false, submissionMessage: null })}
    </form>
  ),
}));

import { TorneoAdminRuta } from "../views/TorneoAdminRuta";

const teamA = { id: "team-a", name: "Equipo A", group_id: "A" };
const teamB = { id: "team-b", name: "Equipo B", group_id: "A" };

const match = (id: string, court: string, position: number) => ({
  id,
  group_id: "A",
  stage: "group" as const,
  category: "Senior",
  title: null,
  position,
  home_id: teamA.id,
  away_id: teamB.id,
  home_name: teamA.name,
  away_name: teamB.name,
  scheduled_at: `2026-11-21T${String(9 + position).padStart(2, "0")}:00:00-05:00`,
  court,
  duration_minutes: 30,
  status: "scheduled" as const,
  home_score: null,
  away_score: null,
  home_penalties: null,
  away_penalties: null,
  winner_id: null,
  decision: null,
  elapsed_seconds: 0,
  running: false,
  segment: "regular",
  live_points: { home: 0, away: 0 },
});

const TORNEO = {
  ready: true,
  competition_id: "competition-1",
  competition_name: "Fútbol Senior",
  competitions: [
    {
      id: "competition-1",
      name: "Fútbol Senior",
      discipline: "Fútbol",
      category: "Senior",
      date: "2026-11-21",
    },
  ],
  tournament: "Salesianos FEST 2026",
  discipline: "Fútbol",
  category: "Senior",
  date: "2026-11-21",
  server_time: "2026-11-21T09:00:00-05:00",
  groups: [
    {
      id: "A",
      label: "Grupo A",
      revision: 3,
      teams: [teamA, teamB],
      table: [],
      matches: [match("match-a", "A", 0), match("match-b", "B", 1)],
    },
  ],
  knockout: [],
  teams: [teamA, teamB],
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.guardarGrupo.mockResolvedValue({});
});

describe("administración del torneo por canchas", () => {
  it("agrupa los partidos y permite mostrar una sola cancha", () => {
    render(<TorneoAdminRuta />);

    fireEvent.click(screen.getByRole("button", { name: "Por canchas" }));

    expect(screen.getByRole("heading", { name: "Cancha A" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Cancha B" })).toBeVisible();

    fireEvent.change(screen.getByLabelText("Filtrar por cancha"), {
      target: { value: "B" },
    });

    expect(
      screen.queryByRole("heading", { name: "Cancha A" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cancha B" })).toBeVisible();
    expect(screen.getAllByLabelText("CANCHA")).toHaveLength(1);
    expect(screen.getByLabelText("CANCHA")).toHaveValue("B");
  });

  it("guarda el grupo completo aunque la vista filtre una cancha", () => {
    render(<TorneoAdminRuta />);
    fireEvent.click(screen.getByRole("button", { name: "Por canchas" }));
    fireEvent.change(screen.getByLabelText("Filtrar por cancha"), {
      target: { value: "A" },
    });

    const article = screen.getByText("PARTIDO 1").closest("article");
    expect(article).not.toBeNull();
    fireEvent.change(
      within(article as HTMLElement).getByLabelText("Marcador local"),
      {
        target: { value: "3" },
      },
    );
    fireEvent.click(
      within(article as HTMLElement).getByRole("button", {
        name: "Guardar partido",
      }),
    );

    expect(mocks.guardarGrupo).toHaveBeenCalledWith({
      id: "A",
      data: {
        revision: 3,
        matches: [
          expect.objectContaining({ id: "match-a", home_score: 3 }),
          expect.objectContaining({ id: "match-b", court: "B" }),
        ],
      },
    });
  });
});
