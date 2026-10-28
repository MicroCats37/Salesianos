import { describe, expect, it } from "vitest";
import type { PaseCatalogo, PasePrecio } from "../schemas/pase.schema";
import {
  formatearMontoPase,
  PASE_CANTIDAD_MAXIMA_POR_COMPRA,
  paseCantidadLimite,
  paseComprable,
  paseEtapaVigente,
  pasePrecioUnitario,
  paseTotal,
  redondearMonto,
} from "./pase.precio";

/**
 * The tests of the commercial rules of a pass.
 *
 * The module under test is dependency-free on purpose, so the rules can be
 * verified without the React/axios runtime.
 */

/** A price row of the calendar. */
function precio(
  etapa: string,
  precioUnitario: number,
  vigenteDesde: string,
  vigenteHasta: string | null = null,
): PasePrecio {
  return {
    etapa,
    precio_unitario: precioUnitario,
    vigente_desde: vigenteDesde,
    vigente_hasta: vigenteHasta,
  };
}

/** A pass of the catalogue. */
function pase(overrides: Partial<PaseCatalogo> = {}): PaseCatalogo {
  return {
    id: "pase-1",
    evento_id: "evento-1",
    nombre: "Pase de Fiesta",
    descripcion: "Acceso nominativo a la fiesta.",
    activo: true,
    precio_preventa: 40,
    precio_regular: 50,
    precio_vigente: 40,
    cantidad_maxima: 0,
    precios: [
      precio("PREVENTA", 40, "2026-10-01", "2026-10-25"),
      precio("REGULAR", 50, "2026-10-26", "2026-11-08"),
    ],
    ...overrides,
  };
}

describe("pase.precio · precio vigente", () => {
  it("devuelve el precio vigente que reporta el backend", () => {
    expect(pasePrecioUnitario(pase())).toBe(40);
  });

  it("no inventa un precio cuando el backend no reporta uno", () => {
    expect(pasePrecioUnitario(pase({ precio_vigente: null }))).toBeNull();
  });

  it("la etapa vigente es la que está dentro de su ventana", () => {
    expect(paseEtapaVigente(pase(), "2026-10-10")?.etapa).toBe("PREVENTA");
    expect(paseEtapaVigente(pase(), "2026-10-30")?.etapa).toBe("REGULAR");
  });

  it("el último día de la ventana es inclusivo, como en el backend", () => {
    expect(paseEtapaVigente(pase(), "2026-10-25")?.etapa).toBe("PREVENTA");
    expect(paseEtapaVigente(pase(), "2026-10-26")?.etapa).toBe("REGULAR");
  });

  it("la preventa gana cuando dos ventanas se solapan", () => {
    const solapado = pase({
      precios: [
        precio("PREVENTA", 40, "2026-10-01", "2026-11-08"),
        precio("REGULAR", 50, "2026-10-01", "2026-11-08"),
      ],
    });
    expect(paseEtapaVigente(solapado, "2026-10-15")?.etapa).toBe("PREVENTA");
  });

  it("no hay etapa vigente fuera de las ventanas", () => {
    expect(paseEtapaVigente(pase(), "2026-11-20")).toBeNull();
    expect(paseEtapaVigente(pase(), "2026-09-30")).toBeNull();
  });
});

describe("pase.precio · límite de cantidad", () => {
  it("el inventario limitado acota la cantidad", () => {
    expect(paseCantidadLimite(pase({ cantidad_maxima: 12 }))).toBe(12);
  });

  it("el inventario ilimitado deja el límite comercial del backend", () => {
    expect(paseCantidadLimite(pase({ cantidad_maxima: 0 }))).toBe(
      PASE_CANTIDAD_MAXIMA_POR_COMPRA,
    );
  });

  it("nunca supera el máximo por compra del backend", () => {
    expect(paseCantidadLimite(pase({ cantidad_maxima: 500 }))).toBe(
      PASE_CANTIDAD_MAXIMA_POR_COMPRA,
    );
  });
});

describe("pase.precio · total", () => {
  it("multiplica el precio vigente por la cantidad", () => {
    expect(paseTotal(pase(), 3)).toBe(120);
  });

  it("redondea a dos decimales", () => {
    expect(paseTotal(pase({ precio_vigente: 12.5 }), 3)).toBe(37.5);
    expect(redondearMonto(10.005)).toBe(10.01);
  });

  it("no muestra un total sin precio vigente", () => {
    expect(paseTotal(pase({ precio_vigente: null }), 2)).toBeNull();
  });

  it("no muestra un total de una cantidad inválida", () => {
    expect(paseTotal(pase(), 0)).toBeNull();
    expect(paseTotal(pase(), -1)).toBeNull();
  });
});

describe("pase.precio · presentación del monto", () => {
  it("usa el símbolo del sol para el PEN", () => {
    expect(formatearMontoPase(40, "PEN")).toBe("S/ 40.00");
  });

  it("usa el código de la moneda cuando no es el PEN", () => {
    expect(formatearMontoPase(40, "USD")).toBe("USD 40.00");
  });

  it("un monto ausente se presenta como un guion", () => {
    expect(formatearMontoPase(null)).toBe("—");
    expect(formatearMontoPase(undefined)).toBe("—");
  });
});

describe("pase.precio · pase comprable", () => {
  it("un pase activo con precio vigente es comprable", () => {
    expect(paseComprable(pase())).toBe(true);
  });

  it("un pase inactivo no es comprable", () => {
    expect(paseComprable(pase({ activo: false }))).toBe(false);
  });

  it("un pase sin precio vigente no es comprable", () => {
    expect(paseComprable(pase({ precio_vigente: null }))).toBe(false);
  });
});
