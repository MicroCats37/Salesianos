// @vitest-environment jsdom

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorAdmin } from "@/features/admin/operaciones/services/admin.service";
import {
  useEmitirCredencial,
  useOtorgarCortesia,
} from "../hooks/useAdminPases";
import {
  emitirCredencial,
  otorgarCortesia,
} from "../services/admin.pase.service";

vi.mock("../services/admin.pase.service", () => ({
  emitirCredencial: vi.fn(),
  listarCortesias: vi.fn(),
  otorgarCortesia: vi.fn(),
  revocarCortesia: vi.fn(),
  rutaCortesias: () => "/administracion/pases/cortesias",
  rutaEmitirCredencial: () => "/validaciones/tickets",
  rutaRevocarCortesia: (cortesiaId: string) =>
    `/administracion/pases/cortesias/${cortesiaId}/revocar`,
}));

const otorgarMock = vi.mocked(otorgarCortesia);
const emitirMock = vi.mocked(emitirCredencial);

/** The command of the grant of a courtesy. */
const COMANDO = {
  edicion_id: "edicion-1",
  pase_id: "pase-1",
  tipo_documento: "DNI",
  numero_documento: "77777777",
  nombres: "Rosa",
  apellidos: "Díaz",
  motivo: "Cortesía de la organización.",
};

/** The answer of the grant of a courtesy. */
const CORTESIA = {
  id: "cortesia-1",
  derecho_id: "derecho-1",
  edicion_id: "edicion-1",
  edicion_nombre: "EDICION DE EJEMPLO",
  pase_id: "pase-1",
  pase_nombre: "Pase FEST",
  persona_id: "persona-1",
  persona_nombres: "Rosa Díaz",
  persona_tipo_documento: "DNI",
  persona_numero_documento: "77777777",
  estado: "ACTIVA",
  motivo: "Cortesía de la organización.",
  actor_usuario_id: null,
  actor_nombres: "Administrador",
  concedido_en: "2026-11-20T10:00:00Z",
  revocado_en: null,
};

/** The answer of the issue of the credential. */
const CREDENCIAL = {
  ticket_id: "ticket-1",
  codigo: "FEST-secreto-de-ejemplo",
  tipo_derecho: "ENTRADA_CORTESIA",
  operacion: "INGRESO",
  edicion_id: "edicion-1",
  emitido_en: "2026-11-21T10:00:00Z",
};

/** A client of queries WITHOUT retries: a failure is a failure. */
function clienteDePrueba(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

/** The harness of the grant of a courtesy. */
function HarnessOtorgar({
  onResultado,
}: {
  onResultado: (resultado: unknown, error: unknown) => void;
}) {
  const otorgar = useOtorgarCortesia();

  return (
    <button
      type="button"
      onClick={() => {
        void otorgar.mutateAsync(COMANDO).then(
          (resultado) => onResultado(resultado, null),
          (error: unknown) => onResultado(null, error),
        );
      }}
    >
      otorgar
    </button>
  );
}

/** The harness of the issue of the credential. */
function HarnessCredencial() {
  const emision = useEmitirCredencial();

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          void emision.emitir("derecho-1");
        }}
      >
        emitir
      </button>
      <button type="button" onClick={emision.descartar}>
        descartar
      </button>
      <output data-testid="codigo">{emision.credencial?.codigo ?? ""}</output>
    </div>
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  // El adaptador de avisos escribe en la consola: el ruido no es información.
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

describe("ADP — el otorgamiento de una cortesía", () => {
  it("invalida EXACTAMENTE el namespace de las cortesías", async () => {
    const queryClient = clienteDePrueba();
    const invalidaciones = vi.spyOn(queryClient, "invalidateQueries");
    otorgarMock.mockResolvedValue(CORTESIA);

    let resultado: unknown = null;
    render(
      <QueryClientProvider client={queryClient}>
        <HarnessOtorgar
          onResultado={(valor) => {
            resultado = valor;
          }}
        />
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "otorgar" }));

    await waitFor(() => expect(resultado).not.toBeNull());
    expect(invalidaciones).toHaveBeenCalledWith({
      queryKey: ["admin", "pases", "cortesias"],
    });
  });

  it("un 409 llega al que la invocó con su estado y su código", async () => {
    const queryClient = clienteDePrueba();
    const duplicado = new ErrorAdmin(
      409,
      "PASE_DUPLICADO",
      "La persona ya tiene una entrada activa de este pase en esta edición.",
    );
    otorgarMock.mockRejectedValue(duplicado);

    let fallo: unknown = null;
    render(
      <QueryClientProvider client={queryClient}>
        <HarnessOtorgar
          onResultado={(_valor, error) => {
            fallo = error;
          }}
        />
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "otorgar" }));

    await waitFor(() => expect(fallo).not.toBeNull());
    expect(fallo).toBeInstanceOf(ErrorAdmin);
    expect((fallo as ErrorAdmin).status).toBe(409);
    expect((fallo as ErrorAdmin).codigo).toBe("PASE_DUPLICADO");
  });
});

describe("ADP — la credencial de la puerta es de una sola entrega", () => {
  it("el código NO entra en ninguna caché y se descarta al cerrar", async () => {
    const queryClient = clienteDePrueba();
    emitirMock.mockResolvedValue(CREDENCIAL);

    render(
      <QueryClientProvider client={queryClient}>
        <HarnessCredencial />
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "emitir" }));

    await waitFor(() =>
      expect(screen.getByTestId("codigo").textContent).toBe(
        "FEST-secreto-de-ejemplo",
      ),
    );

    // Ni la caché de consultas ni la de mutaciones guardan el secreto.
    const consultas = queryClient.getQueryCache().getAll();
    const mutaciones = queryClient.getMutationCache().getAll();
    expect(
      consultas.some((entrada) =>
        JSON.stringify(entrada.state.data ?? "").includes("FEST-secreto"),
      ),
    ).toBe(false);
    expect(
      mutaciones.some((entrada) =>
        JSON.stringify(entrada.state.data ?? "").includes("FEST-secreto"),
      ),
    ).toBe(false);

    await userEvent.click(screen.getByRole("button", { name: "descartar" }));

    expect(screen.getByTestId("codigo").textContent).toBe("");
  });

  it("el comando declara SOLO el derecho", async () => {
    const queryClient = clienteDePrueba();
    emitirMock.mockResolvedValue(CREDENCIAL);

    render(
      <QueryClientProvider client={queryClient}>
        <HarnessCredencial />
      </QueryClientProvider>,
    );

    await userEvent.click(screen.getByRole("button", { name: "emitir" }));

    await waitFor(() => expect(emitirMock).toHaveBeenCalledTimes(1));
    expect(emitirMock).toHaveBeenCalledWith({ derecho_id: "derecho-1" });
  });
});
