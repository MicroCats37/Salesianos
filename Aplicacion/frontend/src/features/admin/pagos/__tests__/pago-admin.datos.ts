import {
  adminPagoDetalleEnvelope,
  listaPagosAdminEnvelope,
  pagoAdminDetalleDesdeWire,
  pagoAdminListaDesdeWire,
} from "../schemas/pago-admin.schema";
import type {
  AdminPagoDetalleOut,
  AdminPagoListItemOut,
} from "../types/pagos-admin.types";

/**
 * The data of the suites of the payments.
 *
 * It is the ANSWER OF THE CONTRACT, parsed by the SAME Zod mirror that the
 * service uses (`FR-08` §1.4).
 *
 * The amount is `"0.00"` on purpose: an example amount must not look like a
 * real price (`FR-08` §2.4) and the browser NEVER calculates one.
 */

function datosDe<T>(envelope: { data: T | null }): T {
  if (!envelope.data) {
    throw new Error("El espejo del contrato no devolvió datos.");
  }

  return envelope.data;
}

const ESTADO_PENDIENTE = {
  codigo: "PENDIENTE",
  etiqueta: "Pago pendiente",
  descripcion: "El pago todavía no se ha confirmado.",
};

const PAGO = {
  compra_id: "00000000-0000-4000-8000-0000000000B1",
  orden_pago_id: "00000000-0000-4000-8000-0000000000F1",
  tipo_compra: "INSCRIPCION",
  resumen_concepto: "RESUMEN DE EJEMPLO",
  comprador: {
    persona_id: "00000000-0000-4000-8000-0000000000B2",
    nombre: "COMPRADOR DE EJEMPLO",
  },
  monto: "0.00",
  moneda: "PEN",
  estado_operativo: ESTADO_PENDIENTE,
  entrega_derechos: {
    codigo: "SIN_ENTREGA",
    etiqueta: "Sin derechos habilitados",
  },
  acciones_disponibles: ["VER_INSCRIPCION", "VER_HISTORIAL"],
};

/** The rows of the operational list of the payments. */
export const listaPagosAdmin: readonly AdminPagoListItemOut[] = datosDe(
  listaPagosAdminEnvelope.parse({
    success: true,
    data: {
      items: [{ ...PAGO, fecha: "2026-01-01" }],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    },
    error: null,
    message: null,
  }),
).items.map(pagoAdminListaDesdeWire);

/** The commercial detail of a payment. */
export const detallePagoAdmin: AdminPagoDetalleOut = pagoAdminDetalleDesdeWire(
  datosDe(
    adminPagoDetalleEnvelope.parse({
      success: true,
      data: {
        ...PAGO,
        compra: {
          id: "00000000-0000-4000-8000-0000000000B1",
          estado: "PENDIENTE",
          total: "0.00",
          moneda: "PEN",
          reutilizada: false,
        },
        origen_pago: "SIN_PAGO",
        intentos: [
          {
            id: "00000000-0000-4000-8000-0000000000F2",
            intento: 1,
            estado: "PENDIENTE",
            verificada: false,
            codigo_respuesta: "00",
            metodo_pago: "",
            creada_en: "2026-01-01T00:00:00Z",
          },
        ],
        operaciones_manuales: [
          {
            id: "00000000-0000-4000-8000-0000000000F3",
            canal: "BROWSER",
            monto: "0.00",
            moneda: "PEN",
            motivo: "MOTIVO DE EJEMPLO",
            registrada_en: "2026-01-01T00:00:00Z",
            actor: "ADMINISTRADOR DE EJEMPLO",
          },
        ],
        siguiente_accion: null,
      },
      error: null,
      message: null,
    }),
  ),
);
