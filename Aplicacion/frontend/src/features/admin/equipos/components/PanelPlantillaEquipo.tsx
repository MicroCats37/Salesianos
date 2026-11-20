"use client";

import { UserMinus, UsersRound } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { AdminEmptyState } from "@/features/admin/components";
import { DialogoRetirarParticipante } from "@/features/admin/inscripciones/components/DialogoRetirarParticipante";
import type {
  ColumnaOperativa,
  FilaOperativa,
} from "@/features/admin/operaciones";
import { ListaOperativa } from "@/features/admin/operaciones";
import type { ParticipanteDeEquipoOut } from "../types/equipos-admin.types";

const COLUMNAS: ColumnaOperativa[] = [
  { key: "persona", label: "Persona", prioridad: 1, titular: true },
  { key: "documento", label: "Documento", prioridad: 1 },
  { key: "estado", label: "Estado", prioridad: 1 },
  { key: "rol", label: "Rol", prioridad: 2 },
  { key: "accion", label: "Acción", prioridad: 2 },
];

/**
 * PanelPlantillaEquipo - the roster of a team.
 *
 * It shows the people of the team with their DOCUMENT and their state, which
 * is what `frontend/04` §5 asks for.
 *
 * ## The withdrawal is a HISTORICAL withdrawal
 *
 * The row action asks for the audited reason and the command is the one of
 * the backend: the participation goes to `RETIRADA` and frees its cupo. The
 * `Persona` is NOT deleted and the historical participations are NOT erased:
 * the padrón is intocable from here.
 */
export function PanelPlantillaEquipo({
  participantes,
  inscripcionId,
}: {
  participantes: readonly ParticipanteDeEquipoOut[];
  /** The registration the team belongs to: the withdrawal is scoped to it. */
  inscripcionId: string;
}) {
  const [retirada, setRetirada] = useState<string | null>(null);

  const filas: FilaOperativa[] = participantes.map((participante) => ({
    id: participante.id,
    celdas: {
      persona: participante.nombre,
      documento: participante.documento,
      estado: participante.estado,
      rol: participante.rol,
      accion: (
        <Button
          variant="outline"
          size="sm"
          className="min-h-11"
          onClick={() => setRetirada(participante.id)}
        >
          <UserMinus className="size-4" aria-hidden="true" />
          Retirar
        </Button>
      ),
    },
  }));

  const participanteRetirado = participantes.find((p) => p.id === retirada);

  return (
    <div className="flex flex-col gap-4">
      <ListaOperativa
        caption="Nómina del equipo"
        columnas={COLUMNAS}
        filas={filas}
        vacio={
          <AdminEmptyState
            icon={UsersRound}
            title="Sin plantilla en este equipo"
            description="Un equipo sin plantilla no puede competir. Agrega a las personas que ya están en el padrón identificándolas por su documento exacto."
          />
        }
      />

      <DialogoRetirarParticipante
        abierto={retirada !== null}
        onAbiertoChange={(abierto) => {
          if (!abierto) setRetirada(null);
        }}
        nombreParticipante={participanteRetirado?.nombre ?? "esta persona"}
        inscripcionId={inscripcionId}
        participacionId={retirada ?? undefined}
      />
    </div>
  );
}
