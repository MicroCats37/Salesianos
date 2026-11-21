import { ErrorAdmin } from "@/features/admin/operaciones/services/admin.service";
import { erroresDeCampoDeError } from "@/features/admin/operaciones/utils/admin.estado.utils";

/**
 * How a failure of the ADMINISTRATIVE ASSISTED commands becomes a state of
 * the form.
 *
 * ## The rule that decides the branch
 *
 * The interface branches on the HTTP STATUS and on the STABLE CODE of the
 * failure, and NEVER on the prose: the catalogue of public codes is not
 * closed (`contract/api-wrapper-presenter-contract.md` §8).
 *
 * | The failure | What the form does |
 * |---|---|
 * | `409 PRECIO_CAMBIADO` | the price moved since the quotation: the quotation is dropped and asked again |
 * | `422` with field errors | each error reaches the control that owns it |
 * | any other failure | the public prose of the server, printed verbatim |
 */

/** The code the server publishes when the price moved since the quotation. */
export const CODIGO_PRECIO_CAMBIADO = "PRECIO_CAMBIADO";

/**
 * The controls of the form of the assisted purchase.
 *
 * The server publishes the DOTTED path of the field (`evidencia.referencia`,
 * `cliente.numero_documento`), and the form of the assisted purchase has ONE
 * evidence block and ONE identity block: the control that owns the error is
 * the LAST segment of the path.
 *
 * A path whose last segment is not a control of this form (`pase_id`,
 * `evidencia.precio_version`) is a FORM-level error: it is never invented
 * onto a control that does not exist.
 */
const CONTROLES_DE_LA_COMPRA = new Set([
  "tipo_documento",
  "numero_documento",
  "nombres",
  "apellidos",
  "genero",
  "contacto_email",
  "cantidad",
  "canal",
  "referencia",
  "motivo",
  "monto_declarado",
]);

/**
 * Whether the failure is the `409` that says the price moved.
 *
 * It is the ONLY failure that changes the state of the form: the quotation
 * belongs to a price that no longer exists, so it is dropped and asked again
 * instead of being retried blindly.
 */
export function esPrecioCambiado(error: unknown): boolean {
  return (
    error instanceof ErrorAdmin &&
    error.status === 409 &&
    error.codigo === CODIGO_PRECIO_CAMBIADO
  );
}

/**
 * The control of the form that owns a field error of the server.
 *
 * `null` when the path belongs to a field that this form does not draw: the
 * error stays a form-level error.
 */
export function controlDeErrorDeCampo(campo: string): string | null {
  const segmentos = campo.split(".");
  const ultimo = segmentos[segmentos.length - 1];

  if (!ultimo || !CONTROLES_DE_LA_COMPRA.has(ultimo)) return null;

  return ultimo;
}

/**
 * The field errors of a failure, mapped onto the controls of the form.
 *
 * Only the FROZEN channel travels (`error.field_errors[]`): the administration
 * area answers in the frozen envelope.
 */
export function erroresDeCampoDeLaCompra(
  error: unknown,
): Record<string, string> {
  const errores: Record<string, string> = {};

  for (const [campo, mensaje] of Object.entries(erroresDeCampoDeError(error))) {
    const control = controlDeErrorDeCampo(campo);

    if (!control) continue;

    errores[control] = mensaje;
  }

  return errores;
}
