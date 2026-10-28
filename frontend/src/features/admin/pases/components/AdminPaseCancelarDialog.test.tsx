// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdminPaseCancelarDialog } from "./AdminPaseCancelarDialog";

/**
 * The dialog of the administrative cancellation of a pass purchase.
 *
 * The suite verifies the contract of the flow:
 *
 * 1. the motive is MANDATORY and it is the only thing it collects,
 * 2. the operation is NOT a monetary refund and the dialog says so,
 * 3. the counts of the rights are reported and the cancellation travels with
 *    the audited motive,
 * 4. a failure reaches the administrator as an alert, never as a silent
 *    dismissal.
 */

const { cancelarCompraPase } = vi.hoisted(() => ({
  cancelarCompraPase: vi.fn(),
}));

vi.mock("../services/admin.pase.service", () => ({
  cancelarCompraPase,
}));

const COMPRA_ID = "22222222-2222-4222-8222-222222222222";
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

describe("AdminPaseCancelarDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cancelarCompraPase.mockResolvedValue({
      compra_id: COMPRA_ID,
      estado_compra: "CANCELADA",
      estado_orden: "CANCELADA",
      ya_cancelada: false,
      beneficiarios_revocados: 2,
      personas_afectadas: 2,
      motivo: "Solicitud del comprador",
    });
  });

  it("es un diálogo ACCESIBLE con su título", async () => {
    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        ordenPagoId={ORDEN_PAGO_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    const dialogo = await screen.findByRole("dialog");
    expect(dialogo).toHaveAccessibleName("Cancelar la compra de pases");
  });

  it("advierte que la cancelación NO es un reembolso", async () => {
    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(/no devuelve dinero/i);
  });

  it("muestra los conteos de los derechos que se revocarán", async () => {
    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    await screen.findByRole("dialog");
    expect(screen.getByText("Pase de Fiesta")).toBeInTheDocument();
    expect(screen.getByText("Derechos activos")).toBeInTheDocument();
  });

  it("viaja con el MOTIVO auditado que escribió el administrador", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        ordenPagoId={ORDEN_PAGO_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(
      screen.getByLabelText(/Motivo de la cancelación/),
      "Solicitud del comprador",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Cancelar la compra de pases" }),
    );

    await waitFor(() => {
      expect(cancelarCompraPase).toHaveBeenCalledTimes(1);
    });
    expect(cancelarCompraPase).toHaveBeenCalledWith(COMPRA_ID, {
      motivo: "Solicitud del comprador",
    });
  });

  it("el motivo es OBLIGATORIO: sin él no se envía nada", async () => {
    const usuario = userEvent.setup();

    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        ordenPagoId={ORDEN_PAGO_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.click(
      screen.getByRole("button", { name: "Cancelar la compra de pases" }),
    );

    await waitFor(() => {
      expect(
        screen.getByText(/El motivo de la cancelación es obligatorio/),
      ).toBeInTheDocument();
    });
    expect(cancelarCompraPase).not.toHaveBeenCalled();
  });

  it("renderiza el CONFLICTO del backend como alerta", async () => {
    const usuario = userEvent.setup();
    const { ApiQueryError } = await import("@/hooks/callsApi/useApiQuery");

    cancelarCompraPase.mockRejectedValue(
      new ApiQueryError("La compra no es una compra de pases.", 409),
    );

    renderizar(
      <AdminPaseCancelarDialog
        open
        onOpenChange={() => {}}
        compraId={COMPRA_ID}
        ordenPagoId={ORDEN_PAGO_ID}
        productoNombre="Pase de Fiesta"
        cantidad={3}
        beneficiariosActivos={2}
      />,
    );

    await screen.findByRole("dialog");
    await usuario.type(
      screen.getByLabelText(/Motivo de la cancelación/),
      "Solicitud del comprador",
    );
    await usuario.click(
      screen.getByRole("button", { name: "Cancelar la compra de pases" }),
    );

    const alerta = await screen.findByText(
      "La compra no es una compra de pases.",
    );
    expect(alerta).toBeInTheDocument();
  });
});
