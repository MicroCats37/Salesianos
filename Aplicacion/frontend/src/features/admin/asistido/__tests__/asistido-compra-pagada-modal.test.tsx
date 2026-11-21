// @vitest-environment jsdom

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorAdmin } from "@/features/admin/operaciones/services/admin.service";
import { ModalCompraParaCliente } from "../components/ModalCompraParaCliente";
import { useCotizacionPase } from "../hooks/useCotizacionPase";

/**
 * The PAID purchase of a pass, on the screen.
 *
 * The suite freezes the FOUR behaviours that the form owes to the operator:
 *
 * 1. it shows the price of the SERVER (quantity, unit price, total and
 *    currency) and it NEVER computes one;
 * 2. it asks for a NEW quotation when the quantity changes, and an answer
 *    that belongs to an older quantity never wins;
 * 3. the `409` of the moved price asks for a new quotation instead of
 *    retrying blindly, and the `422` puts the error of each field on the
 *    control that owns it;
 * 4. the command invalidates EXACTLY the payments of the area and the
 *    purchases of the passes.
 */

const { cotizarMock, comprarMock, comprarPedidoMock, resolverMock } =
  vi.hoisted(() => ({
    cotizarMock: vi.fn(),
    comprarMock: vi.fn(),
    comprarPedidoMock: vi.fn(),
    resolverMock: vi.fn(),
  }));

vi.mock("../services/asistido.service", () => ({
  agregarParticipanteEquipo: vi.fn(),
  comprarPaseCliente: comprarMock,
  comprarPedidoCliente: comprarPedidoMock,
  cotizarPaseCliente: cotizarMock,
}));

vi.mock("@/features/auth/hooks", () => ({
  useResolverPersona: () => ({
    mutateAsync: resolverMock,
    isPending: false,
  }),
}));

/** The quotation of ONE quantity. */
function cotizacion(cantidad: number, total: string) {
  return {
    pase_id: "pase-1",
    edicion_id: "edicion-1",
    pase_nombre: "Pase FEST",
    cantidad,
    precio_unitario: "35.00",
    total,
    moneda: "PEN",
    version: `version-${cantidad}`,
    estado: "ACTIVA",
    validez_hasta: "2026-11-21T23:00:00Z",
  };
}

/** The purchase the server registers. */
const COMPRA = {
  compra_id: "compra-1",
  recurso_id: "recurso-1",
  orden_pago_id: "orden-1",
  tipo: "PASE",
  concepto: "Pase FEST",
  total: "70.00",
  moneda: "PEN",
  estado: "PAGADA",
  estado_pago: "MANUAL",
  comprador_persona_id: "persona-cliente",
  comprador_nombre: "Rosa Díaz",
  cantidad: 2,
  monto_declarado: null,
};

/** A promise whose answer the test decides. */
function diferido<T>() {
  let resolver!: (valor: T) => void;
  const promesa = new Promise<T>((resolve) => {
    resolver = resolve;
  });
  return { promesa, resolver };
}

function clienteConQuery(queryClient: QueryClient) {
  return function Envoltorio({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

beforeEach(() => {
  cotizarMock.mockReset();
  comprarMock.mockReset();
  comprarPedidoMock.mockReset();
  resolverMock.mockReset();

  cotizarMock.mockResolvedValue(cotizacion(1, "35.00"));
  comprarMock.mockResolvedValue(COMPRA);
  resolverMock.mockResolvedValue({
    origen: "LOCAL",
    persona_id: "persona-1",
    persistida: true,
    tipo_documento: "DNI",
    numero_documento: "77777777",
    nombres: "Rosa",
    apellidos: "Díaz",
  });
});

describe("ACP — la cotización viva del pase", () => {
  it("una respuesta VIEJA no puede escribir el estado de una cantidad nueva", async () => {
    const primera = diferido<ReturnType<typeof cotizacion>>();
    const segunda = diferido<ReturnType<typeof cotizacion>>();

    cotizarMock
      .mockImplementationOnce(() => primera.promesa)
      .mockImplementationOnce(() => segunda.promesa);

    const { result } = renderHook(() => useCotizacionPase());

    act(() => {
      result.current.cotizar("pase-1", 1);
    });

    await waitFor(() => {
      expect(cotizarMock).toHaveBeenCalledTimes(1);
    });

    act(() => {
      result.current.invalidar();
      result.current.cotizar("pase-1", 2);
    });

    await waitFor(() => {
      expect(cotizarMock).toHaveBeenCalledTimes(2);
    });

    await act(async () => {
      segunda.resolver(cotizacion(2, "70.00"));
    });

    await waitFor(() => {
      expect(result.current.cotizacion?.cantidad).toBe(2);
    });

    // La respuesta que viaja más lento es de la cantidad ANTERIOR: no puede
    // pisar la cotización vigente.
    await act(async () => {
      primera.resolver(cotizacion(1, "35.00"));
    });

    await waitFor(() => {
      expect(result.current.cotizacion?.cantidad).toBe(2);
      expect(result.current.cotizacion?.total).toBe("70.00");
    });
  });

  it("dropping the quotation also drops the answer that is travelling", async () => {
    const pendiente = diferido<ReturnType<typeof cotizacion>>();
    cotizarMock.mockImplementationOnce(() => pendiente.promesa);

    const { result } = renderHook(() => useCotizacionPase());

    act(() => {
      result.current.cotizar("pase-1", 1);
    });

    await waitFor(() => {
      expect(cotizarMock).toHaveBeenCalledTimes(1);
    });

    act(() => {
      result.current.invalidar();
    });

    await act(async () => {
      pendiente.resolver(cotizacion(1, "35.00"));
    });

    expect(result.current.cotizacion).toBeNull();
  });
});

describe("ACP — el modal de la compra asistida de un pase", () => {
  it("muestra el precio que publicó el servidor y NUNCA lo calcula", async () => {
    cotizarMock.mockImplementation(({ cantidad }: { cantidad: number }) =>
      Promise.resolve(cotizacion(cantidad, cantidad === 2 ? "70.00" : "35.00")),
    );

    const queryClient = new QueryClient();
    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(screen.getByText("Cantidad cotizada: 1")).toBeDefined();
      },
      { timeout: 3000 },
    );

    expect(screen.getByText("Total cotizado: 35.00 PEN")).toBeDefined();
    expect(screen.getByText("Precio unitario: 35.00 PEN")).toBeDefined();

    // Dos unidades: el TOTAL publicado por el servidor es 70.00. El
    // navegador no lo multiplicó: lo imprimió.
    fireEvent.change(screen.getByLabelText(/Cantidad/), {
      target: { value: "2" },
    });

    await waitFor(
      () => {
        expect(screen.getByText("Total cotizado: 70.00 PEN")).toBeDefined();
      },
      { timeout: 3000 },
    );

    expect(screen.getByText("Cantidad cotizada: 2")).toBeDefined();
    expect(screen.getByText("Precio unitario: 35.00 PEN")).toBeDefined();
  });

  it("cambiar la cantidad VUELVE a cotizar en el servidor", async () => {
    cotizarMock.mockResolvedValue(cotizacion(1, "35.00"));

    const queryClient = new QueryClient();
    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(1);
      },
      { timeout: 3000 },
    );

    fireEvent.change(screen.getByLabelText(/Cantidad/), {
      target: { value: "3" },
    });

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(2);
      },
      { timeout: 3000 },
    );

    expect(cotizarMock).toHaveBeenLastCalledWith({
      pase_id: "pase-1",
      cantidad: 3,
    });
  });

  it("el importe declarado sólo se ofrece en el camino de los PASES", async () => {
    const queryClient = new QueryClient();
    const { unmount } = render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(
          screen.getByLabelText(/Importe declarado \(informativo\)/),
        ).toBeDefined();
      },
      { timeout: 3000 },
    );

    expect(
      screen.getByText(
        "El servidor confirma el total; este importe queda sólo como evidencia auditada.",
      ),
    ).toBeDefined();

    unmount();

    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PRODUCTO"
        concepto="Polo del FEST"
        itemId="producto-1"
      />,
      { wrapper: clienteConQuery(new QueryClient()) },
    );

    expect(
      screen.queryByLabelText(/Importe declarado \(informativo\)/),
    ).toBeNull();
  });
});

describe("ACP — los fallos del comando de compra", () => {
  /** Rellena la identidad, la evidencia y envía el comando. */
  async function enviarElFormulario() {
    fireEvent.change(screen.getByLabelText(/Número de documento/), {
      target: { value: "77777777" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Buscar la identidad del documento" }),
    );

    await waitFor(() => {
      expect(screen.getByText("Rosa Díaz")).toBeDefined();
    });

    fireEvent.change(screen.getByLabelText(/Referencia/), {
      target: { value: "REC-0001" },
    });
    fireEvent.change(screen.getByLabelText(/Motivo/), {
      target: { value: "Cobro en la boletería." },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Registrar la compra y su pago" }),
    );
  }

  it("el 409 del precio movido VUELVE a cotizar en vez de reintentar a ciegas", async () => {
    cotizarMock.mockResolvedValue(cotizacion(1, "35.00"));
    comprarMock.mockRejectedValue(
      new ErrorAdmin(409, "PRECIO_CAMBIADO", "El precio del pase cambió."),
    );

    const queryClient = new QueryClient();
    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(1);
      },
      { timeout: 3000 },
    );

    await enviarElFormulario();

    await waitFor(
      () => {
        expect(comprarMock).toHaveBeenCalledTimes(1);
      },
      { timeout: 3000 },
    );

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(2);
      },
      { timeout: 3000 },
    );

    // El modal SIGUE ABIERTO: el comando no se registró.
    expect(
      screen.getByRole("button", { name: "Registrar la compra y su pago" }),
    ).toBeDefined();
  });

  it("el 422 pone el error de cada campo en el control que lo posee", async () => {
    cotizarMock.mockResolvedValue(cotizacion(1, "35.00"));
    comprarMock.mockRejectedValue(
      new ErrorAdmin(422, "VALIDATION_ERROR", "Revisa los datos.", [
        {
          campo: "evidencia.referencia",
          codigo: "INVALID_VALUE",
          mensaje: "La referencia no es válida.",
        },
      ]),
    );

    const queryClient = new QueryClient();
    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(1);
      },
      { timeout: 3000 },
    );

    await enviarElFormulario();

    await waitFor(() => {
      expect(screen.getByText("La referencia no es válida.")).toBeDefined();
    });
  });

  it("el comando invalida SÓLO los pagos del área y las compras de pases", async () => {
    cotizarMock.mockResolvedValue(cotizacion(1, "35.00"));
    comprarMock.mockResolvedValue(COMPRA);

    const queryClient = new QueryClient();
    const invalidadas: unknown[] = [];
    const original = queryClient.invalidateQueries.bind(queryClient);
    queryClient.invalidateQueries = ((...argumentos: unknown[]) => {
      invalidadas.push(argumentos[0]);
      return original(...(argumentos as Parameters<typeof original>));
    }) as typeof queryClient.invalidateQueries;

    render(
      <ModalCompraParaCliente
        open
        onOpenChange={() => undefined}
        modo="PASE"
        concepto="Pase FEST"
        itemId="pase-1"
      />,
      { wrapper: clienteConQuery(queryClient) },
    );

    await waitFor(
      () => {
        expect(cotizarMock).toHaveBeenCalledTimes(1);
      },
      { timeout: 3000 },
    );

    await enviarElFormulario();

    await waitFor(() => {
      expect(invalidadas.length).toBeGreaterThan(0);
    });

    const claves = invalidadas.map(
      (invalidador) => (invalidador as { queryKey: unknown[] }).queryKey,
    );

    expect(claves).toContainEqual(["admin.pagos"]);
    expect(claves).toContainEqual(["pase", "compras"]);
    expect(claves).not.toContainEqual(["admin"]);
    expect(claves).not.toContainEqual(["pase", "catalogo"]);
  });
});
