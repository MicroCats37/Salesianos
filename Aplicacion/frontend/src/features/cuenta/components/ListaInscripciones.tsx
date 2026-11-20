import { ArrowRight, Users } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemGroup,
  ItemHeader,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { InscripcionResumen } from "../types/cuenta.types";
import { VeredictoEstado } from "./VeredictoEstado";

export interface ListaInscripcionesProps {
  /** The registrations to list. */
  inscripciones: InscripcionResumen[];
  className?: string;
}

/**
 * The sentence that carries the cupos.
 *
 * RB-01 ACCOUNT-02: the figure is read in a sentence, never as three
 * separate numerals. The sentence is built from the numbers the presenter
 * sent; no capacity is computed here.
 */
function fraseCupos(inscripcion: InscripcionResumen) {
  const cupos = inscripcion.cupos_disponibles;
  const personas = inscripcion.personas;

  if (cupos === 0) {
    return `No quedan cupos disponibles. ${personas} ${personas === 1 ? "persona inscrita" : "personas inscritas"}.`;
  }

  return `Quedan ${cupos} ${cupos === 1 ? "cupo disponible" : "cupos disponibles"}. ${personas} ${personas === 1 ? "persona inscrita" : "personas inscritas"}.`;
}

/**
 * ListaInscripciones - the registrations of the responsible.
 *
 * A LIST, not a grid of cards: the responsible reads her own registrations
 * one after the other and compares them, and a row compares better than a
 * tile.
 *
 * The table appears at 1024 and the labelled cards below it (SH-02 2.2):
 * at 360 a table of five columns is unreadable, and a row whose meaning is
 * only in the header is a row nobody understands.
 */
export function ListaInscripciones({
  inscripciones,
  className,
}: ListaInscripcionesProps) {
  return (
    <div className={className}>
      {/* Cards below 1024: every value carries its own label. */}
      <ItemGroup className="gap-3 lg:hidden">
        {inscripciones.map((inscripcion) => (
          <Item
            key={inscripcion.id}
            variant="outline"
            role="listitem"
            className="flex-col items-stretch gap-3"
          >
            <ItemHeader>
              <ItemMedia variant="icon">
                <Users className="size-4 text-primary" aria-hidden="true" />
              </ItemMedia>
              <ItemContent>
                <ItemTitle className="text-foreground">
                  {inscripcion.edicion}
                </ItemTitle>
                <ItemDescription>{inscripcion.paquete}</ItemDescription>
              </ItemContent>
              <ItemActions>
                <VeredictoEstado veredicto={inscripcion.veredicto} />
              </ItemActions>
            </ItemHeader>

            <p className="text-caption text-muted-foreground">
              {fraseCupos(inscripcion)} Equipos: {inscripcion.equipos}.
            </p>

            {inscripcion.siguiente_accion ? (
              <Button asChild className="min-h-11 w-full">
                <Link href={inscripcion.siguiente_accion.href}>
                  {inscripcion.siguiente_accion.etiqueta}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
            ) : null}
          </Item>
        ))}
      </ItemGroup>

      {/* Table from 1024: the columns are prioritised, nothing is clipped. */}
      <div className="hidden lg:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Registro</TableHead>
              <TableHead scope="col">Estado</TableHead>
              <TableHead scope="col">Plantilla</TableHead>
              <TableHead scope="col">Cupos</TableHead>
              <TableHead scope="col">Siguiente paso</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inscripciones.map((inscripcion) => (
              <TableRow key={inscripcion.id}>
                <TableCell>
                  <div className="flex flex-col gap-0.5">
                    <span className="font-semibold text-foreground">
                      {inscripcion.edicion}
                    </span>
                    <span className="text-caption text-muted-foreground">
                      {inscripcion.paquete}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <VeredictoEstado veredicto={inscripcion.veredicto} />
                </TableCell>
                <TableCell>
                  <span className="tabular-nums">{inscripcion.equipos}</span>{" "}
                  {inscripcion.equipos === 1 ? "equipo" : "equipos"} ·{" "}
                  <span className="tabular-nums">{inscripcion.personas}</span>{" "}
                  {inscripcion.personas === 1 ? "persona" : "personas"}
                </TableCell>
                <TableCell>
                  <span className="tabular-nums font-semibold text-foreground">
                    {inscripcion.cupos_disponibles}
                  </span>
                  <span className="sr-only">. {fraseCupos(inscripcion)}</span>
                </TableCell>
                <TableCell>
                  {inscripcion.siguiente_accion ? (
                    <Button asChild variant="outline" size="sm" className="min-h-11">
                      <Link href={inscripcion.siguiente_accion.href}>
                        {inscripcion.siguiente_accion.etiqueta}
                        <ArrowRight className="size-4" aria-hidden="true" />
                      </Link>
                    </Button>
                  ) : (
                    <span className="text-caption text-muted-foreground">
                      No hay un paso pendiente
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
