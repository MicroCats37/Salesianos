// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CompetenciaByeEditor,
  CompetenciaEncuentroParticipantesEditor,
  CompetenciaEnlaceEditor,
  CompetenciaProgramacionEditor,
} from "./index";

/**
 * The editors of ONE encounter: the schedule, the MANUAL bye, the link and
 * the participants.
 *
 * The suite verifies the contract of every payload (the optimistic lock and
 * the audited motive) and the two promises of the interface: it is
 * RESPONSIVE (one column on mobile, twelve on desktop) and it is
 * ACCESSIBLE (every field has its label).
 */

const {
  configurarByeEncuentro,
  actualizarParticipantesEncuentro,
  enlazarEncuentro,
  programarEncuentro,
} = vi.hoisted(() => ({
  configurarByeEncuentro: vi.fn(),
  actualizarParticipantesEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  programarEncuentro: vi.fn(),
}));

vi.mock("../../services/competencias.comandos.service", () => ({
  actualizarEquipoCompetencia: vi.fn(),
  actualizarParticipantesEncuentro,
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance: vi.fn(),
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro,
  crearEncuentroCompetencia: vi.fn(),
  crearEquipoCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro,
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion: vi.fn(),
  programarEncuentro,
  registrarResultadoEncuentro: vi.fn(),
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const ENCUENTRO_ID = "22222222-2222-4222-8222-222222222222";
const PARTICIPANTE_1 = "33333333-3333-4333-8333-333333333333";
const SIGUIENTE_ID = "44444444-4444-4444-8444-444444444444";

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
  participante_2_id: null,
  participante_2_nombre: null,
  inicio_programado: null,
  fin_programado: null,
  estado: "BORRADOR",
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
  version: 2,
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

describe("CompetenciaProgramacionEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    programarEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("compone el horario con la fecha de la competencia", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaProgramacionEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
        fechaCompetencia="2026-10-25"
      />,
    );

    await usuario.type(screen.getByLabelText(/Hora de inicio/), "10:00");
    await usuario.type(screen.getByLabelText(/Hora de fin/), "10:45");
    await usuario.type(
      screen.getByLabelText(/Motivo del cambio/),
      "Programacion del encuentro del cuadro",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Programar encuentro" }),
    );

    await waitFor(() => {
      expect(programarEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(programarEncuentro).toHaveBeenCalledWith(ENCUENTRO_ID, {
      inicio_programado: "2026-10-25T10:00:00",
      fin_programado: "2026-10-25T10:45:00",
      motivo: "Programacion del encuentro del cuadro",
      expected_version: 2,
    });
  });

  it("rechaza una hora que no existe", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaProgramacionEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
        fechaCompetencia="2026-10-25"
      />,
    );

    await usuario.type(screen.getByLabelText(/Hora de inicio/), "25:00");
    await usuario.click(
      screen.getByRole("button", { name: "Programar encuentro" }),
    );

    // Las dos horas se avisan: el inicio es inválido y el final está vacío.
    expect(
      await screen.findAllByText("Indica la hora como HH:mm."),
    ).toHaveLength(2);
    expect(programarEncuentro).not.toHaveBeenCalled();
  });

  it("es RESPONSIVE: una columna en móvil y doce en escritorio", () => {
    renderizar(
      <CompetenciaProgramacionEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
        fechaCompetencia="2026-10-25"
      />,
    );

    const grilla = document.querySelector(".grid.grid-cols-1");
    expect(grilla).not.toBeNull();
    expect(grilla?.className).toContain("md:grid-cols-12");
  });
});

describe("CompetenciaByeEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    configurarByeEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("configura el bye MANUAL con su motivo y sin participantes", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaByeEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await usuario.type(
      screen.getByLabelText(/Motivo del bye/),
      "Bye manual por decision del arbitro",
    );
    await usuario.click(screen.getByRole("button", { name: "Configurar bye" }));

    await waitFor(() => {
      expect(configurarByeEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(configurarByeEncuentro).toHaveBeenCalledWith(ENCUENTRO_ID, {
      motivo: "Bye manual por decision del arbitro",
      expected_version: 2,
    });
  });

  it("EXIGE el motivo auditado", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaByeEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await usuario.click(screen.getByRole("button", { name: "Configurar bye" }));

    expect(
      await screen.findByText("Explica el motivo (mínimo 5 caracteres)."),
    ).toBeInTheDocument();
    expect(configurarByeEncuentro).not.toHaveBeenCalled();
  });
});

describe("CompetenciaEnlaceEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    enlazarEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("enlaza con el destino, su slot y el motivo AUDITADO", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaEnlaceEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await usuario.type(
      screen.getByLabelText(/Encuentro destino/),
      SIGUIENTE_ID,
    );
    await usuario.click(screen.getByRole("combobox"));
    await usuario.click(
      await screen.findByRole("option", { name: "Participante 2" }),
    );
    await usuario.type(
      screen.getByLabelText(/Motivo del enlace/),
      "Vinculacion del encuentro con la siguiente ronda",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Enlazar encuentro" }),
    );

    await waitFor(() => {
      expect(enlazarEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(enlazarEncuentro).toHaveBeenCalledWith(ENCUENTRO_ID, {
      siguiente_encuentro_id: SIGUIENTE_ID,
      slot_destino: "PARTICIPANTE_2",
      motivo: "Vinculacion del encuentro con la siguiente ronda",
      expected_version: 2,
    });
  });
});

describe("CompetenciaEncuentroParticipantesEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    actualizarParticipantesEncuentro.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("mueve los slots con su motivo y la versión del servidor", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaEncuentroParticipantesEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    await usuario.type(
      screen.getByLabelText(/Motivo del cambio/),
      "Asignacion de los participantes del encuentro",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Guardar participantes" }),
    );

    await waitFor(() => {
      expect(actualizarParticipantesEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(actualizarParticipantesEncuentro).toHaveBeenCalledWith(
      ENCUENTRO_ID,
      {
        participante_1_id: PARTICIPANTE_1,
        participante_2_id: null,
        motivo: "Asignacion de los participantes del encuentro",
        expected_version: 2,
      },
    );
  });

  it("deja el slot VACÍO cuando el campo está en blanco", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaEncuentroParticipantesEditor
        competenciaId={COMPETENCIA_ID}
        encuentro={ENCUENTRO}
      />,
    );

    const primerSlot = screen.getByLabelText(/Participante 1/);
    await usuario.clear(primerSlot);
    await usuario.type(
      screen.getByLabelText(/Motivo del cambio/),
      "Asignacion de los participantes del encuentro",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Guardar participantes" }),
    );

    await waitFor(() => {
      expect(actualizarParticipantesEncuentro).toHaveBeenCalledTimes(1);
    });
    expect(actualizarParticipantesEncuentro).toHaveBeenCalledWith(
      ENCUENTRO_ID,
      expect.objectContaining({ participante_1_id: null }),
    );
  });
});
