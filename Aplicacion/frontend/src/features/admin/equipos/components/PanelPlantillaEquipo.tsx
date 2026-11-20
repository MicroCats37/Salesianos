"use client";

import { useState } from "react";
import { UserMinus, UsersRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AdminEmptyState } from "@/features/admin/components";
import {
  ConfirmacionIrreversible,
  ListaOperativa,
} from "@/features/admin/operaciones";
import type { ColumnaOperativa, FilaOperativa } from "@/features/admin/operaciones";
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
 * is what `frontend/04` §5 asks for. The withdrawal is the S-10 action of
 * the route: the confirmation names the effect and asks for the reason, and
 * it says that the action is not connected yet.
 */
export function PanelPlantillaEquipo({
  participantes,
}: {
  participantes: readonly ParticipanteDeEquipoOut[];
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
            description="Un equipo sin plantilla no puede competir. Cuando el detalle esté conectado, aquí se listarán las personas con su documento, su rol y su estado dentro del equipo."
          />
        }
      />

      <ConfirmacionIrreversible
        abierto={retirada !== null}
        onAbiertoChange={(abierto) => {
          if (!abierto) setRetirada(null);
        }}
        titulo={`Retirar a ${participanteRetirado?.nombre ?? "esta persona"} del equipo`}
        efecto="Retirar a la persona libera su cupo en la inscripción de este equipo; no genera devolución."
        motivo={{
          etiqueta: "Motivo de la retirada",
          placeholder: "Escribe el motivo que queda registrado en la auditoría.",
          requerido: true,
        }}
        confirmar={{
          etiqueta: "Retirar del equipo",
          deshabilitado: true,
        }}
      />
    </div>
  );
}
