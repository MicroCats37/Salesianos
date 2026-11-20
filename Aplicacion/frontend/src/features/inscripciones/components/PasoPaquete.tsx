"use client";

import { TriangleAlert } from "lucide-react";
import { useFormContext, useWatch } from "react-hook-form";
import { RouteEmptyState } from "@/components/shell/RouteEmptyState";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { AltaInscripcionFormData } from "../schemas/alta-inscripcion.schema";
import type { PaqueteCatalogo } from "../types/inscripcion.types";
import { PaqueteCard } from "./PaqueteCard";

export interface PasoPaqueteProps {
  /** The packages of the catalogue, as the server publishes them. */
  paquetes: readonly PaqueteCatalogo[];
  /** Whether the catalogue is still travelling. */
  cargando: boolean;
  /** The message of a recoverable failure, verbatim from the server. */
  error: string | null;
  /** The action that asks for the catalogue again. */
  onReintentar?: () => void;
}

/**
 * PasoPaquete - the first step of the wizard.
 *
 * The visitor chooses ONE package and nothing else. The card prints the
 * cupos the package grants and the price of the catalogue exactly as the
 * server sends them: the quantity of people and the total are NOT decided
 * here, they belong to the package and to the server (RN-C02).
 *
 * The catalogue is a REAL read of the server (RT-IN-12). While it travels
 * the step shows a skeleton with the geometry of the cards, and when it
 * fails the step says so and offers to ask again: it never falls back to an
 * invented catalogue.
 */
export function PasoPaquete(props: PasoPaqueteProps) {
  const paquetes = props.paquetes;
  const cargando = props.cargando;
  const error = props.error;
  const onReintentar = props.onReintentar;

  const contexto = useFormContext<AltaInscripcionFormData>();
  const registro = contexto.register;

  const observacionPaquete = {
    control: contexto.control,
    name: "paquete_id" as const,
  };
  const paqueteId = useWatch(observacionPaquete);

  if (cargando) {
    return (
      <div className="flex flex-col gap-3" aria-busy="true">
        <span className="sr-only">Cargando los paquetes disponibles</span>
        {[0, 1].map((indice) => (
          <div
            key={indice}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4"
          >
            <Skeleton className="h-4 w-2/5" />
            <Skeleton className="h-3 w-4/5" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-destructive/45 bg-destructive/10">
        <TriangleAlert className="size-4 text-destructive" aria-hidden="true" />
        <AlertTitle className="text-foreground">
          No pudimos leer los paquetes
        </AlertTitle>
        <AlertDescription className="text-muted-foreground">{error}</AlertDescription>
        {onReintentar ? (
          <div className="pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onReintentar}
              className="min-h-11"
            >
              Reintentar
            </Button>
          </div>
        ) : null}
      </Alert>
    );
  }

  if (paquetes.length === 0) {
    return (
      <RouteEmptyState
        icon={TriangleAlert}
        title="No hay paquetes disponibles en esta edición"
        description="El catálogo no publica ningún paquete con precio vigente. Cuando la edición abra su venta, los paquetes aparecerán aquí."
      />
    );
  }

  return (
    <fieldset className="flex flex-col gap-4">
      <legend className="text-sm font-semibold text-foreground">
        Elige el paquete que se contrata
      </legend>

      <div className="flex flex-col gap-3">
        {paquetes.map((paquete) => (
          <PaqueteCard
            key={paquete.id}
            paquete={paquete}
            seleccionado={paquete.id === paqueteId}
            registro={registro("paquete_id")}
          />
        ))}
      </div>
    </fieldset>
  );
}
