// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdminPagoManualDialog } from "./AdminPagoManualDialog";

/**
 * The dialog of the administrative approval and annulment of a manual
 * payment.
 *
 * The suite verifies the contract of the flow:
 *
 * 1. the approval is prefilled with the amounts of the ORDER (the approval
 *    never adjusts the price of an order),
 * 2. the payload travels with the evidence the administrator typed,
 * 3. the annulment asks ONLY for the audited motive,
 * 4. a failure reaches the administrator as an alert, never as a silent
 *    dismissal.
 */

const { anularPagoManual, aprobarPagoManual } = vi.hoisted(() => ({
  anularPagoManual: vi.fn(),
  aprobarPagoManual: vi.fn(),
}));

vi.mock("../services/admin.pago.service", () => ({
  anularPagoManual,
  aprobarPagoManual,
  getAdminPagoDetalle: vi.fn(),
  getAdminPagos: vi.fn(),
}));

const ORDEN_PAGO_ID = "11111111-1111-4111-8111-111111111111";

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

describe("AdminPagoManualDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    aprobarPagoManual.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
    anularPagoManual.mockResolvedValue({
      success: true,
      data: null,
      error: null,
      message: null,
    });
  });

  it("prefill el monto y la moneda de la ORDEN", async () => {
    renderizar(
      <AdminPagoManualDialog
        open
        onOpenChange={() => {}}
        modo="aprobar"
        ordenPagoId={ORDEN_PAGO_ID}
        numeroOrden="OP-100"
        montoOrden={400}
        monedaOrden="PEN"
      />,
    );

    expect(await screen.findByLabelText(/Monto/)).toHaveValue("400");
    expect(await screen.findByLabelText(/Moneda/)).toHaveValue("PEN");
  });

  it("es un diálogo ACCESIBLE con su título", async () => {
    renderizar(
      <AdminPagoManualDialog
        open
        onOpenChange={() => {}}
        modo="aprobar"
        ordenPagoId={ORDEN_PAGO_ID}
        numeroOrden="OP-100"
        montoOrden={400}
        monedaOrden="PEN"
      />,
    );

    const dialogo = await screen.findByRole("dialog");
    expect(dialogo).toHaveAccessibleName("Registrar el pago manual");
  });

  it("viaja con la EVIDENCIA que escribió el administrador", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <AdminPagoManualDialog
        open
        onOpenChange={() => {}}
        modo="aprobar"
        ordenPagoId={ORDEN_PAGO_ID}
        numeroOrden="OP-100"
        montoOrden={400}
        monedaOrden="PEN"
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(screen.getByLabelText(/Referencia del pago/), "OP-999");
    await usuario.type(
      screen.getByLabelText(/Motivo de la aprobación/),
      "Abono verificado en la cuenta",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Registrar el pago" }),
    );

    await waitFor(() => {
      expect(aprobarPagoManual).toHaveBeenCalledTimes(1);
    });
    expect(aprobarPagoManual).toHaveBeenCalledWith(ORDEN_PAGO_ID, {
      canal: "TRANSFERENCIA_BANCARIA",
      referencia: "OP-999",
      monto: 400,
      moneda: "PEN",
      motivo: "Abono verificado en la cuenta",
    });
  });

  it("la ANULACIÓN pide SOLO el motivo auditado", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <AdminPagoManualDialog
        open
        onOpenChange={() => {}}
        modo="anular"
        ordenPagoId={ORDEN_PAGO_ID}
        numeroOrden="OP-100"
      />,
    );

    await screen.findByRole("dialog");
    expect(screen.queryByLabelText(/Referencia del pago/)).toBeNull();

    await usuario.type(
      screen.getByLabelText(/Motivo de la anulación/),
      "Registro administrativo duplicado",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Anular la aprobación" }),
    );

    await waitFor(() => {
      expect(anularPagoManual).toHaveBeenCalledTimes(1);
    });
    expect(anularPagoManual).toHaveBeenCalledWith(ORDEN_PAGO_ID, {
      motivo: "Registro administrativo duplicado",
    });
  });

  it("renderiza el CONFLICTO del backend como alerta", async () => {
    const usuario = userEvent.setup();
    const { ApiQueryError } = await import("@/hooks/callsApi/useApiQuery");

    aprobarPagoManual.mockRejectedValue(
      new ApiQueryError(
        "El monto y la moneda no coinciden con la orden de pago.",
        409,
      ),
    );

    renderizar(
      <AdminPagoManualDialog
        open
        onOpenChange={() => {}}
        modo="aprobar"
        ordenPagoId={ORDEN_PAGO_ID}
        numeroOrden="OP-100"
        montoOrden={400}
        monedaOrden="PEN"
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(screen.getByLabelText(/Referencia del pago/), "OP-999");
    await usuario.type(
      screen.getByLabelText(/Motivo de la aprobación/),
      "Abono verificado en la cuenta",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Registrar el pago" }),
    );

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(
      "El monto y la moneda no coinciden con la orden de pago.",
    );
  });
});
