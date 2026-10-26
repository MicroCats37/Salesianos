import type { AdminCampoOrden } from "./admin.lista.utils";

/**
 * The ordering WHITELISTS of the administration area — the client mirror of
 * the backend `ORDERING_*` maps of `AdminOperacionService`.
 *
 * The client NEVER invents an ordering value: it offers only these PUBLIC
 * field names and sends them verbatim. An unknown field would be rejected by
 * the backend with 422 `INVALID_REQUEST`.
 */

/** A3 — registrations. */
export const ORDEN_INSCRIPCIONES: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguas",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "estado", etiqueta: "Estado" },
  { campo: "responsable", etiqueta: "Responsable" },
  { campo: "paquete", etiqueta: "Paquete" },
];

/** A5 — payments. */
export const ORDEN_PAGOS: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguas",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "total", etiqueta: "Total" },
  { campo: "cantidad", etiqueta: "Cantidad" },
  { campo: "estado_compra", etiqueta: "Estado de la compra" },
  { campo: "estado_orden", etiqueta: "Estado de la orden" },
  {
    campo: "pagada_en",
    etiqueta: "Fecha de pago",
    etiquetaAsc: "Pago · más antiguos",
    etiquetaDesc: "Pago · más recientes",
  },
];

/** A7 — teams. */
export const ORDEN_EQUIPOS: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguos",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "nombre", etiqueta: "Nombre" },
  { campo: "disciplina", etiqueta: "Disciplina" },
  { campo: "estado", etiqueta: "Estado" },
];

/** A8 — registered people. */
export const ORDEN_PARTICIPANTES: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguas",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "persona", etiqueta: "Persona" },
  { campo: "estado", etiqueta: "Estado" },
];

/** A9 — roster rows. */
export const ORDEN_PARTICIPACIONES: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguas",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "persona", etiqueta: "Persona" },
  { campo: "equipo", etiqueta: "Equipo" },
  { campo: "disciplina", etiqueta: "Disciplina" },
  { campo: "rol", etiqueta: "Rol" },
  { campo: "estado", etiqueta: "Estado" },
];

/** A10 — accreditations. */
export const ORDEN_ACREDITACIONES: AdminCampoOrden[] = [
  { campo: "persona", etiqueta: "Persona" },
  { campo: "estado", etiqueta: "Estado" },
  { campo: "autorizacion_fiesta", etiqueta: "Autorización de fiesta" },
];

/** A12 — access log. */
export const ORDEN_ACCESOS: AdminCampoOrden[] = [
  {
    campo: "fecha_hora",
    etiqueta: "Fecha y hora",
    etiquetaAsc: "Accesos · más antiguos",
    etiquetaDesc: "Accesos · más recientes",
  },
  { campo: "resultado", etiqueta: "Resultado" },
  { campo: "punto_acceso", etiqueta: "Punto de acceso" },
];

/** A13 — accounts. */
export const ORDEN_USUARIOS: AdminCampoOrden[] = [
  {
    campo: "created_at",
    etiqueta: "Creación",
    etiquetaAsc: "Creación · más antiguas",
    etiquetaDesc: "Creación · más recientes",
  },
  { campo: "username", etiqueta: "Usuario" },
  { campo: "nombres", etiqueta: "Nombre" },
  {
    campo: "last_login",
    etiqueta: "Último acceso",
    etiquetaAsc: "Último acceso · más antiguos",
    etiquetaDesc: "Último acceso · más recientes",
  },
];

/** Default ordering of the registrations (A3). */
export const ORDEN_POR_DEFECTO_INSCRIPCIONES = "-created_at";

/** Default ordering of the payments (A5). */
export const ORDEN_POR_DEFECTO_PAGOS = "-created_at";

/** Default ordering of the teams (A7). */
export const ORDEN_POR_DEFECTO_EQUIPOS = "-created_at";

/** Default ordering of the registered people (A8). */
export const ORDEN_POR_DEFECTO_PARTICIPANTES = "-created_at";

/** Default ordering of the roster rows (A9). */
export const ORDEN_POR_DEFECTO_PARTICIPACIONES = "-created_at";

/** Default ordering of the accreditations (A10). */
export const ORDEN_POR_DEFECTO_ACREDITACIONES = "persona";

/** Default ordering of the access log (A12). */
export const ORDEN_POR_DEFECTO_ACCESOS = "-fecha_hora";

/** Default ordering of the accounts (A13). */
export const ORDEN_POR_DEFECTO_USUARIOS = "-created_at";
