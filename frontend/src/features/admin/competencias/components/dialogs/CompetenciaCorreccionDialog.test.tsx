// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CompetenciaCorreccionDialog } from "./CompetenciaCorreccionDialog";

/**
 * The dialog of the CORRECTION of the winner.
 *
 * The suite verifies the contract of the OVERRIDE: the impact over every
 * descendant is EXPOSED before the confirmation, the acceptance is EXPLICIT
 * (the confirmation stays disabled without it) and the payload travels with
 * `override`, `acepta_impacto`, the audited motive and the optimistic lock.
 */

const { previsualizarCorreccion, confirmarCorreccion } = vi.hoisted(() => ({
  previsualizarCorreccion: vi.fn(),
  confirmarCorreccion: vi.fn(),
}));

vi.mock("../../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance: vi.fn(),
  confirmarCorreccion,
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion,
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro: vi.fn(),
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const GANADOR_ACTUAL = "33333333-3333-4333-8333-333333333333";
const GANADOR_NUEVO = "44444444-4444-4444-8444-444444444444";
const DESCENDIENTE_ID = "55555555-5555-4555-8555-555555555555";

const ENCUENTRO = {
  id: ENCUENTRO_ID,
  ronda_id: "66666666-6666-4666-8666-666666666666",
  ronda_etiqueta: "Semifinal",
  ronda_orden: 3,
  competencia_id: COMPETENCIA_ID,
  competencia_nombre: "Fútbol",
  orden: 1,
  participante_1_id: GANADOR_ACTUAL,
  participante_1_nombre: "Los Halcones",
  participante_2_id: GANADOR_NUEVO,
  participante_2_nombre: "Los Leones",
  inicio_programado: null,
  fin_programado: null,
  estado: "FINALIZADO",
  estado_pre_suspension: null,
  iniciado_en: null,
  finalizado_en: null,
  es_bye: false,
  ganador_id: GANADOR_ACTUAL,
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: null,
  siguiente_encuentro_id: DESCENDIENTE_ID,
  slot_destino: "PARTICIPANTE_1",
  ganador_propagado_id: GANADOR_ACTUAL,
  version: 8,
};

function impacto(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    data: {
      encuentro_id: ENCUENTRO_ID,
      ganador_actual_id: GANADOR_ACTUAL,
      ganador_nuevo_id: GANADOR_NUEVO,
      requiere_override: true,
      descendientes: [
        {
          encuentro_id: DESCENDIENTE_ID,
          slot: "PARTICIPANTE_1",
          estado: "EN_CURSO",
          ocupante_actual_id: GANADOR_ACTUAL,
          ganador_propagado_id: GANADOR_ACTUAL,
          bloqueado: true,
          motivo_bloqueo: "El encuentro dependiente ya comenzó.",
          se_reemplaza: true,
          se_limpia_resultado: true,
        },
      ],
      ...overrides,
    },
    error: null,
    message: null,
  };
}

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

describe("CompetenciaCorreccionDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    previsualizarCorreccion.mockResolvedValue(impacto());
    confirmarCorreccion.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("previsualiza con el ganador propuesto y NUNCA escribe", async () => {
    renderizar(
      <CompetenciaCorreccionDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await waitFor(() => {
      expect(previsualizarCorreccion).toHaveBeenCalledWith(ENCUENTRO_ID, {
        ganador_id: GANADOR_NUEVO,
      });
    });
    expect(confirmarCorreccion).not.toHaveBeenCalled();
  });

  it("EXPONE el impacto sobre cada dependiente", async () => {
    renderizar(
      <CompetenciaCorreccionDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    const seccion = await screen.findByLabelText("Impacto de la corrección");
    expect(seccion).toHaveTextContent(DESCENDIENTE_ID);
    expect(seccion).toHaveTextContent("El encuentro dependiente ya comenzó.");
    expect(seccion).toHaveTextContent("Su resultado se limpia.");
  });

  it("EXIGE la aceptación explícita del impacto", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaCorreccionDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByLabelText("Impacto de la corrección");

    const confirmar = screen.getByRole("button", {
      name: "Confirmar corrección",
    });
    expect(confirmar).toBeDisabled();

    await usuario.click(
      screen.getByRole("checkbox", { name: /Acepto el impacto/ }),
    );

    await waitFor(() => {
      expect(confirmar).not.toBeDisabled();
    });
  });

  it("manda el override con el motivo y la versión del servidor", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaCorreccionDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByLabelText("Impacto de la corrección");

    await usuario.type(
      screen.getByLabelText(/Motivo de la corrección/),
      "Correccion administrativa del ganador del encuentro",
    );
    await usuario.click(
      screen.getByRole("checkbox", { name: /Acepto el impacto/ }),
    );
    await usuario.click(
      screen.getByRole("button", { name: "Confirmar corrección" }),
    );

    await waitFor(() => {
      expect(confirmarCorreccion).toHaveBeenCalledTimes(1);
    });
    expect(confirmarCorreccion).toHaveBeenCalledWith(ENCUENTRO_ID, {
      ganador_id: GANADOR_NUEVO,
      motivo: "Correccion administrativa del ganador del encuentro",
      override: true,
      acepta_impacto: true,
      expected_version: 8,
    });
  });

  it("NO manda override cuando el impacto NO fue aceptado", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaCorreccionDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByLabelText("Impacto de la corrección");

    await usuario.type(
      screen.getByLabelText(/Motivo de la corrección/),
      "Correccion administrativa del ganador del encuentro",
    );

    const confirmar = screen.getByRole("button", {
      name: "Confirmar corrección",
    });
    expect(confirmar).toBeDisabled();
    expect(confirmarCorreccion).not.toHaveBeenCalled();
  });
});
