"use client";

import { Settings2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Encuentro } from "../schemas";
import { CompetenciaAvanceDialog } from "./dialogs/CompetenciaAvanceDialog";
import { CompetenciaCorreccionDialog } from "./dialogs/CompetenciaCorreccionDialog";
import { CompetenciaResultadoDialog } from "./dialogs/CompetenciaResultadoDialog";
import { CompetenciaByeEditor } from "./editors/CompetenciaByeEditor";
import { CompetenciaEditorModal } from "./editors/CompetenciaEditorModal";
import { CompetenciaEnlaceEditor } from "./editors/CompetenciaEnlaceEditor";
import { CompetenciaProgramacionEditor } from "./editors/CompetenciaProgramacionEditor";

/** The actions that the administrator can apply to ONE encounter. */
type AccionEncuentro =
  | "programar"
  | "bye"
  | "enlace"
  | "resultado"
  | "avance"
  | "correccion"
  | null;

/** The label of every action. */
const ACCIONES: { id: Exclude<AccionEncuentro, null>; etiqueta: string }[] = [
  { id: "programar", etiqueta: "Programar" },
  { id: "bye", etiqueta: "Bye manual" },
  { id: "enlace", etiqueta: "Enlace" },
  { id: "resultado", etiqueta: "Resultado" },
  { id: "avance", etiqueta: "Avance" },
  { id: "correccion", etiqueta: "Corregir ganador" },
];

export interface CompetenciasAccionesEncuentroProps {
  /** Identifier of the competition that owns the bracket. */
  competenciaId: string;
  /** The encounter that is being administered. */
  encuentro: Encuentro;
  /** The date of the competition: the schedule shares it. */
  fechaCompetencia: string;
}

/**
 * CompetenciasAccionesEncuentro — the administration of ONE encounter of the
 * bracket.
 *
 * The actions are collapsed by default so the bracket stays readable, and
 * every one of them opens ITS OWN dialog: the schedule, the manual bye, the
 * link, the result, the advance and the correction of the winner.
 *
 * Only ONE dialog is mounted at a time: the nested dialogs of Radix would
 * fight for the focus.
 */
export function CompetenciasAccionesEncuentro({
  competenciaId,
  encuentro,
  fechaCompetencia,
}: CompetenciasAccionesEncuentroProps) {
  const [accion, setAccion] = useState<AccionEncuentro>(null);
  const cerrar = () => setAccion(null);

  return (
    <>
      <details className="group">
        <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-[10px] font-black uppercase tracking-wider text-[#312e8e] hover:underline">
          <Settings2 className="size-3" aria-hidden="true" />
          Administrar
        </summary>

        <div className="mt-2 flex flex-wrap gap-1">
          {ACCIONES.map((opcion) => (
            <Button
              key={opcion.id}
              type="button"
              size="xs"
              variant="outline"
              onClick={() => setAccion(opcion.id)}
            >
              {opcion.etiqueta}
            </Button>
          ))}
        </div>
      </details>

      {accion === "programar" ? (
        <CompetenciaEditorModal
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          titulo="Programar encuentro"
          descripcion="El intervalo es positivo y comparte la fecha de la competencia."
        >
          <CompetenciaProgramacionEditor
            competenciaId={competenciaId}
            encuentro={encuentro}
            fechaCompetencia={fechaCompetencia}
          />
        </CompetenciaEditorModal>
      ) : null}

      {accion === "bye" ? (
        <CompetenciaEditorModal
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          titulo="Configurar bye manual"
          descripcion="El bye lo asigna el administrador: el sistema nunca lo elige."
        >
          <CompetenciaByeEditor
            competenciaId={competenciaId}
            encuentro={encuentro}
          />
        </CompetenciaEditorModal>
      ) : null}

      {accion === "enlace" ? (
        <CompetenciaEditorModal
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          titulo="Enlazar con el siguiente encuentro"
          descripcion="El enlace y su slot se escriben juntos y siempre apuntan a una ronda posterior."
        >
          <CompetenciaEnlaceEditor
            competenciaId={competenciaId}
            encuentro={encuentro}
          />
        </CompetenciaEditorModal>
      ) : null}

      {accion === "resultado" ? (
        <CompetenciaResultadoDialog
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          competenciaId={competenciaId}
          encuentro={encuentro}
        />
      ) : null}

      {accion === "avance" ? (
        <CompetenciaAvanceDialog
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          competenciaId={competenciaId}
          encuentro={encuentro}
        />
      ) : null}

      {accion === "correccion" ? (
        <CompetenciaCorreccionDialog
          open
          onOpenChange={(abierto) => {
            if (!abierto) cerrar();
          }}
          competenciaId={competenciaId}
          encuentro={encuentro}
        />
      ) : null}
    </>
  );
}
