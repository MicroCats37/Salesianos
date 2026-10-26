// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CompetenciaRondaAltaEditor,
  CompetenciaRondaEdicionEditor,
} from "./CompetenciaRondaEditor";

/**
 * The editors of the ROUNDS of a competition.
 *
 * The suite verifies the contract of every payload: the label and the order
 * are MANUAL and the edition travels with the optimistic lock.
 */

const { crearRondaCompetencia, actualizarRondaCompetencia } = vi.hoisted(
  () => ({
    crearRondaCompetencia: vi.fn(),
    actualizarRondaCompetencia: vi.fn(),
  }),
);

vi.mock("../../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia,
  confirmarAvance: vi.fn(),
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia,
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion: vi.fn(),
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro: vi.fn(),
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";

const RONDA = {
  id: "22222222-2222-4222-8222-222222222222",
  competencia_id: COMPETENCIA_ID,
  etiqueta: "Octavos de final",
  orden: 1,
  estado: "ACTIVA",
  version: 5,
  total_encuentros: 4,
};

function renderizar(ui: ReactElement) {
  const cliente = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={cliente}>{ui}</QueryClientProvider>,
  );
}

describe("Los editores de las rondas", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    crearRondaCompetencia.mockResolvedValue({
      success: true,
      data: RONDA,
      error: null,
      message: null,
    });
    actualizarRondaCompetencia.mockResolvedValue({
      success: true,
      data: RONDA,
      error: null,
      message: null,
    });
  });

  it("registra una ronda con su etiqueta y su orden", async () => {
    const usuario = userEvent.setup();

    renderizar(<CompetenciaRondaAltaEditor competenciaId={COMPETENCIA_ID} />);

    await usuario.type(
      screen.getByLabelText(/Etiqueta de la ronda/),
      "Cuartos de final",
    );
    await usuario.type(screen.getByLabelText(/Orden de la ronda/), "2");
    await usuario.click(
      screen.getByRole("button", { name: "Registrar ronda" }),
    );

    await waitFor(() => {
      expect(crearRondaCompetencia).toHaveBeenCalledTimes(1);
    });
    expect(crearRondaCompetencia).toHaveBeenCalledWith(COMPETENCIA_ID, {
      etiqueta: "Cuartos de final",
      orden: 2,
    });
  });

  it("edita una ronda con la versión que el servidor devolvió", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaRondaEdicionEditor
        competenciaId={COMPETENCIA_ID}
        ronda={RONDA}
      />,
    );

    const etiqueta = screen.getByLabelText(/Etiqueta de la ronda/);
    await usuario.clear(etiqueta);
    await usuario.type(etiqueta, "Dieciseisavos");
    await usuario.click(
      screen.getByRole("button", { name: "Guardar cambios" }),
    );

    await waitFor(() => {
      expect(actualizarRondaCompetencia).toHaveBeenCalledTimes(1);
    });
    expect(actualizarRondaCompetencia).toHaveBeenCalledWith(
      COMPETENCIA_ID,
      RONDA.id,
      {
        etiqueta: "Dieciseisavos",
        orden: 1,
        motivo: null,
        expected_version: 5,
      },
    );
  });

  it("acepta una ronda SIN motivo: la ronda no es un movimiento auditado", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaRondaEdicionEditor
        competenciaId={COMPETENCIA_ID}
        ronda={RONDA}
      />,
    );

    await usuario.click(
      screen.getByRole("button", { name: "Guardar cambios" }),
    );

    await waitFor(() => {
      expect(actualizarRondaCompetencia).toHaveBeenCalledTimes(1);
    });
    expect(actualizarRondaCompetencia).toHaveBeenCalledWith(
      COMPETENCIA_ID,
      RONDA.id,
      expect.objectContaining({ motivo: null }),
    );
  });
});
