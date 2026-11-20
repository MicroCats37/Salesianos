/**
 * TEST-ONLY example values of the account area.
 *
 * They are NOT a contract fixture and they are NOT a mirror of a presenter:
 * the wrappers of the account (`RT-ID-04`, `RT-ID-05`, `RT-ID-06`) have NO
 * registered backend route yet, so there is no frozen wrapper to mirror and
 * nothing to declare here. These values exist ONLY so the suites can exercise
 * the POPULATED compositions of the views (the list, the filters, the verdict
 * chip and the partial payment).
 *
 * The rules of the contract that applied to the provisional fixture still
 * apply here: the values are EXAMPLES, not calculations. A price, a capacity,
 * a payment state and a permission are DECLARED, never derived: this module
 * contains no `if`, no arithmetic and no clock.
 *
 * This module lives inside `__tests__` and is imported by NO production
 * module (`FR-08` §1.2, Exports). The production routes of the account area
 * render their HONEST state until the backend owns those routes.
 */

import type {
  CompraDetalle,
  CompraResumen,
  InscripcionResumen,
  Pagina,
  ResumenCuenta,
  Veredicto,
} from "../types/cuenta.types";

/** The verdict of a payment that has not been confirmed yet. */
export const veredictoPendiente: Veredicto = {
  estado: {
    codigo: "PENDIENTE",
    etiqueta: "Pago pendiente",
    descripcion: "El pago todavía no ha sido confirmado.",
  },
  rol: "pendiente",
};

/** The verdict of a payment whose evidence is not conclusive yet. */
export const veredictoVerificando: Veredicto = {
  estado: {
    codigo: "VERIFICANDO",
    etiqueta: "Verificando pago",
    descripcion: "Recibimos el resultado del pago y todavía no es concluyente.",
  },
  rol: "verificando",
};

/**
 * The verdict of a payment that was charged but whose right is not enabled
 * yet. This is the PARTIAL state (`SH-03` §5).
 */
export const veredictoAtencion: Veredicto = {
  estado: {
    codigo: "NECESITA_ATENCION",
    etiqueta: "Pago confirmado, pendiente de activación",
    descripcion:
      "El pago está confirmado, pero el derecho todavía no se ha habilitado.",
  },
  rol: "atencion",
};

/** The verdict of a payment the provider did not complete. */
export const veredictoSinConfirmar: Veredicto = {
  estado: {
    codigo: "NO_COMPLETADO",
    etiqueta: "Pago no completado",
    descripcion: "El intento de pago no se completó y la compra sigue pendiente.",
  },
  rol: "sin-confirmar",
};

/** The verdict of a confirmed payment whose right is already enabled. */
export const veredictoConfirmado: Veredicto = {
  estado: {
    codigo: "CONFIRMADO",
    etiqueta: "Pago confirmado",
    descripcion: "El pago está confirmado y el derecho está habilitado.",
  },
  rol: "confirmado",
};

/** A registration of the responsible. */
export const inscripcionEjemplo: InscripcionResumen = {
  id: "00000000-0000-4000-8000-0000000000A1",
  edicion: "EDICIÓN 2026",
  paquete: "PAQUETE DE EJEMPLO",
  equipos: 1,
  personas: 6,
  cupos_disponibles: 2,
  veredicto: veredictoPendiente,
  siguiente_accion: {
    etiqueta: "Completar el pago",
    href: "/mis-inscripciones/00000000-0000-4000-8000-0000000000A1",
  },
};

/** A purchase of the account, as the list shows it. */
export const compraEjemplo: CompraResumen = {
  id: "00000000-0000-4000-8000-0000000000B1",
  origen: "INSCRIPCION",
  concepto: "PAQUETE DE EJEMPLO",
  monto: "0.00",
  moneda: "PEN",
  fecha: "21 de noviembre de 2026",
  veredicto: veredictoConfirmado,
};

/** A purchase of the account, as the detail shows it. */
export const compraDetalleEjemplo: CompraDetalle = {
  ...compraEjemplo,
  veredicto: veredictoAtencion,
  derechos: [
    { codigo: "CUPOS", etiqueta: "Cupos deportivos" },
    { codigo: "INSCRIPCION", etiqueta: "Inscripción" },
  ],
  ruta_origen: "/mis-inscripciones/00000000-0000-4000-8000-0000000000A1",
};

/** The counters of the account hub. */
export const resumenCuentaEjemplo: ResumenCuenta = {
  inscripciones: 1,
  compras: 1,
};

/** The one pagination shape of the frozen envelope. */
export const paginaVaciaEjemplo: Pagina<never> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 25,
  total_pages: 0,
};
