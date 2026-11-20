import { describe, expect, it } from "vitest";

import {
  entregaConfirmadaSchema,
  entregaPendienteSchema,
  entregasPendientesEnvelope,
  paseBeneficiarioSchema,
} from "../schemas/validacion.schema";
import { ENTREGA_PENDIENTE } from "./datos.contract";

/**
 * The mirror of the wire of the TARGET backend for the validation area.
 *
 * The examples are the JSON that the presenters of `DOM-03` and `DOM-06`
 * publish
 * (`Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pase_schemas.py`
 * and
 * `Aplicacion/backend/modules/marketplace/presentation/schemas/inventario_schemas.py`).
 * They are EXAMPLES of the wire, not a transport: no module of production
 * imports this file.
 *
 * **These suites have NEVER RUN.** They are written and the execution is
 * deferred to the verification phase. Nothing here may be read as a green
 * result.
 */
describe("API-05 — el espejo del backend objetivo (validaciones)", () => {
  it("acepta la forma exacta de EntregaPendienteOut", () => {
    const resultado = entregaPendienteSchema.parse(ENTREGA_PENDIENTE);

    expect(resultado.pedido_id).toBe(ENTREGA_PENDIENTE.pedido_id);
    expect(resultado.lineas[0].concepto_nombre).toBe("Camiseta del festival");
  });

  it("el importe es un NÚMERO: el backend serializa el Decimal así", () => {
    expect(() =>
      entregaPendienteSchema.parse({
        ...ENTREGA_PENDIENTE,
        total: "24.00",
      }),
    ).toThrow();
  });

  it("el estado del pedido y el de la entrega son DOS hechos", () => {
    const resultado = entregaPendienteSchema.parse(ENTREGA_PENDIENTE);

    expect(resultado.estado).toBe("PAGADO");
    expect(resultado.estado_entrega).toBe("PENDIENTE");
  });

  it("la cola de recogidas separa pendientes de entregadas", () => {
    const respuesta = entregasPendientesEnvelope.parse({
      success: true,
      data: { pendientes: [ENTREGA_PENDIENTE], entregadas: [] },
      error: null,
      message: null,
    });

    expect(respuesta.data?.pendientes).toHaveLength(1);
  });

  it("acepta la forma exacta de EntregaConfirmadaOut", () => {
    const resultado = entregaConfirmadaSchema.parse({
      pedido_id: ENTREGA_PENDIENTE.pedido_id,
      estado_entrega: "ENTREGADO",
      cantidad_total: 2,
      actor_id: "2c3d4e5f-6a7b-8c9d-8e1f-2a3b4c5d6e7f",
      entregada_en: "2026-11-21T19:12:40+00:00",
      lineas: ENTREGA_PENDIENTE.lineas,
    });

    expect(resultado.cantidad_total).toBe(2);
    expect(resultado.estado_entrega).toBe("ENTREGADO");
  });

  it("RECHAZA una entrega sin identificador de pedido", () => {
    expect(() =>
      entregaPendienteSchema.parse({ ...ENTREGA_PENDIENTE, pedido_id: "" }),
    ).toThrow();
  });

  it("el derecho de entrada se REUSA del dueño del lote, no se duplica", () => {
    // El espejo del pase pertenece a `features/pases`: la consola de
    // validación no publica una segunda copia de la misma forma de wire.
    const derecho = paseBeneficiarioSchema.parse({
      id: "5c9d0e1f-2a3b-4c5d-8e7f-8091a2b3c4d5",
      pase_id: "6d0e1f2a-3b4c-5d6e-8f80-91a2b3c4d5e6",
      pase_nombre: "Pase general",
      edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
      persona_id: "7e1f2a3b-4c5d-6e7f-8091-a2b3c4d5e6f7",
      persona_nombres: "María",
      persona_apellidos: "Fernández",
      persona_tipo_documento: "DNI",
      persona_numero_documento: "10000001",
      origen: "COMPRA",
      estado: "ACTIVO",
      cantidad: 1,
      cantidad_consumida: 0,
      cantidad_disponible: 1,
      asignado_en: "2026-11-18T14:20:00+00:00",
      motivo: "",
      revocado_en: null,
      motivo_revocacion: "",
    });

    expect(derecho.cantidad_disponible).toBe(1);
    expect(derecho.estado).toBe("ACTIVO");
  });
});
