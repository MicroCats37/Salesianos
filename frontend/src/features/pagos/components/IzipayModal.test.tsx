// @vitest-environment jsdom
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  INTERVALO_SONDEO_MS,
  MAX_SONDEOS,
} from "../utils/checkout.recuperacion";
import { IzipayModal } from "./IzipayModal";

/**
 * The checkout of the frontend.
 *
 * The suite verifies the CONTRACT of the recovery:
 *
 * 1. closing the modal releases the checkout of the provider,
 * 2. a typed preparation error is rendered with the PUBLIC message of the API
 *    — never with a raw HTTP status string,
 * 3. an uncertain relay is recovered from the state of the transaction that
 *    was prepared,
 * 4. the verification is BOUNDED: it ends with a message the operator can
 *    act upon.
 */

const { iniciarPagoIzipay, confirmarPagoIzipay, obtenerEstadoTransaccion } =
  vi.hoisted(() => ({
    iniciarPagoIzipay: vi.fn(),
    confirmarPagoIzipay: vi.fn(),
    obtenerEstadoTransaccion: vi.fn(),
  }));

vi.mock("../services/pago.service", () => ({
  iniciarPagoIzipay,
  confirmarPagoIzipay,
  obtenerEstadoTransaccion,
}));

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

// ── Provider SDK falso ────────────────────────────────────────────────────────

interface OpcionesFormulario {
  authorization: string;
  callbackResponse: (payload: unknown) => void | Promise<void>;
}

/**
 * The fake provider SDK: it renders the form inside the container of the
 * modal and it releases it when the popup closes.
 */
class CheckoutFalso {
  static instancias: CheckoutFalso[] = [];

  desmontado = false;
  opciones: OpcionesFormulario | null = null;

  constructor(_config: unknown) {
    CheckoutFalso.instancias.push(this);
  }

  LoadForm(opciones: OpcionesFormulario) {
    this.opciones = opciones;

    const contenedor = document.getElementById("izipay-checkout");
    const formulario = document.createElement("div");
    formulario.dataset.testid = "formulario-del-proveedor";
    contenedor?.appendChild(formulario);
  }

  Unmount() {
    this.desmontado = true;
  }
}

// ── Payloads ──────────────────────────────────────────────────────────────────

const TRANSACCION_ID = "12345678901234";

const PREPARACION_OK = {
  success: true,
  data: {
    compra_id: "c-1",
    orden_pago_id: "o-1",
    transaction_id: TRANSACCION_ID,
    order_number: "1234567890",
    token: "token-de-sesion",
    merchant_code: "tienda",
    amount: 400,
    currency: "PEN",
    buyer_email: "comprador@ejemplo.pe",
    buyer_name: "Juan",
    buyer_surname: "Perez",
  },
  error: undefined,
  message: null,
};

const PAYLOAD_APROBADO = {
  code: "00",
  message: "Operación completada",
  transactionId: TRANSACCION_ID,
  orderNumber: "1234567890",
  amount: "400.00",
  signature: "firma",
  payloadHttp: "payload",
  response: { payMethod: "CARD" },
};

const CONFIRMACION_OK = {
  success: true,
  data: {
    transaction_id: TRANSACCION_ID,
    success: true,
    status: "EXITO",
    orden_pago_id: "o-1",
    response_code: "00",
    response_message: "Operación completada",
    metodo_pago: "CARD",
    already_confirmed: false,
    settlement_status: "SETTLED",
  },
  message: "Pago realizado con éxito.",
};

function transaccion(estado: "PENDIENTE" | "EXITO") {
  return {
    success: true,
    data: {
      id: "t-1",
      orden_pago_id: "o-1",
      transaction_id: TRANSACCION_ID,
      order_number: "1234567890",
      amount: 400,
      currency: "PEN",
      status: estado,
      response_code: estado === "EXITO" ? "00" : null,
      response_message: estado === "EXITO" ? "Operación completada" : null,
      metodo_pago: estado === "EXITO" ? "CARD" : null,
      created_at: "2026-01-01T00:00:00",
      updated_at: "2026-01-01T00:00:00",
    },
    message: "Transaccion encontrada.",
  };
}

/** Avanza el reloj falso y deja que React aplique los cambios. */
async function avanzar(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

function renderModal(
  props: { onClose?: () => void; onSuccess?: () => void | Promise<void> } = {},
) {
  const onClose = props.onClose ?? vi.fn();
  const onSuccess = props.onSuccess ?? vi.fn();

  const utils = render(
    <IzipayModal
      isOpen
      onClose={onClose}
      compraId="c-1"
      onSuccess={onSuccess}
    />,
  );

  return { ...utils, onClose, onSuccess };
}

// ── Suite ─────────────────────────────────────────────────────────────────────

describe("IzipayModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    CheckoutFalso.instancias = [];
    (window as unknown as { Izipay?: unknown }).Izipay = CheckoutFalso;

    iniciarPagoIzipay.mockResolvedValue(PREPARACION_OK);
    confirmarPagoIzipay.mockResolvedValue(CONFIRMACION_OK);
    obtenerEstadoTransaccion.mockResolvedValue(transaccion("EXITO"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("libera el checkout del PROVEEDOR cuando el modal se cierra", async () => {
    const onClose = vi.fn();
    const { rerender } = renderModal({ onClose });

    await waitFor(() => expect(CheckoutFalso.instancias).toHaveLength(1));
    const checkout = CheckoutFalso.instancias[0];
    expect(checkout.desmontado).toBe(false);

    rerender(
      <IzipayModal
        isOpen={false}
        onClose={onClose}
        compraId="c-1"
        onSuccess={vi.fn()}
      />,
    );

    await waitFor(() => expect(checkout.desmontado).toBe(true));
  });

  it("muestra el MENSAJE PÚBLICO del error tipado de la preparación", async () => {
    iniciarPagoIzipay.mockRejectedValue(
      Object.assign(new Error("Request failed with status code 409"), {
        response: {
          status: 409,
          data: {
            success: false,
            data: null,
            error: {
              code: "RESOURCE_CHANGED",
              message:
                "El recurso cambió mientras lo editabas. Actualiza tus datos e inténtalo nuevamente.",
            },
          },
        },
      }),
    );

    renderModal();

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(
      "El recurso cambió mientras lo editabas. Actualiza tus datos e inténtalo nuevamente.",
    );
    expect(alerta).toHaveTextContent("RESOURCE_CHANGED");
    // NUNCA el texto crudo del estado HTTP.
    expect(alerta).not.toHaveTextContent("409");
    expect(alerta).not.toHaveTextContent("Request failed with status code");
  });

  it("detecta el PAGO cuando el relay es incierto y la transacción lo registra", async () => {
    // El relay NO responde: el pago puede haberse registrado igual.
    confirmarPagoIzipay.mockRejectedValue(new Error("Network Error"));

    const { onClose, onSuccess } = renderModal();

    await waitFor(() => expect(CheckoutFalso.instancias).toHaveLength(1));
    const checkout = CheckoutFalso.instancias[0];
    await waitFor(() => expect(checkout.opciones).not.toBeNull());

    await act(async () => {
      await checkout.opciones?.callbackResponse(PAYLOAD_APROBADO);
    });

    // Sólo se consulta la transacción que preparó ESTE checkout.
    await waitFor(() =>
      expect(obtenerEstadoTransaccion).toHaveBeenCalledWith(TRANSACCION_ID),
    );
    await waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(1));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("recupera el PAGO cuando el popup se cierra SIN relay", async () => {
    vi.useFakeTimers();

    const { onClose, onSuccess } = renderModal();

    await avanzar(10);
    expect(CheckoutFalso.instancias).toHaveLength(1);

    // El proveedor cierra el popup: libera lo que renderizó y NO invoca el
    // callback. El relay es INCIERTO.
    await act(async () => {
      document
        .querySelector('[data-testid="formulario-del-proveedor"]')
        ?.remove();
    });

    // El periodo de gracia deja que el callback del proveedor llegue.
    await avanzar(2000);

    expect(obtenerEstadoTransaccion).toHaveBeenCalledWith(TRANSACCION_ID);
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("ACOTA la verificación y avisa cuando el pago no se puede confirmar", async () => {
    vi.useFakeTimers();

    confirmarPagoIzipay.mockRejectedValue(new Error("Network Error"));
    obtenerEstadoTransaccion.mockResolvedValue(transaccion("PENDIENTE"));

    const { onSuccess } = renderModal();

    await avanzar(10);
    const checkout = CheckoutFalso.instancias[0];

    await act(async () => {
      await checkout.opciones?.callbackResponse(PAYLOAD_APROBADO);
    });
    await avanzar(10);

    await avanzar(MAX_SONDEOS * INTERVALO_SONDEO_MS + 1000);

    const alerta = screen.getByRole("alert");
    expect(alerta).toHaveTextContent("No se pudo verificar el pago");
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
