"use client";

import { useState } from "react";
import { UserMinus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AdminEmptyState } from "@/features/admin/components";
import { CifrasCupos, ListaOperativa } from "@/features/admin/operaciones";
import type { ColumnaOperativa, FilaOperativa } from "@/features/admin/operaciones";
import type {
  ParticipanteDeEquipoOut,
  PoolDeInscripcionOut,
} from "../types/inscripciones-admin.types";
import { DialogoRetirarParticipante } from "./DialogoRetirarParticipante";

const COLUMNAS: ColumnaOperativa[] = [
  { key: "persona", label: "Persona", prioridad: 1, titular: true },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "equipo", label: "Equipo", prioridad: 2 },
  { key: "rol", label: "Rol", prioridad: 2 },
  { key: "accion", label: "Acción", prioridad: 2 },
];

/**
 * A person of the roster, with the team she belongs to.
 */
export interface PersonaDelPool {
  participante: ParticipanteDeEquipoOut;
  equipo: string;
}

/**
 * PanelPoolInscripcion - the tab «Pool y personas» of the detail.
 *
 * It shows the THREE cupos, the CAUSES that prevent widening the roster and
 * the people of the roster with their state. The causes are the `mensaje` of
 * the backend, printed verbatim: the browser never decides why a person
 * cannot enter (`D-UI02-01`).
 *
 * The roster comes from the administrative presenter, which publishes the
 * name and the document of every person; the pool of the responsible only
 * publishes the counts and the causes.
 *
 * The withdrawal is the S-10 action of the route. It opens a confirmation
 * that names the effect and asks for the reason, and the confirmation itself
 * says that the action is not connected yet.
 */
export function PanelPoolInscripcion({
  pool,
  personas,
  inscripcionId,
}: {
  pool: PoolDeInscripcionOut;
  personas: readonly PersonaDelPool[];
  /** The registration that owns the pool. It travels to the S-10 command. */
  inscripcionId?: string;
}) {
  const [participacionRetirada, setParticipacionRetirada] = useState<
    string | null
  >(null);

  const filas: FilaOperativa[] = personas.map(({ participante, equipo }) => ({
    id: participante.id,
    celdas: {
      persona: (
        <span className="flex flex-col">
          <span className="font-semibold text-foreground">
            {participante.nombre}
          </span>
          <span className="text-xs text-foreground-muted">
            {participante.documento}
          </span>
        </span>
      ),
      estado: participante.estado,
      equipo,
      rol: participante.rol,
      accion: (
        <Button
          variant="outline"
          size="sm"
          className="min-h-11"
          onClick={() => setParticipacionRetirada(participante.id)}
        >
          <UserMinus className="size-4" aria-hidden="true" />
          Retirar
        </Button>
      ),
    },
  }));

  const retirada = personas.find(
    ({ participante }) => participante.id === participacionRetirada,
  );

  return (
    <div className="flex flex-col gap-4">
      <CifrasCupos
        cupos={{
          adquiridos: pool.cupos_pagados,
          asignados: pool.cupos_asignados,
          disponibles: pool.cupos_disponibles,
        }}
      />

      {pool.impedimentos.length > 0 ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold text-foreground">
            Causas que impiden ampliar la plantilla
          </h3>
          <ul className="flex list-none flex-col gap-2">
            {pool.impedimentos.map((impedimento) => (
              <li
                key={impedimento.codigo}
                className="rounded-[var(--radius-md)] border border-border bg-surface-recessed/60 px-3 py-2 text-sm leading-snug text-foreground"
              >
                {impedimento.mensaje}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <ListaOperativa
        caption="Personas del pool de la inscripción"
        columnas={COLUMNAS}
        filas={filas}
        vacio={
          <AdminEmptyState
            icon={Users}
            title="Todavía no hay personas en el pool"
            description="Las participaciones se leen del pool de la inscripción. Cuando el servicio esté disponible, aquí se listarán las personas con su equipo, su rol y el estado de su participación."
          />
        }
      />

      <DialogoRetirarParticipante
        abierto={participacionRetirada !== null}
        onAbiertoChange={(abierto) => {
          if (!abierto) setParticipacionRetirada(null);
        }}
        nombreParticipante={retirada?.participante.nombre ?? "la persona"}
        inscripcionId={inscripcionId}
        participacionId={retirada?.participante.id}
      />
    </div>
  );
}
