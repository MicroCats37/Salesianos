/**
 * The vocabulary of the validation area.
 *
 * Two sources, and they are kept apart on purpose:
 *
 * - The ERROR CODES come from the frozen ledger
 *   (`evidence/contracts/route-to-wrapper-ledger.csv`, routes `RT-RT-01` and
 *   `RT-RT-02`): `TICKET_NO_ENCONTRADO`, `ACTION_NOT_ALLOWED`,
 *   `TICKET_YA_CONSUMIDO`, `CANTIDAD_EXCEDIDA`, `DERECHO_REVOCADO` and
 *   `IDEMPOTENCY_KEY_REUTILIZADA`.
 * - The STATES of the subjects come from the backend `TextChoices`:
 *   `EstadoDerechoPase` (`ACTIVO` / `REVOCADO`) of `DOM-03` and
 *   `EstadoEntregaPedido` (`PENDIENTE` / `ENTREGADO`) of `DOM-06`.
 *
 * The code of a SUCCESSFUL validation is NOT frozen: the module `validaciones`
 * does not exist in the target, so there is no presenter that publishes one.
 * `VALIDACION_PERMITIDA` is the PROVISIONAL code this frontend uses until
 * the backend ratifies it (`A0-UI05-02`, re-raised as `A0-API05-02`). A code outside the dictionary is
 * never guessed: it keeps its own text and falls into the `desconocido`
 * bucket, so an unknown verdict is visible instead of silently painted.
 */

import type {
  EstadoDeclarado,
  RolVeredictoValidacion,
  VeredictoValidacion,
} from "../types/validacion.types";

/** The wording of a code, or `null` when the code is not in the dictionary. */
type Diccionario = Readonly<Record<string, string>>;

/** The outcome codes of `RT-RT-01` and `RT-RT-02`. */
export const CODIGOS_VALIDACION: Diccionario = {
  VALIDACION_PERMITIDA: "Validación permitida",
  TICKET_NO_ENCONTRADO: "No existe ninguna entrada con ese código",
  ACTION_NOT_ALLOWED: "Esta acción no está permitida en este punto de control",
  TICKET_YA_CONSUMIDO: "Esta entrada ya se usó",
  CANTIDAD_EXCEDIDA: "No quedan unidades disponibles en esta entrada",
  DERECHO_REVOCADO: "Esta entrada está revocada",
  IDEMPOTENCY_KEY_REUTILIZADA: "Esta confirmación ya se había registrado",
};

/** `EstadoDerechoPase` — the state of a right of entry (`DOM-03`). */
export const ESTADOS_DERECHO: Diccionario = {
  ACTIVO: "Activo",
  REVOCADO: "Revocado",
};

/** `EstadoEntregaPedido` — the state of the delivery of an order (`DOM-06`). */
export const ESTADOS_ENTREGA: Diccionario = {
  PENDIENTE: "Pendiente",
  ENTREGADO: "Entregado",
};

/** `EstadoPedido` — the state of the order itself (`DOM-06`). */
export const ESTADOS_PEDIDO: Diccionario = {
  PENDIENTE: "Pendiente",
  PAGADO: "Pagado",
  CANCELADO: "Cancelado",
};

/**
 * The buckets that paint each outcome.
 *
 * The bucket is PRESENTATIONAL: it says how the chip is painted, never what
 * the outcome means (`SH-01` §3.2).
 */
const BOLES: Readonly<Record<string, RolVeredictoValidacion>> = {
  VALIDACION_PERMITIDA: "permitido",
  TICKET_NO_ENCONTRADO: "denegado",
  ACTION_NOT_ALLOWED: "denegado",
  TICKET_YA_CONSUMIDO: "consumido",
  CANTIDAD_EXCEDIDA: "excedido",
  DERECHO_REVOCADO: "revocado",
  IDEMPOTENCY_KEY_REUTILIZADA: "parcial",
};

/**
 * Resolve a code into the verdict that travels with its label.
 *
 * The label is the wording the backend published when it published one, and
 * the wording of the frozen codes otherwise. The client NEVER rewrites the
 * wording the server chose (`SH-03` §6).
 */
export function resolverVeredicto(
  codigo: string,
  etiqueta?: string,
): VeredictoValidacion {
  const estado: EstadoDeclarado = {
    codigo,
    etiqueta: etiqueta ?? CODIGOS_VALIDACION[codigo] ?? codigo,
  };
  return { estado, rol: BOLES[codigo] ?? "desconocido" };
}

/** Resolve the state of a right of entry. */
export function estadoDerecho(codigo: string): EstadoDeclarado {
  return { codigo, etiqueta: ESTADOS_DERECHO[codigo] ?? codigo };
}

/** Resolve the state of the delivery of an order. */
export function estadoEntrega(codigo: string): EstadoDeclarado {
  return { codigo, etiqueta: ESTADOS_ENTREGA[codigo] ?? codigo };
}

/** Resolve the state of an order. */
export function estadoPedido(codigo: string): EstadoDeclarado {
  return { codigo, etiqueta: ESTADOS_PEDIDO[codigo] ?? codigo };
}
