// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CompetenciaResultadoDialog } from "./CompetenciaResultadoDialog";

/**
 * The dialog of the RESULT of an encounter.
 *
 * The suite verifies the contract of the result: the winner is the only
 * authoritative datum, the scores are optional and the payload travels with
 * the audited motive and the optimistic lock.
 */

const { registrarResultadoEncuentro } = vi.hoisted(() => ({
  registrarResultadoEncuentro: vi.fn(),
}));

vi.mock("../../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance: vi.fn(),
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion: vi.fn(),
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro,
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const PARTICIPANTE_1 = "33333333-3333-4333-8333-333333333333";
const PARTICIPANTE_2 = "44444444-4444-4444-8444-444444444444";

const ENCUENTRO = {
  id: ENCUENTRO_ID,
  ronda_id: "55555555-5555-4555-8555-555555555555",
  ronda_etiqueta: "Final",
  ronda_orden: 4,
  competencia_id: COMPETENCIA_ID,
  competencia_nombre: "Fútbol",
  orden: 1,
  participante_1_id: PARTICIPANTE_1,
  participante_1_nombre: "Los Halcones",
  participante_2_id: PARTICIPANTE_2,
  participante_2_nombre: "Los Leones",
  inicio_programado: "2026-10-25T10:00:00",
  fin_programado: "2026-10-25T10:45:00",
  estado: "PROGRAMADO",
  estado_pre_suspension: null,
  iniciado_en: null,
  finalizado_en: null,
  es_bye: false,
  ganador_id: null,
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: null,
  siguiente_encuentro_id: null,
  slot_destino: null,
  ganador_propagado_id: null,
  version: 3,
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

describe("CompetenciaResultadoDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    registrarResultadoEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("es un diálogo ACCESIBLE con su título", async () => {
    renderizar(
      <CompetenciaResultadoDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    const dialogo = await screen.findByRole("dialog");
    expect(dialogo).toHaveAccessibleName("Registrar resultado");
  });

  it("ofrece SOLO los equipos que ocupan un slot como ganador", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaResultadoDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.click(screen.getByRole("combobox"));

    const opciones = await screen.findAllByRole("option");
    expect(opciones.map((opcion) => opcion.textContent)).toEqual([
      "Los Halcones",
      "Los Leones",
    ]);
  });

  it("manda el ganador, los puntajes opcionales y el motivo AUDITADO", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaResultadoDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByRole("dialog");

    await usuario.click(screen.getByRole("combobox"));
    await usuario.click(
      await screen.findByRole("option", { name: "Los Leones" }),
    );

    await usuario.type(
      screen.getByLabelText(/Puntaje del participante 1/),
      "3",
    );
    await usuario.type(
      screen.getByLabelText(/Puntaje del participante 2/),
      "1",
    );
    await usuario.type(
      screen.getByLabelText(/Detalle del marcador/),
      "3 sets a 2",
    );
    await usuario.type(
      screen.getByLabelText(/Motivo del registro/),
      "Registro del resultado del encuentro",
    );

    await usuario.click(
      screen.getByRole("button", { name: "Registrar resultado" }),
    );

    await waitFor(() => {
      expect(registrarResultadoEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(registrarResultadoEncuentro).toHaveBeenCalledWith(ENCUENTRO_ID, {
      ganador_id: PARTICIPANTE_2,
      puntaje_1: 3,
      puntaje_2: 1,
      marcador_detalle: "3 sets a 2",
      motivo: "Registro del resultado del encuentro",
      expected_version: 3,
    });
  });

  it("NO manda puntajes cuando el marcador está vacío", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaResultadoDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(
      screen.getByLabelText(/Motivo del registro/),
      "Registro del resultado del encuentro",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Registrar resultado" }),
    );

    await waitFor(() => {
      expect(registrarResultadoEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(registrarResultadoEncuentro).toHaveBeenCalledWith(
      ENCUENTRO_ID,
      expect.objectContaining({ puntaje_1: null, puntaje_2: null }),
    );
  });

  it("BLOQUEA el registro cuando el encuentro no tiene participantes", async () => {
    renderizar(
      <CompetenciaResultadoDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={{
          ...ENCUENTRO,
          participante_1_id: null,
          participante_1_nombre: null,
          participante_2_id: null,
          participante_2_nombre: null,
        }}
      />,
    );

    expect(
      await screen.findByText(/El encuentro no tiene participantes/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Registrar resultado" }),
    ).toBeDisabled();
  });
});
