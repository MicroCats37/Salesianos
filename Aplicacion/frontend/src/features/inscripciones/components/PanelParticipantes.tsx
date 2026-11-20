"use client";

import { UserRound } from "lucide-react";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ParticipacionPool } from "../types/inscripcion.types";

export interface PanelParticipantesProps {
  /** The participations of the pool, exactly as the server publishes them. */
  participaciones: readonly ParticipacionPool[];
  /**
   * The action that withdraws a participation.
   *
   * It is ABSENT when the route does not own the write (the section is then
   * a pure reading). When it is present, the section owns the S-10
   * confirmation of the withdrawal.
   */
  onRetirar?: (participacion: ParticipacionPool) => void;
}

/**
 * PanelParticipantes - the people of the pool of a registration.
 *
 * The list is a semantic TABLE from 1024 and a labelled card list below it,
 * so the meaning survives every width without a horizontal scroll.
 *
 * The cupo state is read from the two facts the server publishes
 * (`ocupa_cupo` and `retirada_en`): the browser does not derive a verdict,
 * it phrases what the server already decided.
 */
export function PanelParticipantes(props: PanelParticipantesProps) {
  const participaciones = props.participaciones;
  const onRetirar = props.onRetirar;

  if (participaciones.length === 0) {
    return (
      <RouteEmptyState
        icon={UserRound}
        title="Todavía no hay personas en el pool"
        description="Las personas se asignan a los equipos cuando los cupos están pagados. Mientras el pago no se confirme, nadie ocupa un cupo."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="hidden lg:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Equipo</TableHead>
              <TableHead scope="col">Disciplina</TableHead>
              <TableHead scope="col">Rol</TableHead>
              <TableHead scope="col">Cupo</TableHead>
              {onRetirar ? <TableHead scope="col">Acción</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {participaciones.map((participacion) => (
              <TableRow key={participacion.id}>
                <TableCell className="font-medium text-foreground">
                  {participacion.equipo_nombre}
                </TableCell>
                <TableCell>{participacion.disciplina_nombre}</TableCell>
                <TableCell>{participacion.rol}</TableCell>
                <TableCell>
                  {participacion.retirada_en
                    ? "Retirada"
                    : participacion.ocupa_cupo
                      ? "Ocupando cupo"
                      : "Sin cupo"}
                </TableCell>
                {onRetirar ? (
                  <TableCell>
                    {participacion.retirada_en ? null : (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => onRetirar(participacion)}
                        className="min-h-11"
                      >
                        Retirar
                      </Button>
                    )}
                  </TableCell>
                ) : null}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <ul className="flex flex-col gap-3 lg:hidden">
        {participaciones.map((participacion) => (
          <li
            key={participacion.id}
            className="flex flex-col gap-1 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <span className="text-sm font-semibold text-foreground">
              {participacion.equipo_nombre}
            </span>
            <span className="text-caption text-muted-foreground">
              {participacion.disciplina_nombre}
            </span>
            <span className="text-caption text-muted-foreground">
              Rol: {participacion.rol}
            </span>
            <span className="text-caption text-muted-foreground">
              {participacion.retirada_en
                ? "Retirada"
                : participacion.ocupa_cupo
                  ? "Ocupando cupo"
                  : "Sin cupo"}
            </span>
            {onRetirar && !participacion.retirada_en ? (
              <Button
                type="button"
                variant="outline"
                onClick={() => onRetirar(participacion)}
                className="mt-2 min-h-11 self-start"
              >
                Retirar
              </Button>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
