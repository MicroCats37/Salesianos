// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CompetenciaEquipoAltaEditor,
  CompetenciaEquipoEdicionEditor,
} from "./CompetenciaEquipoEditor";

/**
 * The editors of the teams of a competition.
 *
 * The suite verifies the CONTRACT of the editor: the exact payload that
 * travels to the API (the manual order, the audited motive and the
 * optimistic lock), the validation of Zod and the rendering of a failure.
 */

const { crearEquipoCompetencia, actualizarEquipoCompetencia } = vi.hoisted(
  () => ({
    crearEquipoCompetencia: vi.fn(),
    actualizarEquipoCompetencia: vi.fn(),
  }),
);

vi.mock("../../services/competencias.comandos.service", () => ({
  crearEquipoCompetencia,
  actualizarEquipoCompetencia,
  actualizarParticipantesEncuentro: vi.fn(),
  actualizarRondaCompetencia: vi.fn(),
  confirmarAvance: vi.fn(),
  confirmarCorreccion: vi.fn(),
  configurarByeEncuentro: vi.fn(),
  crearEncuentroCompetencia: vi.fn(),
  crearRondaCompetencia: vi.fn(),
  desenlazarEncuentro: vi.fn(),
  enlazarEncuentro: vi.fn(),
  previsualizarAvance: vi.fn(),
  previsualizarCorreccion: vi.fn(),
  programarEncuentro: vi.fn(),
  registrarResultadoEncuentro: vi.fn(),
}));

const COMPETENCIA_ID = "11111111-1111-4111-8111-111111111111";
const EQUIPO_ID = "22222222-2222-4222-8222-222222222222";

const EQUIPO = {
  id: "33333333-3333-4333-8333-333333333333",
  competencia_id: COMPETENCIA_ID,
  equipo_id: EQUIPO_ID,
  equipo_nombre: "Los Halcones",
  orden: 2,
  estado: "ACTIVO",
  version: 7,
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

describe("CompetenciaEquipoAltaEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("manda el equipo con el ORDEN MANUAL y sin versión", async () => {
    const usuario = userEvent.setup();
    crearEquipoCompetencia.mockResolvedValue({
      success: true,
      data: EQUIPO,
      error: null,
      message: null,
    });

    renderizar(<CompetenciaEquipoAltaEditor competenciaId={COMPETENCIA_ID} />);

    await usuario.type(
      screen.getByLabelText(/Identificador del equipo/),
      EQUIPO_ID,
    );
    await usuario.type(screen.getByLabelText(/Orden en el cuadro/), "3");
    await usuario.click(
      screen.getByRole("button", { name: "Incorporar equipo" }),
    );

    await waitFor(() => {
      expect(crearEquipoCompetencia).toHaveBeenCalledTimes(1);
    });
    expect(crearEquipoCompetencia).toHaveBeenCalledWith(COMPETENCIA_ID, {
      equipo_id: EQUIPO_ID,
      orden: 3,
    });
  });

  it("NO manda nada cuando el orden está vacío", async () => {
    const usuario = userEvent.setup();

    renderizar(<CompetenciaEquipoAltaEditor competenciaId={COMPETENCIA_ID} />);

    await usuario.type(
      screen.getByLabelText(/Identificador del equipo/),
      EQUIPO_ID,
    );
    await usuario.click(
      screen.getByRole("button", { name: "Incorporar equipo" }),
    );

    expect(await screen.findByText("Indica el orden.")).toBeInTheDocument();
    expect(crearEquipoCompetencia).not.toHaveBeenCalled();
  });
});

describe("CompetenciaEquipoEdicionEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("manda el motivo y la VERSIÓN QUE EL SERVIDOR DEVUELVE", async () => {
    const usuario = userEvent.setup();
    actualizarEquipoCompetencia.mockResolvedValue({
      success: true,
      data: EQUIPO,
      error: null,
      message: null,
    });

    renderizar(
      <CompetenciaEquipoEdicionEditor
        competenciaId={COMPETENCIA_ID}
        equipo={EQUIPO}
      />,
    );

    const orden = screen.getByLabelText(/Orden en el cuadro/);
    await usuario.clear(orden);
    await usuario.type(orden, "5");
    await usuario.type(
      screen.getByLabelText(/Motivo del cambio/),
      "Reordeno el cuadro por decisión del-php",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Guardar cambios" }),
    );

    await waitFor(() => {
      expect(actualizarEquipoCompetencia).toHaveBeenCalledTimes(1);
    });
    expect(actualizarEquipoCompetencia).toHaveBeenCalledWith(
      COMPETENCIA_ID,
      EQUIPO.id,
      {
        orden: 5,
        estado: "ACTIVO",
        motivo: "Reordeno el cuadro por decisión del-php",
        expected_version: 7,
      },
    );
  });

  it("exige el motivo AUDITADO antes de enviar", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <CompetenciaEquipoEdicionEditor
        competenciaId={COMPETENCIA_ID}
        equipo={EQUIPO}
      />,
    );

    await usuario.click(
      screen.getByRole("button", { name: "Guardar cambios" }),
    );

    expect(
      await screen.findByText("Explica el motivo (mínimo 5 caracteres)."),
    ).toBeInTheDocument();
    expect(actualizarEquipoCompetencia).not.toHaveBeenCalled();
  });
});
