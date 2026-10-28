import { describe, expect, it } from "vitest";
import {
  type PaseEstadoLike,
  paseActivacionPendiente,
  paseCompraCancelada,
  paseCompraPagable,
  paseEstadoTone,
  paseOrigenPagoLabel,
  paseSiguientePaso,
} from "./pase.estado";

/**
 * The tests of the commercial state of a pass purchase.
 *
 * The module under test is dependency-free on purpose, so the mapping can be
 * verified without the React/axios runtime.
 */

/** A commercial state of a purchase. */
function estado(estadoCompra: string, estadoOrden: string): PaseEstadoLike {
  return { estado_compra: estadoCompra, estado_orden: estadoOrden };
}

describe("pase.estado · tono del estado", () => {
  it("una compra pagada se presenta como pagada", () => {
    expect(paseEstadoTone(estado("PAGADA", "PAGADA"))).toBe("pagada");
  });

  it("una compra pendiente sin pago es pendiente", () => {
    expect(paseEstadoTone(estado("PENDIENTE", "PENDIENTE"))).toBe("pendiente");
  });

  it("una orden vencida vence la compra", () => {
    expect(paseEstadoTone(estado("PENDIENTE", "VENCIDA"))).toBe("vencida");
  });

  it("una compra cancelada está cancelada aunque su orden esté pagada", () => {
    expect(paseEstadoTone(estado("CANCELADA", "PAGADA"))).toBe("cancelada");
    expect(paseEstadoTone(estado("PENDIENTE", "CANCELADA"))).toBe("cancelada");
  });

  it("un estado desconocido se presenta como pendiente", () => {
    expect(paseEstadoTone(estado("INVENTADO", "INVENTADO"))).toBe("pendiente");
  });
});

describe("pase.estado · pagabilidad", () => {
  it("una compra pendiente con orden pendiente se puede pagar", () => {
    expect(paseCompraPagable(estado("PENDIENTE", "PENDIENTE"))).toBe(true);
  });

  it("una orden ya pagada NO se puede pagar de nuevo", () => {
    expect(paseCompraPagable(estado("PENDIENTE", "PAGADA"))).toBe(false);
  });

  it("una compra pagada no se puede pagar", () => {
    expect(paseCompraPagable(estado("PAGADA", "PAGADA"))).toBe(false);
  });
});

describe("pase.estado · activación pendiente", () => {
  it("el pago registrado con la compra aún pendiente es una activación pendiente", () => {
    expect(paseActivacionPendiente(estado("PENDIENTE", "PAGADA"))).toBe(true);
  });

  it("una compra pagada ya no tiene la activación pendiente", () => {
    expect(paseActivacionPendiente(estado("PAGADA", "PAGADA"))).toBe(false);
  });
});

describe("pase.estado · cancelación", () => {
  it("detecta la compra y la orden canceladas", () => {
    expect(paseCompraCancelada(estado("CANCELADA", "PAGADA"))).toBe(true);
    expect(paseCompraCancelada(estado("PENDIENTE", "CANCELADA"))).toBe(true);
    expect(paseCompraCancelada(estado("PENDIENTE", "PENDIENTE"))).toBe(false);
  });
});

describe("pase.estado · siguiente paso", () => {
  it("una compra pagada pide asignar los beneficiarios", () => {
    expect(paseSiguientePaso(estado("PAGADA", "PAGADA"))).toContain(
      "asignar las personas",
    );
  });

  it("una activación pendiente NO se presenta como una compra pagada", () => {
    const mensaje = paseSiguientePaso(estado("PENDIENTE", "PAGADA"));
    expect(mensaje).toContain("activación comercial sigue pendiente");
    expect(mensaje).not.toContain("Tu pase está pagado");
  });

  it("una compra pendiente pide completar el pago", () => {
    expect(paseSiguientePaso(estado("PENDIENTE", "PENDIENTE"))).toContain(
      "Completa el pago",
    );
  });

  it("una orden vencida pide comprar de nuevo", () => {
    expect(paseSiguientePaso(estado("PENDIENTE", "VENCIDA"))).toContain(
      "venció",
    );
  });

  it("una compra cancelada informa que fue cancelada", () => {
    expect(paseSiguientePaso(estado("CANCELADA", "PAGADA"))).toContain(
      "cancelada",
    );
  });
});

describe("pase.estado · origen del pago", () => {
  it("cada origen verificado tiene su etiqueta", () => {
    expect(paseOrigenPagoLabel("IZIPAY")).toContain("pasarela");
    expect(paseOrigenPagoLabel("MANUAL")).toContain("administración");
    expect(paseOrigenPagoLabel("SIN_PAGO")).toContain("Sin pago");
  });

  it("un origen ausente no inventa una etiqueta de pago", () => {
    expect(paseOrigenPagoLabel(null)).toBe("Origen del pago desconocido");
  });
});
