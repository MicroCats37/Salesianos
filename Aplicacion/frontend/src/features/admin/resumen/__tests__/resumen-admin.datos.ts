import { resumenOperativoSchema } from "../schemas/resumen-admin.schema";

/**
 * The contract of the TRANSVERSAL summary, parsed by the SAME Zod mirror that
 * the service uses.
 *
 * A shape the mirror rejects breaks the suite BEFORE it draws anything
 * (`FR-08` §1.4): the data of a test is the answer of the contract, never a
 * hand-written object that the contract never accepted.
 */
export const RESUMEN_DERECHO = {
  edicion_id: "edicion-1",
  edicion_nombre: "FEST 2026",
  edicion_estado: "PUBLICADA",
  metricas: [
    {
      codigo: "INSCRIPCIONES",
      etiqueta: "Inscripciones",
      descripcion: "Inscripciones dadas de alta en la edición.",
      valor: 12,
    },
    {
      codigo: "EQUIPOS",
      etiqueta: "Equipos",
      descripcion: "Equipos declarados en las inscripciones.",
      valor: 4,
    },
  ],
  incidencias: [
    {
      codigo: "INSCRIPCIONES_PENDIENTES_DE_PAGO",
      etiqueta: "Inscripciones con cupos sin pagar",
      descripcion: "Cupos contratados que un pago verificado no habilitó.",
      cantidad: 3,
      accion: {
        codigo: "REVISAR_INSCRIPCIONES",
        etiqueta: "Revisar inscripciones",
        href: "/administracion/inscripciones?estado_pago=PENDIENTE",
      },
    },
  ],
};

/** The same answer, already parsed by the mirror of the service. */
export const RESUMEN_IZQUIERDO = resumenOperativoSchema.parse(RESUMEN_DERECHO);
