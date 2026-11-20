import { ScrollText } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { AdminDataTable, AdminEmptyState } from "@/features/admin/components";
import type { RegistroValidacion } from "../types/validacion.types";
import { CODIGOS_VALIDACION } from "../utils/validaciones.estados.utils";
import { formatearInstante } from "../utils/validaciones.fecha.utils";
import { ChipVeredictoValidacion } from "./ChipVeredictoValidacion";

/**
 * FiltrosAuditoria - the filters of the audit (`ADM-22`).
 *
 * The bar is a NATIVE GET form: the filters live in the URL, they survive a
 * reload and they work without JavaScript.
 *
 * Only the filters whose VOCABULARY is frozen are offered here: the verdict,
 * whose codes come from the ledger of `RT-RT-01` and `RT-RT-02`. The other
 * dimensions of the brief — ticket, person, purchase, type of right, date,
 * operator and point — need the parameter names of `RT-VA-01`, and that
 * route is still PROVISIONAL: they are owed to API-05 with its ratification
 * (`A0-UI05-02`, re-raised as `A0-API05-02`).
 */
export function FiltrosAuditoria({
  veredicto,
  accion,
}: {
  /** The verdict filter of the URL, if there is one. */
  veredicto?: string;
  /** The route the form submits to. */
  accion: string;
}) {
  return (
    <form
      method="get"
      action={accion}
      className="flex flex-wrap items-end gap-3"
      aria-label="Filtros de la auditoría de validaciones"
    >
      <div className="flex min-w-56 flex-col gap-1">
        <label
          htmlFor="filtro-veredicto-validacion"
          className="text-caption text-muted-foreground"
        >
          Resultado de la validación
        </label>
        <select
          id="filtro-veredicto-validacion"
          name="veredicto"
          defaultValue={veredicto ?? ""}
          className="min-h-11 rounded-[var(--radius-md)] border border-border bg-surface-raised px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
        >
          <option value="">Todos los resultados</option>
          {Object.entries(CODIGOS_VALIDACION).map(([codigo, etiqueta]) => (
            <option key={codigo} value={codigo}>
              {etiqueta}
            </option>
          ))}
        </select>
      </div>

      <Button type="submit" className="min-h-11">
        Filtrar
      </Button>

      {veredicto ? (
        <Button variant="outline" asChild className="min-h-11">
          <Link href={accion}>Quitar el filtro</Link>
        </Button>
      ) : null}
    </form>
  );
}

/**
 * TablaAuditoriaValidaciones - the audit of the edition (`ADM-22`).
 *
 * The audit is TRANSVERSAL: it lists the entries AND the pickups of the
 * store, and it never mixes them with a payment confirmation
 * (`GOV-02-RB-08c`).
 *
 * The record exposes the ACTOR, the INSTANT, the RESULT and the POINT as
 * TEXT: the verdict is never a colour-only trail (`RB-08` ADM-22). Below 768
 * the row becomes a card with the same four facts; from 768 it is a table
 * with the priority columns.
 */
export function TablaAuditoriaValidaciones({
  registros,
  filtroVeredicto,
  accion,
}: {
  registros: RegistroValidacion[];
  /** The verdict filter of the URL, if there is one. */
  filtroVeredicto?: string;
  /** The route of the filters. */
  accion: string;
}) {
  if (registros.length === 0) {
    return filtroVeredicto ? (
      <AdminEmptyState
        icon={ScrollText}
        title="No hay validaciones con ese resultado"
        description="Hay asientos en la auditoría, pero ninguno con el resultado que has filtrado. Quita el filtro para verlos todos."
        action={
          <Button variant="outline" asChild className="min-h-11">
            <Link href={accion}>Quitar el filtro</Link>
          </Button>
        }
      />
    ) : (
      <AdminEmptyState
        icon={ScrollText}
        title="Todavía no hay asientos en la auditoría"
        description="El servicio de auditoría de validaciones todavía no está disponible en el backend, así que aquí no se dibuja ningún asiento. Cuando lo esté, se listarán los ingresos a la fiesta y las recogidas de la tienda con su resultado, su punto de control y su responsable."
      />
    );
  }

  return (
    <>
      <ul className="flex flex-col gap-3 md:hidden">
        {registros.map((registro) => {
          const instante = formatearInstante(registro.instante);
          return (
            <li
              key={registro.id}
              className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-surface-raised p-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <ChipVeredictoValidacion veredicto={registro.veredicto} />
                <span className="rounded-full border border-border bg-surface-recessed px-2 py-0.5 text-caption text-muted-foreground">
                  {registro.tipo === "ENTRADA" ? "Ingreso" : "Recogida"}
                </span>
              </div>
              <p className="text-sm font-semibold text-foreground">
                {[registro.titular.nombres, registro.titular.apellidos]
                  .filter(Boolean)
                  .join(" ")}
              </p>
              <p className="text-caption text-muted-foreground">
                {registro.punto} · {registro.operador}
              </p>
              {instante ? (
                <p className="text-caption text-muted-foreground">
                  <time dateTime={registro.instante}>{instante}</time>
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>

      <div className="hidden md:block">
        <AdminDataTable
          caption="Auditoría de ingresos y recogidas"
          columns={[
            { key: "instante", label: "Momento" },
            { key: "tipo", label: "Tipo" },
            { key: "veredicto", label: "Resultado" },
            { key: "persona", label: "Persona" },
            { key: "referencia", label: "Referencia" },
            { key: "punto", label: "Punto de control" },
            { key: "operador", label: "Operador" },
            { key: "cantidad", label: "Unidades", numerico: true },
          ]}
          filas={registros.map((registro) => {
            const instante = formatearInstante(registro.instante);
            return {
              cells: {
                instante: instante ? (
                  <time dateTime={registro.instante} className="tabular-nums">
                    {instante}
                  </time>
                ) : (
                  "—"
                ),
                tipo: (
                  <span className="text-muted-foreground">
                    {registro.tipo === "ENTRADA" ? "Ingreso" : "Recogida"}
                  </span>
                ),
                veredicto: (
                  <ChipVeredictoValidacion veredicto={registro.veredicto} />
                ),
                persona: (
                  <span className="font-medium text-foreground">
                    {[registro.titular.nombres, registro.titular.apellidos]
                      .filter(Boolean)
                      .join(" ")}
                  </span>
                ),
                referencia: (
                  <span className="font-mono text-xs text-muted-foreground">
                    {registro.referencia}
                  </span>
                ),
                punto: (
                  <span className="text-muted-foreground">
                    {registro.punto}
                  </span>
                ),
                operador: (
                  <span className="text-muted-foreground">
                    {registro.operador}
                  </span>
                ),
                cantidad: String(registro.cantidad),
              },
            };
          })}
        />
      </div>
    </>
  );
}
