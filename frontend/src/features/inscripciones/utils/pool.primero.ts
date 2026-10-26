/**
 * Pool-first UX mapping — pure, dependency-free.
 *
 * The participant lifecycle has ONE entry point: the pool. The UI therefore
 * needs a single, honest vocabulary:
 *
 * 1. "Agregar participante" — the CTA that opens the preregistration.
 * 2. "asigna desde el selector" — the only way to place somebody in a team.
 *
 * The copy lives here (and not inline in the components) so the header CTA,
 * the empty state, the empty team card and the empty selector cannot drift
 * apart. The module has no runtime dependency, so the mapping can be verified
 * deterministically.
 */

/** Where the primary pool CTA is rendered. */
export type PoolCtaContexto = "cabecera" | "vacio";

/** The primary pool CTA (label + supporting copy). */
export interface PoolCta {
  /** Button label. */
  label: string;
  /** Supporting copy shown next to / under the CTA. */
  description: string;
}

/** A guidance block that points the responsable to the pool. */
export interface PoolGuia {
  /** Short statement of the situation. */
  titulo: string;
  /** The next safe action. */
  descripcion: string;
}

/**
 * The primary pool CTA.
 *
 * The label never mentions a team: registering a participant and placing them
 * in a team are two different operations, and the CTA only does the first.
 */
export function poolCtaDe(contexto: PoolCtaContexto): PoolCta {
  if (contexto === "vacio") {
    return {
      label: "Agregar el primer participante",
      description:
        "Registra a la persona en el pool. Cuando tenga un cupo pagado podrás asignarla a un equipo con el selector.",
    };
  }
  return {
    label: "Agregar participante",
    description:
      "Registra a la persona en el pool y asígnala a un equipo con el selector.",
  };
}

/**
 * Guidance for a team without participants.
 *
 * It states the two steps in order (pool first, selector second) so the
 * responsable never looks for a "create player in this team" action.
 */
export function poolGuiaEquipoVacio(): PoolGuia {
  return {
    titulo: "Este equipo todavía no tiene participantes.",
    descripcion:
      "Primero pre-registra a la persona en el pool con «Agregar participante» y luego asígnala desde el selector de este equipo.",
  };
}

/**
 * Guidance for the selector when there is no eligible candidate.
 *
 * It replaces the removed "Registrar nuevo participante" button: the selector
 * only ASSIGNS, the pool REGISTERS.
 */
export function poolGuiaSelectorVacio(): PoolGuia {
  return {
    titulo: "No hay participantes que puedan unirse a este equipo.",
    descripcion:
      "Registra a la persona en el pool con «Agregar participante» y vuelve a abrir el selector para asignarla.",
  };
}
