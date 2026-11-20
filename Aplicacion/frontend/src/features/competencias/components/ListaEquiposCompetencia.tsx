import { Swords } from "lucide-react";
import {
  AdminDataTable,
  AdminEmptyState,
} from "@/features/admin/components";
import { ChipEstadoCompetencia } from "./ChipEstadoCompetencia";
import { estadoEquipoCompetencia } from "../utils/competencias.estados.utils";
import type { CompetenciaEquipo } from "../types/competencia.types";

/**
 * ListaEquiposCompetencia - the teams of a competition (`ADM-11`).
 *
 * The seed is MANUAL and the retirement is not a deletion: a withdrawn team
 * keeps its history (`RN-K02`). The table says both without hiding either.
 */
export function ListaEquiposCompetencia({
  equipos,
}: {
  equipos: CompetenciaEquipo[];
}) {
  if (equipos.length === 0) {
    return (
      <AdminEmptyState
        icon={Swords}
        title="Todavía no hay equipos en esta competencia"
        description="El alta de equipos es manual: el sistema nunca siembra un cuadro por su cuenta. Añade un equipo elegible de la misma disciplina y dale su semilla."
      />
    );
  }

  return (
    <AdminDataTable
      caption="Equipos de la competencia"
      columns={[
        { key: "equipo", label: "Equipo" },
        { key: "orden", label: "Semilla", numerico: true },
        { key: "estado", label: "Estado" },
        { key: "version", label: "Versión", numerico: true },
      ]}
      filas={equipos.map((equipo) => ({
        cells: {
          equipo: (
            <span className="font-medium text-foreground">
              {equipo.equipo_nombre}
            </span>
          ),
          orden: String(equipo.orden),
          estado: (
            <ChipEstadoCompetencia
              estado={estadoEquipoCompetencia(equipo.estado)}
            />
          ),
          version: String(equipo.version),
        },
      }))}
    />
  );
}
