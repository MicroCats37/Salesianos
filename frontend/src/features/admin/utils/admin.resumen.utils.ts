/**
 * Operational overview — pure mapping from the backend payload to the view
 * model of the administration dashboard.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically (same
 * pattern as `features/inscripciones/utils/pool.estado.ts`).
 *
 * The backend is the only authority: it decides every count, balance and
 * eligibility. This module NEVER recomputes a metric — it only groups,
 * labels and formats what the backend already sent
 * (`contract/api-wrapper-presenter-contract.md` §7).
 */

import type { AdminResumenResponse } from "../schemas";
import type { AdminTone } from "./admin.estado.utils";

export type { AdminTone };

/** A metric tile of the overview. */
export interface AdminKpi {
  id: string;
  label: string;
  /** Display-ready value (already formatted). */
  value: string;
  /** The raw number the backend sent — never recomputed. */
  rawValue: number;
  hint: string;
  tone: AdminTone;
  /** Route of the list that owns this metric. */
  ruta?: string;
}

/** A single item of an attention list. */
export interface AdminAlertItem {
  id: string;
  label: string;
  value: number;
  detail: string;
  tone: AdminTone;
  /**
   * Route of the list that shows the alerted items, already FILTERED.
   *
   * It is absent when the meaning of the alert CANNOT be expressed as a
   * filter of the backend: an alert without a filter is plain text, never a
   * link that opens an unfiltered list.
   */
  ruta?: string;
}

/** An attention list: one operational area that needs attention. */
export interface AdminAlertGroup {
  id: string;
  title: string;
  description: string;
  items: AdminAlertItem[];
}

/**
 * Tone of every inscription state — mirrors the state vocabulary of the
 * backend `EstadoInscripcionChoices`.
 */
const ESTADO_INSCIPCION_TONE: Record<string, AdminTone> = {
  BORRADOR: "amber",
  RECIBIDA: "blue",
  EN_REVISION: "violet",
  OBSERVADA: "orange",
  VALIDADA: "cyan",
  CONFIRMADA: "emerald",
  RECHAZADA: "red",
  CANCELADA: "rose",
};

const ESTADO_INSCIPCION_LABEL: Record<string, string> = {
  BORRADOR: "Borrador",
  RECIBIDA: "Recibida",
  EN_REVISION: "En revisión",
  OBSERVADA: "Observada",
  VALIDADA: "Validada",
  CONFIRMADA: "Confirmada",
  RECHAZADA: "Rechazada",
  CANCELADA: "Cancelada",
};

const MONTO_FORMATTER = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const NUMERO_FORMATTER = new Intl.NumberFormat("es-PE");

/**
 * Tone of an inscription state.
 *
 * Unknown states fall back to `slate`: a state the UI does not know about is
 * rendered neutrally instead of being coloured as something it is not.
 */
export function estadoInscripcionTone(estado: string): AdminTone {
  return ESTADO_INSCIPCION_TONE[estado] ?? "slate";
}

/** Human label of an inscription state. */
export function estadoInscripcionLabel(estado: string): string {
  return ESTADO_INSCIPCION_LABEL[estado] ?? estado;
}

/** Format a monetary amount as Peruvian soles. */
export function formatearMonto(monto: number): string {
  return MONTO_FORMATTER.format(monto);
}

/** Format a plain integer with the local thousands separator. */
export function formatearNumero(valor: number): string {
  return NUMERO_FORMATTER.format(valor);
}

/**
 * Format a backend date.
 *
 * A date-only value (`YYYY-MM-DD`) is formatted without touching the time
 * zone: `new Date("2026-10-25")` is parsed as UTC midnight and would render
 * as the previous day in a negative UTC offset.
 */
export function formatearFecha(fecha: string | null | undefined): string {
  if (!fecha) return "—";

  const soloFecha = /^(\d{4})-(\d{2})-(\d{2})$/.exec(fecha);

  if (soloFecha) {
    return `${soloFecha[3]}/${soloFecha[2]}/${soloFecha[1]}`;
  }

  const instante = new Date(fecha);

  if (Number.isNaN(instante.getTime())) return "—";

  return instante.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/**
 * The seven metric tiles of the overview.
 *
 * The eighth block of the backend payload (`evento`) is the identity of the
 * active edition, so it is rendered as the header of the page instead of a
 * tile.
 */
export function resumenKpis(resumen: AdminResumenResponse): AdminKpi[] {
  const {
    inscripciones,
    pagos,
    cupos,
    equipos,
    participantes,
    acreditaciones,
    accesos,
  } = resumen;

  const rutaInscripciones = "/administracion/inscripciones";
  const rutaPagos = "/administracion/pagos";
  const rutaParticipantes = "/administracion/participantes";
  const rutaEquipos = "/administracion/equipos";
  const rutaAcreditaciones = "/administracion/acreditaciones";

  return [
    {
      id: "inscripciones",
      label: "Inscripciones",
      value: formatearNumero(inscripciones.total),
      rawValue: inscripciones.total,
      hint: `${inscripciones.creadas_ultimos_7_dias} creadas en los últimos 7 días`,
      tone: "brand",
      ruta: rutaInscripciones,
    },
    {
      id: "pagos",
      label: "Monto pagado",
      value: formatearMonto(pagos.monto_pagado),
      rawValue: pagos.monto_pagado,
      hint: `${pagos.compras_pagadas} pagadas · ${pagos.compras_pendientes} pendientes`,
      tone: "emerald",
      ruta: rutaPagos,
    },
    {
      id: "cupos",
      label: "Cupos pagados",
      value: formatearNumero(cupos.pagado),
      rawValue: cupos.pagado,
      hint: `${cupos.disponible_pagado} disponibles · ${cupos.asignado_activo} asignados`,
      tone: "cyan",
      ruta: rutaParticipantes,
    },
    {
      id: "equipos",
      label: "Equipos",
      value: formatearNumero(equipos.total),
      rawValue: equipos.total,
      hint: `${equipos.completos} completos · ${equipos.incompletos} incompletos`,
      tone: "violet",
      ruta: rutaEquipos,
    },
    {
      id: "participantes",
      label: "Participantes",
      value: formatearNumero(participantes.personas_distintas),
      rawValue: participantes.personas_distintas,
      hint: `${participantes.participaciones_activas} participaciones · ${participantes.en_pool} en pool`,
      tone: "orange",
      ruta: rutaParticipantes,
    },
    {
      id: "acreditaciones",
      label: "Acreditaciones",
      value: formatearNumero(acreditaciones.total),
      rawValue: acreditaciones.total,
      hint: `${acreditaciones.con_acceso_fiesta} con acceso · ${acreditaciones.bloqueadas_por_admin} bloqueadas`,
      tone: "slate",
      ruta: rutaAcreditaciones,
    },
    {
      id: "accesos",
      label: "Accesos",
      value: formatearNumero(accesos.permitidos),
      rawValue: accesos.permitidos,
      hint: `${accesos.denegados} denegados`,
      tone: "rose",
      ruta: `${rutaAcreditaciones}?tab=accesos`,
    },
  ];
}

/**
 * The routes of the alerts that CAN be expressed as a filter.
 *
 * The parameter names are the REAL ones the backend accepts and they respect
 * the namespaces of the lists (`participantes_`): a link with a parameter the
 * endpoint ignores opens a list that is NOT filtered, which is worse than no
 * link at all.
 *
 * | Alert                 | Parameter (real)                     |
 * |-----------------------|--------------------------------------|
 * | inscripción por estado| `estado` (namespace raíz, A3)        |
 * | compras pendientes    | `estado_compra` (namespace raíz, A5) |
 * | órdenes vencidas      | `estado_orden` (namespace raíz, A5)  |
 * | pool de participantes  | `estado_pool` (ns `participantes_`)  |
 * | roster incompleto     | `roster` (namespace raíz, A7)         |
 */
const RUTA_INSCRIPCIONES = "/administracion/inscripciones";
const RUTA_PAGOS = "/administracion/pagos";
const RUTA_PARTICIPANTES = "/administracion/participantes";
const RUTA_EQUIPOS = "/administracion/equipos";

/** Namespace of the parameters of the people list (A8). */
const NS_PARTICIPANTES = "participantes_";

/**
 * The four attention lists of the overview.
 *
 * Only items with a positive count are listed: a zero is not an alert. A
 * group without items is dropped entirely instead of showing an empty card.
 */
export function resumenAlertas(
  resumen: AdminResumenResponse,
): AdminAlertGroup[] {
  const grupos: AdminAlertGroup[] = [];

  const estadosRevision = ["RECIBIDA", "EN_REVISION", "OBSERVADA"];

  const itemsInscripciones = estadosRevision
    .map((estado) => ({
      id: `inscripcion-${estado}`,
      label: estadoInscripcionLabel(estado),
      value: resumen.inscripciones.por_estado[estado] ?? 0,
      detail: "Requieren la revisión del comité",
      tone: estadoInscripcionTone(estado),
      ruta: `${RUTA_INSCRIPCIONES}?estado=${estado}`,
    }))
    .filter((item) => item.value > 0);

  if (itemsInscripciones.length > 0) {
    grupos.push({
      id: "inscripciones",
      title: "Inscripciones por revisar",
      description: "Estados que todavía no fueron validados por el comité.",
      items: itemsInscripciones,
    });
  }

  const itemsPagos = [
    {
      id: "compras-pendientes",
      label: "Compras pendientes de pago",
      value: resumen.pagos.compras_pendientes,
      detail: "Sin confirmar el pago",
      tone: "amber" as AdminTone,
      ruta: `${RUTA_PAGOS}?estado_compra=PENDIENTE`,
    },
    {
      id: "ordenes-vencidas",
      label: "Órdenes de pago vencidas",
      value: resumen.pagos.ordenes_vencidas,
      detail: "El plazo de pago ya terminó",
      tone: "rose" as AdminTone,
      ruta: `${RUTA_PAGOS}?estado_orden=VENCIDA`,
    },
    {
      // The backend does NOT expose a filter for the liquidation of a
      // purchase: an alert without a filter stays plain text.
      id: "compras-sin-liquidar",
      label: "Compras pagadas sin liquidar",
      value: resumen.pagos.compras_pagadas_sin_liquidar,
      detail: "El pago existe pero la compra sigue pendiente",
      tone: "orange" as AdminTone,
    },
  ].filter((item) => item.value > 0);

  if (itemsPagos.length > 0) {
    grupos.push({
      id: "pagos",
      title: "Pagos por resolver",
      description: "Compras y órdenes de pago con la operación detenida.",
      items: itemsPagos,
    });
  }

  const itemsCupos = [
    {
      id: "cupos-sin-asignar",
      label: "Cupos pagados sin asignar",
      value: resumen.cupos.disponible_pagado,
      detail: "Capacidad pagada que aún no tiene persona",
      tone: "blue" as AdminTone,
      ruta: `${RUTA_PARTICIPANTES}?${NS_PARTICIPANTES}estado_pool=CUPO_POR_ASIGNAR`,
    },
    {
      // The exhausted capacity counts REGISTRATIONS and the people list
      // counts PEOPLE: there is no filter that expresses it.
      id: "capacidad-exhaustada",
      label: "Inscripciones sin capacidad pagada",
      value: resumen.cupos.inscripciones_con_capacidad_exhaustada,
      detail: "Requieren una ampliación de cupos",
      tone: "orange" as AdminTone,
    },
    {
      id: "participantes-sin-cupo",
      label: "Participantes sin cupo activo",
      value: resumen.participantes.sin_cupo_activo,
      detail: "No pueden asignarse a un equipo todavía",
      tone: "amber" as AdminTone,
      ruta: `${RUTA_PARTICIPANTES}?${NS_PARTICIPANTES}estado_pool=SIN_CAPACIDAD`,
    },
  ].filter((item) => item.value > 0);

  if (itemsCupos.length > 0) {
    grupos.push({
      id: "cupos",
      title: "Cupos por asignar",
      description: "Capacidad pagada y participantes sin cupo vigente.",
      items: itemsCupos,
    });
  }

  const itemsEquipos = [
    {
      id: "equipos-incompletos",
      label: "Equipos con roster incompleto",
      value: resumen.equipos.incompletos,
      detail: "No alcanzan el mínimo deportivo",
      tone: "amber" as AdminTone,
      ruta: `${RUTA_EQUIPOS}?roster=INCOMPLETO`,
    },
    {
      id: "participantes-en-pool",
      label: "Participantes en pool",
      value: resumen.participantes.en_pool,
      detail: "Pre-registrados sin equipo asignado",
      tone: "blue" as AdminTone,
      ruta: `${RUTA_PARTICIPANTES}?${NS_PARTICIPANTES}estado_pool=LISTO`,
    },
  ].filter((item) => item.value > 0);

  if (itemsEquipos.length > 0) {
    grupos.push({
      id: "equipos",
      title: "Equipos por completar",
      description: "Rosters incompletos y personas sin equipo.",
      items: itemsEquipos,
    });
  }

  return grupos;
}
