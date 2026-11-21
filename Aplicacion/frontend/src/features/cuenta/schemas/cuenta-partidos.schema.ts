import { z } from "zod";
import { encuentroPublicoSchema } from "@/features/competencias/publico/schemas/encuentro-publico.schema";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirror of the ACCOUNT read of the matches.
 *
 * Change: `partidos-marcadores-competencias` · Batch 3B
 *
 * It is a 1:1 mirror of `MisPartidosOut` (the backend wrapper published by
 * `MisPartidosController` on `GET /api/cuenta/mis-partidos`).
 *
 * ## The rules of the mirror
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The encounter is the SAME wire** that the competitions area publishes
 *   (`EncuentroPublicoOut`): the teams, the score, the EXPLICIT winner and the
 *   version. The account needs exactly those and none of the administrative
 *   affordances.
 * - **The winner is never derived from the score**: it travels as it was
 *   published.
 * - **The version travels** so that a future realtime event can be discarded
 *   when it is older than what the account already shows.
 */
export const cuentaEquipoSchema = z.object({
  id: z.string().min(1),
  equipo_id: z.string().min(1),
  equipo_nombre: z.string(),
  orden: z.number().int(),
  estado: z.string().min(1),
  version: z.number().int(),
});

/** The matches of the account (`MisPartidosOut`). */
export const cuentaPartidosSchema = z.object({
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  total: z.number().int(),
  equipos: z.array(cuentaEquipoSchema),
  en_vivo: z.array(encuentroPublicoSchema),
  proximos: z.array(encuentroPublicoSchema),
  finalizados: z.array(encuentroPublicoSchema),
});

/** The envelope of the read (`GET /api/cuenta/mis-partidos`). */
export const cuentaPartidosEnvelope = apiResponseSchema(cuentaPartidosSchema);

export type CuentaEquipo = z.infer<typeof cuentaEquipoSchema>;
export type CuentaPartidos = z.infer<typeof cuentaPartidosSchema>;
