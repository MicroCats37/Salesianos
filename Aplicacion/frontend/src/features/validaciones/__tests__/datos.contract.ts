import { entregaPendienteSchema } from "../schemas/validacion.schema";
import type {
  RegistroValidacion,
  ResultadoValidacion,
  VistaPreviaValidacion,
} from "../types/validacion.types";
import { resolverVeredicto } from "../utils/validaciones.estados.utils";

/**
 * The data of the validation suite.
 *
 * ## WHY THE DATA LIVES HERE AND NOT IN A PRODUCTION FIXTURE
 *
 * The provisional fixture of `UI-05` was a file of PRODUCTION code that
 * carried a copy of the wire of the backend. `API-05` removes it, because the
 * wire of the backend is now written down ONCE, in the mirror
 * (`schemas/validacion.schema.ts`), and the suite reads that same mirror.
 *
 * These are EXAMPLES of the wire, not a transport: no module of production
 * imports this file and it is not exported from any barrel.
 *
 * ## TWO KINDS OF DATA, AND THE DIFFERENCE IS DECLARED
 *
 * - The **pickup** is the FROZEN shape of `DOM-06`
 *   (`EntregaPendienteOut`): it comes from the mirror.
 * - The **preview**, the **confirmation** and the **audit row** are
 *   PROVISIONAL: the module `validaciones` does not exist in the target, so
 *   `TicketPreviewOut`, `TicketConfirmadoOut` and
 *   `AdminValidacionListItemOut` have NO presenter to mirror. Their literals
 *   live HERE, in a test, and never in production code: a provisional
 *   contract is not a contract (`A0-API05-02`).
 */

/** A paid order that still waits for its pickup (`EntregaPendienteOut`). */
export const ENTREGA_PENDIENTE = entregaPendienteSchema.parse({
  pedido_id: "8b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  comprador_nombres: "María",
  comprador_apellidos: "Fernández",
  comprador_documento: "10000001",
  estado: "PAGADO",
  estado_entrega: "PENDIENTE",
  total: 24,
  moneda: "PEN",
  lineas: [
    {
      tipo_concepto: "PRODUCTO",
      concepto_id: "9c3d4e5f-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
      concepto_nombre: "Camiseta del festival",
      cantidad: 2,
      precio_unitario: 12,
      precio_aplicado: 12,
      subtotal: 24,
    },
  ],
  created_at: "2026-11-18T14:20:00+00:00",
});

/**
 * PROVISIONAL — the preview of an entry (`TicketPreviewOut`).
 *
 * There is NO presenter for it: the module `validaciones` does not exist in
 * the target. The shape is the seam where the real wrapper will land.
 */

/** A preview that the backend ADMITS: the credential can be consumed. */
export const VISTA_PREVIA_PERMITIDA: VistaPreviaValidacion = {
  puede_validar: true,
  veredicto: resolverVeredicto("VALIDACION_PERMITIDA"),
  titular: {
    nombres: "María",
    apellidos: "Fernández",
    tipo_documento: "DNI",
    numero_documento: "10000001",
  },
  derecho: {
    tipo: "PASE",
    nombre: "Pase general",
    estado: "ACTIVO",
    cantidad_total: 1,
    cantidad_consumida: 0,
    cantidad_disponible: 1,
    revocado_en: null,
  },
  punto: "Puerta principal",
  operador: "Operador de turno",
  instante: "2026-11-21T19:05:00+00:00",
};

/** A preview that the backend REFUSES: the credential was already used. */
export const VISTA_PREVIA_CONSUMIDA: VistaPreviaValidacion = {
  ...VISTA_PREVIA_PERMITIDA,
  puede_validar: false,
  veredicto: resolverVeredicto("TICKET_YA_CONSUMIDO"),
  derecho: {
    ...VISTA_PREVIA_PERMITIDA.derecho,
    cantidad_consumida: 1,
    cantidad_disponible: 0,
  },
  consumo_previo: {
    instante: "2026-11-21T18:42:00+00:00",
    punto: "Puerta principal",
    operador: "Operador de turno",
  },
};

/** A preview that the backend REFUSES: the right was revoked. */
export const VISTA_PREVIA_REVOCADA: VistaPreviaValidacion = {
  ...VISTA_PREVIA_PERMITIDA,
  puede_validar: false,
  veredicto: resolverVeredicto("DERECHO_REVOCADO"),
  derecho: {
    ...VISTA_PREVIA_PERMITIDA.derecho,
    estado: "REVOCADO",
    cantidad_disponible: 0,
    revocado_en: "2026-11-20T18:00:00+00:00",
  },
};

/** PROVISIONAL — the outcome of a CONFIRMED validation (`TicketConfirmadoOut`). */
export const RESULTADO_CONFIRMACION: ResultadoValidacion = {
  validado: true,
  veredicto: resolverVeredicto("VALIDACION_PERMITIDA"),
  cantidad_consumida: 1,
  punto: "Puerta principal",
  operador: "Operador de turno",
  instante: "2026-11-21T19:05:12+00:00",
  repetida: false,
};

/** PROVISIONAL — a row of the audit (`AdminValidacionListItemOut`). */
export const REGISTRO_ENTRADA: RegistroValidacion = {
  id: "0d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  tipo: "ENTRADA",
  veredicto: resolverVeredicto("VALIDACION_PERMITIDA"),
  titular: {
    nombres: "María",
    apellidos: "Fernández",
    tipo_documento: "DNI",
    numero_documento: "10000001",
  },
  referencia: "Pase general",
  punto: "Puerta principal",
  operador: "Operador de turno",
  instante: "2026-11-21T19:05:12+00:00",
  cantidad: 1,
};

/** PROVISIONAL — a row of the audit: a pickup that was refused. */
export const REGISTRO_ENTREGA: RegistroValidacion = {
  id: "1e5f6a7b-8c9d-0e1f-2a3b-4c5d-6e7f8091a2b3",
  tipo: "ENTREGA",
  veredicto: resolverVeredicto("TICKET_NO_ENCONTRADO"),
  titular: {
    nombres: "Juan",
    apellidos: "Pérez",
    tipo_documento: "DNI",
    numero_documento: "10000002",
  },
  referencia: "8b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  punto: "Mostrador de la tienda",
  operador: "Operador de turno",
  instante: "2026-11-21T19:12:40+00:00",
  cantidad: 0,
};
