"use client";

import { TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { handleApiError } from "@/errors";
import { useRetirarParticipante } from "../hooks";
import type {
  EquipoInscripcion,
  ParticipacionPool,
} from "../types/inscripcion.types";
import { FormularioParticipante } from "./FormularioParticipante";
import { PanelParticipantes } from "./PanelParticipantes";

export interface SeccionParticipantesProps {
  /** The registration that owns the pool. */
  inscripcionId: string;
  /** The teams of the registration. */
  equipos: readonly EquipoInscripcion[];
  /** The participations of the pool, as the server publishes them. */
  participaciones: readonly ParticipacionPool[];
}

/**
 * SeccionParticipantes - the people of the pool and their management.
 *
 * The section owns the TWO writes of the pool (`RT-IN-05` and `RT-IN-06`):
 * the assignment of a person and the withdrawal of a participation.
 *
 * The withdrawal is IRREVERSIBLE in the sense that matters to the operator
 * (S-10): it frees the cupo of THAT registration, it does NOT cancel the
 * purchase, it does NOT return money and it does NOT touch the inventory
 * (`RN-I04`, `DEC-06`). The confirmation says exactly that before the
 * action happens.
 *
 * The answer of the server is the UPDATED pool, so the balance on the screen
 * is the one of the server and never a number computed in the browser
 * (`RN-I03`).
 */
export function SeccionParticipantes(props: SeccionParticipantesProps) {
  const retirar = useRetirarParticipante();

  const [pendiente, setPendiente] = useState<ParticipacionPool | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function confirmarRetiro() {
    if (!pendiente) return;

    setMensaje(null);

    try {
      await retirar.mutateAsync({
        inscripcion_id: props.inscripcionId,
        participacion_id: pendiente.id,
      });
    } catch (error) {
      setMensaje(handleApiError(error).message);
    } finally {
      setPendiente(null);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {mensaje ? (
        <Alert className="border-destructive/45 bg-destructive/10">
          <TriangleAlert
            className="size-4 text-destructive"
            aria-hidden="true"
          />
          <AlertTitle className="text-foreground">
            No pudimos retirar a la persona
          </AlertTitle>
          <AlertDescription className="text-muted-foreground">
            {mensaje}
          </AlertDescription>
        </Alert>
      ) : null}

      <PanelParticipantes
        participaciones={props.participaciones}
        onRetirar={(participacion) => {
          setMensaje(null);
          setPendiente(participacion);
        }}
      />

      <FormularioParticipante
        inscripcionId={props.inscripcionId}
        equipos={props.equipos}
      />

      <AlertDialog
        open={pendiente !== null}
        onOpenChange={(abierto) => {
          if (!abierto) setPendiente(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Retirar a esta persona del equipo
            </AlertDialogTitle>
            <AlertDialogDescription>
              Se libera su cupo en esta inscripción. La compra no se cancela, no
              se devuelve dinero y el inventario no cambia.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={retirar.isPending}
              onClick={() => void confirmarRetiro()}
            >
              Retirar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
