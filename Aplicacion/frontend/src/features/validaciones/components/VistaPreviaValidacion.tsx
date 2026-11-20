import { Eye } from "lucide-react";
import { ChipVeredictoValidacion } from "./ChipVeredictoValidacion";
import { estadoDerecho } from "../utils/validaciones.estados.utils";
import { formatearInstante } from "../utils/validaciones.fecha.utils";
import type { VistaPreviaValidacion } from "../types/validacion.types";

/**
 * VistaPreviaValidacion - the reusable preview of the validation area.
 *
 * ONE component renders the preview of BOTH operations: the entry of the
 * party (`ADM-16`) and the pickup of the store (`ADM-20`). The two flows
 * share the PRESENTATION and nothing else: the subject they read is a right
 * of entry in one case and a paid order in the other.
 *
 * The preview NEVER consumes. Its title says so, in the interface and not
 * only in the documentation, and the confirm is a separate action with its
 * own state (`GOV-02-RB-05b`).
 *
 * When the backend refuses, the panel shows the reason IT published and does
 * not offer the confirmation: the client never decides that a credential can
 * be consumed.
 */
export function VistaPreviaValidacion({
  vistaPrevia,
  titulo = "Vista previa de la validación",
}: {
  vistaPrevia: VistaPreviaValidacion;
  /** The title of the block, for the surface that owns it. */
  titulo?: string;
}) {
  const instante = formatearInstante(vistaPrevia.instante);
  const instantePrevio = vistaPrevia.consumo_previo
    ? formatearInstante(vistaPrevia.consumo_previo.instante)
    : null;

  const nombreTitular = [vistaPrevia.titular.nombres, vistaPrevia.titular.apellidos]
    .filter(Boolean)
    .join(" ");

  return (
    <section
      aria-label={titulo}
      className="flex flex-col gap-4 rounded-[var(--radius-md)] border border-border bg-surface-recessed p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Eye className="size-4 text-info" aria-hidden="true" />
          {titulo}
        </h3>
        <span className="rounded-full border border-border bg-surface-raised px-2 py-0.5 text-caption text-muted-foreground">
          Esta vista previa no consume nada
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <ChipVeredictoValidacion veredicto={vistaPrevia.veredicto} />
        <span className="text-caption text-muted-foreground">
          {vistaPrevia.puede_validar
            ? "El servidor admite la validación ahora."
            : "El servidor no admite la validación: no se ofrece confirmar."}
        </span>
      </div>

      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-[var(--radius-sm)] border border-border bg-surface-raised p-3">
          <dt className="text-caption text-muted-foreground">Persona</dt>
          <dd className="text-sm font-semibold text-foreground">
            {nombreTitular || "El backend no publicó un nombre"}
          </dd>
          <dd className="text-caption text-muted-foreground">
            {vistaPrevia.titular.tipo_documento}{" "}
            {vistaPrevia.titular.numero_documento}
          </dd>
        </div>

        <div className="rounded-[var(--radius-sm)] border border-border bg-surface-raised p-3">
          <dt className="text-caption text-muted-foreground">Derecho</dt>
          <dd className="text-sm font-semibold text-foreground">
            {vistaPrevia.derecho.nombre}
          </dd>
          <dd className="text-caption text-muted-foreground">
            {estadoDerecho(vistaPrevia.derecho.estado).etiqueta}
            {vistaPrevia.derecho.revocado_en
              ? ` · revocado el ${formatearInstante(vistaPrevia.derecho.revocado_en) ?? ""}`
              : ""}
          </dd>
        </div>

        <div className="rounded-[var(--radius-sm)] border border-border bg-surface-raised p-3">
          <dt className="text-caption text-muted-foreground">Unidades</dt>
          <dd className="text-sm font-semibold text-foreground tabular-nums">
            {vistaPrevia.derecho.cantidad_disponible} disponibles de{" "}
            {vistaPrevia.derecho.cantidad_total}
          </dd>
          <dd className="text-caption text-muted-foreground tabular-nums">
            {vistaPrevia.derecho.cantidad_consumida} ya canjeadas
          </dd>
        </div>

        <div className="rounded-[var(--radius-sm)] border border-border bg-surface-raised p-3">
          <dt className="text-caption text-muted-foreground">Dónde y cuándo</dt>
          <dd className="text-sm font-semibold text-foreground">
            {vistaPrevia.punto}
          </dd>
          <dd className="text-caption text-muted-foreground">
            {vistaPrevia.operador}
            {instante ? ` · ${instante}` : ""}
          </dd>
        </div>
      </dl>

      {vistaPrevia.consumo_previo ? (
        <div className="rounded-[var(--radius-sm)] border border-warning/45 bg-warning/10 p-3">
          <p className="text-sm font-semibold text-foreground">
            Esta credencial ya se había consumido
          </p>
          <p className="text-caption text-muted-foreground">
            {vistaPrevia.consumo_previo.punto} ·{" "}
            {vistaPrevia.consumo_previo.operador}
            {instantePrevio ? ` · ${instantePrevio}` : ""}
          </p>
        </div>
      ) : null}
    </section>
  );
}
