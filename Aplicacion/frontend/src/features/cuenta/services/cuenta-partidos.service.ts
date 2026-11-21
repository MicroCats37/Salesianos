import { apiSend } from "@/lib/api";
import type { CuentaPartidos } from "../schemas/cuenta-partidos.schema";
import { cuentaPartidosEnvelope } from "../schemas/cuenta-partidos.schema";

/**
 * The ONE client of the matches of the account.
 *
 * The route is the one REGISTERED by `MisPartidosController`
 * (`Aplicacion/backend/modules/competencias/presentation/controllers/mis_partidos_controller.py`):
 * a route that is not registered does not exist and is never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `GET /api/cuenta/mis-partidos` | GET | `/cuenta/mis-partidos` | `MisPartidosOut` |
 *
 * The route requires a SESSION and it does NOT accept any person, user or
 * team: the identity is the session's.
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the HTTP
 * client and of the rule that a `204` is never parsed.
 */

/** The route of the matches of the account. */
export const RUTA_PARTIDOS_CUENTA = "/cuenta/mis-partidos";

/**
 * The matches of the account, in their three buckets.
 *
 * An answer that does not comply with the mirror is a LOUD failure, never a
 * partially trusted value.
 */
export async function listarPartidosCuenta(): Promise<CuentaPartidos> {
  const { status, data } = await apiSend<unknown>("get", RUTA_PARTIDOS_CUENTA);

  if (status === 204) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new Error(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const envelope = cuentaPartidosEnvelope.parse(data);

  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? "No se pudieron obtener tus partidos.");
  }

  return envelope.data;
}
