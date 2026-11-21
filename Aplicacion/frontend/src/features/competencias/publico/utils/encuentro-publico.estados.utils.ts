/**
 * The vocabulary of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * Every label of this file is a 1:1 mirror of a backend `TextChoices`: the
 * code AND its wording come from
 * `Aplicacion/backend/modules/competencias/domain/constants.py`
 * (`EstadoEncuentroPublico`). Nothing here is invented and nothing here is a
 * rule: the module publishes the code, the client resolves the wording and
 * never the other way round.
 *
 * A code that is NOT in the dictionary is NOT guessed: it falls back to the
 * code itself, so an unknown public state is visible instead of silently
 * painted as something it is not.
 */

/** `EstadoEncuentroPublico` — the three buckets the backend publishes. */
export const ESTADOS_PUBLICO_ENCUENTRO: Readonly<Record<string, string>> = {
  PROGRAMA: "Programado",
  EN_VIVO: "En vivo",
  FINALIZADO: "Finalizado",
};

/**
 * The wording of a public state.
 *
 * A code outside the dictionary keeps ITS OWN text: an unknown state is
 * shown, never hidden and never guessed.
 */
export function etiquetaEstadoPublico(codigo: string): string {
  return ESTADOS_PUBLICO_ENCUENTRO[codigo] ?? codigo;
}
