// @vitest-environment jsdom

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  partidoTorneoSchema,
  torneoPublicoSchema,
} from "../schemas/torneo-publico.schema";
import { EncuentrosPublicosView } from "../views/EncuentrosPublicosView";

const match = {
  id: "P-081",
  group_id: null,
  stage: "cross" as const,
  category: "Master",
  title: "1° Master A vs 2° Master B",
  position: 0,
  home_id: null,
  away_id: null,
  home_name: "1° Master A",
  away_name: "2° Master B",
  scheduled_at: "2026-11-21T16:00:00-05:00",
  court: "A",
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
};

describe("fixture público normalizado", () => {
  it("acepta cruces y terceros puestos sin exigir equipos resueltos", () => {
    expect(partidoTorneoSchema.parse(match).stage).toBe("cross");
    expect(
      partidoTorneoSchema.parse({
        ...match,
        id: "P-098",
        stage: "third_place",
        title: "3er puesto Master",
      }).stage,
    ).toBe("third_place");
  });

  it("renderiza las etiquetas clasificatorias declaradas por el backend", () => {
    const data = torneoPublicoSchema.parse({
      ready: true,
      competition_id: "competition-1",
      competition_name: "Fútbol 7 Masculino Interpromociones",
      competitions: [
        {
          id: "competition-1",
          name: "Fútbol 7 Masculino Interpromociones",
          discipline: "Fútbol",
          category: "Interpromociones",
          date: "2026-11-21",
        },
      ],
      tournament: "Salesianos FEST 2026",
      discipline: "Fútbol",
      category: "Interpromociones",
      date: "2026-11-21",
      server_time: "2026-11-21T09:00:00-05:00",
      groups: [
        {
          id: "A",
          label: "Senior A",
          revision: 0,
          teams: [],
          table: [],
          matches: [],
        },
      ],
      knockout: [
        match,
        {
          ...match,
          id: "P-098",
          stage: "third_place",
          category: "Master",
          title: "3er puesto Master",
          home_name: "Por definir",
          away_name: "Por definir",
        },
      ],
      teams: [],
    });

    render(<EncuentrosPublicosView estado="listo" encuentros={data} />);
    fireEvent.click(screen.getByRole("button", { name: "Llaves" }));

    expect(screen.getByText("1° Master A")).toBeInTheDocument();
    expect(screen.getByText("2° Master B")).toBeInTheDocument();
    expect(screen.getByText("3er puesto Master")).toBeInTheDocument();
    expect(screen.getByText("Tercer puesto")).toBeInTheDocument();
  });
});
