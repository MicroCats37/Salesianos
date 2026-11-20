import { describe, expect, it } from "vitest";
import {
  SCHEMA_VERSION,
  ticketConfirmadoSchema,
  ticketPreviewEnvelope,
  ticketPreviewSchema,
} from "../schemas/validacion.schema";

/**
 * The contract mirror of the validation console (`RT-RT-01` / `RT-RT-02`).
 *
 * The backend publishes the FROZEN shape of `FR-05` §3.1 and §3.2. The mirror
 * has to be EXACT: a field that the server does not publish, or a field that
 * the server publishes and the mirror forgets, is a drift (`FR-07` §4).
 */

const UUID = "11111111-2222-3333-4444-555555555555";
const OTRO_UUID = "66666666-7777-8888-9999-000000000000";

const VISTA_PREVIA = {
  edicion_id: UUID,
  tipo_derecho: "PASE",
  codigo: "pase-fest",
  estado: "ACTIVO",
  cantidad_total: 2,
  cantidad_disponible: 1,
  cantidad_consumida: 1,
  puede_canjear: true,
  motivo_codigo: null,
  motivo_mensaje: null,
  titular: { persona_id: OTRO_UUID, nombre: "Ana Quispe" },
};

const CANJEADO = {
  validacion_id: UUID,
  tipo_derecho: "PASE",
  cantidad_consumida: 1,
  cantidad_restante: 0,
  estado: "CANJEADO",
  consumido_en: "2026-11-20T03:47:00Z",
  actor: { usuario_id: OTRO_UUID, persona_id: null },
  repetido: false,
};

describe("el espejo del contrato de la consola de validación", () => {
  it("declara la versión congelada del módulo", () => {
    expect(SCHEMA_VERSION).toBe("1.0.0");
  });

  it("acepta la forma congelada de la vista previa", () => {
    expect(ticketPreviewSchema.parse(VISTA_PREVIA)).toEqual(VISTA_PREVIA);
  });

  it("acepta una vista previa que no se puede canjear, con su motivo", () => {
    const denegada = {
      ...VISTA_PREVIA,
      puede_canjear: false,
      motivo_codigo: "TICKET_YA_CONSUMIDO",
      motivo_mensaje: "La credencial ya fue consumida.",
    };
    expect(ticketPreviewSchema.parse(denegada).motivo_codigo).toBe(
      "TICKET_YA_CONSUMIDO",
    );
  });

  it("RECHAZA una vista previa sin el titular", () => {
    const { titular, ...sinTitular } = VISTA_PREVIA;
    expect(ticketPreviewSchema.safeParse(sinTitular).success).toBe(false);
  });

  it("acepta la forma congelada del canje", () => {
    expect(ticketConfirmadoSchema.parse(CANJEADO)).toEqual(CANJEADO);
  });

  it("RECHAZA un canje sin la marca de tiempo", () => {
    const { consumido_en, ...sinInstante } = CANJEADO;
    expect(ticketConfirmadoSchema.safeParse(sinInstante).success).toBe(false);
  });

  it("exige el envelope de éxito con sus cuatro claves", () => {
    const envelope = ticketPreviewEnvelope.parse({
      success: true,
      data: VISTA_PREVIA,
      error: null,
      message: "Credencial comprobada correctamente.",
    });
    expect(envelope.data?.puede_canjear).toBe(true);
  });
});
