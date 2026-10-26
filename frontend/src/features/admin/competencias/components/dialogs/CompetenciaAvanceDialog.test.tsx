// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CompetenciaAvanceDialog } from "./CompetenciaAvanceDialog";

/**
 * The dialog of the ADVANCE of the winner.
 *
 * The suite verifies the contract of the flow: the proposal NEVER writes,
 * the blocked destination blocks the confirmation, the confirmation travels
 * with the audited motive and the optimistic lock, and a conflict is
 * rendered with its retry.
 */

const { previsualizarAvance, confirmarAvance } = vi.hoisted(() => ({
  previsualizarAvance: vi.fn(),
  confirmarAvance: vi.fn(),
}));

vi.mock("../../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance,
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance,
  previsualizarCorreccion: vi.fn(),
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro: vi.fn(),
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const SIGUIENTE_ID = "33333333-3333-4333-8333-333333333333";
const GANADOR_ID = "44444444-4444-4444-8444-444444444444";

const ENCUENTRO = {
  id: ENCUENTRO_ID,
  ronda_id: "55555555-5555-4555-8555-555555555555",
  ronda_etiqueta: "Cuartos de final",
  ronda_orden: 1,
  competencia_id: COMPETENCIA_ID,
  competencia_nombre: "Fútbol",
  orden: 1,
  participante_1_id: GANADOR_ID,
  participante_1_nombre: "Los Halcones",
  participante_2_id: null,
  participante_2_nombre: null,
  inicio_programado: null,
  fin_programado: null,
  estado: "BORRADOR",
  estado_pre_suspension: null,
  iniciado_en: null,
  finalizado_en: null,
  es_bye: false,
  ganador_id: GANADOR_ID,
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: null,
  siguiente_encuentro_id: SIGUIENTE_ID,
  slot_destino: "PARTICIPANTE_1",
  ganador_propagado_id: null,
  version: 6,
};

function propuesta(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    data: {
      encuentro_id: ENCUENTRO_ID,
      siguiente_encuentro_id: SIGUIENTE_ID,
      slot_destino: "PARTICIPANTE_1",
      ganador_id: GANADOR_ID,
      ocupante_actual_id: null,
      ya_propagado: false,
      bloqueado: false,
      motivo_bloqueo: null,
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

describe("CompetenciaAvanceDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    previsualizarAvance.mockResolvedValue(propuesta());
    confirmarAvance.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("expone la propuesta y NUNCA escribe al previsualizar", async () => {
    renderizar(
      <CompetenciaAvanceDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    expect(
      await screen.findByLabelText("Propuesta del avance"),
    ).toBeInTheDocument();
    expect(await screen.findByText(SIGUIENTE_ID)).toBeTruthy();
    expect(confirmarAvance).not.toHaveBeenCalled();
  });

  it("es un diálogo ACCESIBLE con su título", async () => {
    renderizar(
      <CompetenciaAvanceDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    const dialogo = await screen.findByRole("dialog");
    expect(dialogo).toHaveAccessibleName("Propagar el ganador");
  });

  it("confirma con el motivo AUDITADO y la versión del servidor", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaAvanceDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(
      screen.getByLabelText(/Motivo de la propagación/),
      "Propagacion del ganador al encuentro enlazado",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Confirmar avance" }),
    );

    await waitFor(() => {
      expect(confirmarAvance).toHaveBeenCalledTimes(1);
    });
    expect(confirmarAvance).toHaveBeenCalledWith(ENCUENTRO_ID, {
      motivo: "Propagacion del ganador al encuentro enlazado",
      expected_version: 6,
    });
  });

  it("BLOQUEA la confirmación cuando el destino está bloqueado", async () => {
    previsualizarAvance.mockResolvedValue(
      propuesta({
        bloqueado: true,
        motivo_bloqueo: "El encuentro destino ya comenzó.",
      }),
    );

    renderizar(
      <CompetenciaAvanceDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    expect(
      await screen.findByText(/El encuentro destino ya comenzó/),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Confirmar avance" }),
    ).toBeDisabled();
    expect(confirmarAvance).not.toHaveBeenCalled();
  });

  it("renderiza el CONFLICTO con su reintento", async () => {
    const usuario = userEvent.setup();
    const { ApiQueryError } = await import("@/hooks/callsApi/useApiQuery");

    confirmarAvance.mockRejectedValue(
      new ApiQueryError("El recurso cambió mientras lo editabas.", 409),
    );

    renderizar(
      <CompetenciaAvanceDialog
        open
        onOpenChange={() => {}}
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(
      screen.getByLabelText(/Motivo de la propagación/),
      "Propagacion del ganador al encuentro enlazado",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Confirmar avance" }),
    );

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("El recurso cambió mientras lo editabas.");
    expect(alerta).toHaveTextContent("Otro administrador cambió este recurso.");
    expect(
      screen.getByRole("button", { name: "Reintentar" }),
    ).toBeInTheDocument();
  });
});
