import { describe, expect, it } from "vitest";
import { AdminPagoListItemSchema } from "./admin.pago.schema";

/**
 * Contract test of the mirror of the payment row (A5).
 *
 * `estado_operativo` is the OPERATOR VERDICT of the payment: the ONE answer
 * to "is this payment done?". The backend owns it
 * (`backend/modules/pagos/domain/services/core/estado_operativo_pago_service.py`)
 * and the client RENDERS it — it never recomputes it.
 *
 * The mirror is 1:1 with the backend wrapper: a row without the verdict is
 * REJECTED, so a half-migrated contract fails loudly instead of silently
 * rendering an empty state.
 */

const FILA = {
  compra_id: "11111111-2222-3333-4444-555555555555",
  orden_pago_id: "22222222-3333-4444-5555-666666666666",
  numero_orden: "ORD-0001",
  inscripcion_id: "33333333-4444-5555-6666-777777777777",
  pase_id: null,
  responsable_nombre: "Persona Compradora",
  tipo: "INICIAL",
  producto_nombre: "Pack FEST",
  cantidad: 2,
  precio_unitario: 75,
  total: 150,
  estado_compra: "PAGADA",
  estado_orden: "PAGADA",
  pagada_en: "2026-10-01T12:00:00Z",
  origen_pago: "IZIPAY",
  estado_operativo: "PAGADA",
  monto_orden: 150,
  moneda_orden: "PEN",
  beneficiarios_activos: 0,
  beneficiarios_revocados: 0,
  created_at: "2026-09-30T09:00:00Z",
};

describe("admin.pago.schema — el veredicto operativo del pago", () => {
  it("acepta una fila con el veredicto operativo", () => {
    const parsed = AdminPagoListItemSchema.parse(FILA);

    expect(parsed.estado_operativo).toBe("PAGADA");
  });

  it("rechaza una fila sin el veredicto operativo", () => {
    const { estado_operativo: _veredicto, ...filaIncompleta } = FILA;

    const resultado = AdminPagoListItemSchema.safeParse(filaIncompleta);

    expect(resultado.success).toBe(false);
  });

  it("rechaza un veredicto vacio", () => {
    const resultado = AdminPagoListItemSchema.safeParse({
      ...FILA,
      estado_operativo: "",
    });

    // Una fila sin veredicto no tiene estado que mostrar: el espejo la
    // rechaza en lugar de dejar un badge vacio en la tabla.
    expect(resultado.success).toBe(false);
  });

  it("acepta un veredicto desconocido para poder renderizarlo neutro", () => {
    const resultado = AdminPagoListItemSchema.safeParse({
      ...FILA,
      estado_operativo: "INVENTADO",
    });

    // El codigo NO se estrecha: un veredicto nuevo atraviesa el espejo y la
    // interfaz lo renderiza neutro, sin romper la pagina entera.
    expect(resultado.success).toBe(true);
  });

  it("viaja con los hechos que lo sostienen, para el detalle", () => {
    const parsed = AdminPagoListItemSchema.parse({
      ...FILA,
      estado_compra: "PENDIENTE",
      estado_operativo: "PAGADA_SIN_LIQUIDAR",
    });

    // El veredicto NO reemplaza los hechos: siguen travelling como la traza
    // de auditoría de la decisión.
    expect(parsed.estado_operativo).toBe("PAGADA_SIN_LIQUIDAR");
    expect(parsed.estado_compra).toBe("PENDIENTE");
    expect(parsed.estado_orden).toBe("PAGADA");
    expect(parsed.origen_pago).toBe("IZIPAY");
  });
});
