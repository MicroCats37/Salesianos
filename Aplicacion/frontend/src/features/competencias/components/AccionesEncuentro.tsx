"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Encuentro } from "../types/competencia.types";
import {
  esConflictoDeVersion,
  mensajeDeError,
} from "../utils/competencias.errores.utils";
import { etiquetaAccion } from "../utils/competencias.estados.utils";
import { DialogoAvanceEncuentro } from "./DialogoAvanceEncuentro";
import { DialogoCorreccionEncuentro } from "./DialogoCorreccionEncuentro";
import { DialogoEnlaceEncuentro } from "./DialogoEnlaceEncuentro";
import { DialogoEstadoEncuentro } from "./DialogoEstadoEncuentro";
import { DialogoProgramacionEncuentro } from "./DialogoProgramacionEncuentro";
import { DialogoResultadoEncuentro } from "./DialogoResultadoEncuentro";

/**
 * The dialog that is open.
 *
 * The operator opens ONE thing at a time: the panel is small and the two
 * steps of the advance and of the correction live inside their own dialog.
 */
type DialogoAbierto =
  | "programacion"
  | "resultado"
  | "avance"
  | "correccion"
  | "enlace"
  | "iniciar"
  | "desprogramar"
  | "cancelar"
  | null;

/**
 * The actions that this surface offers, and the dialog of each one.
 *
 * They are a SUBSET of the actions the server advertises: the surface offers
 * what it can do HONESTLY, and the actions it does not offer are NAMED
 * below, never hidden.
 */
const DIALOGO_POR_ACCION: Record<string, DialogoAbierto> = {
  programar: "programacion",
  desprogramar: "desprogramar",
  iniciar: "iniciar",
  registrar_resultado: "resultado",
  avanzar: "avance",
  corregir: "correccion",
  enlazar: "enlace",
  cancelar: "cancelar",
};

export interface AccionesEncuentroProps {
  /** The encounter, in its canonical shape. */
  encuentro: Encuentro;
  /**
   * The encounters that can receive the winner.
   *
   * They are the encounters of the POSTERIOR rounds: the backend rejects a
   * link that points backwards (`RN-K02`). They travel as a PROP because the
   * panel is a presentational component: it never reads the cache by itself.
   */
  destinos?: readonly Encuentro[];
  /**
   * The conflict declared by the backend.
   *
   * A version conflict NEVER auto-applies: it informs, it offers a reload
   * and it leaves the decision to the operator (`RB-05` ADM-11).
   */
  onConflicto?: (mensaje: string) => void;
}

/**
 * AccionesEncuentro - the operator surface of ONE encounter.
 *
 * It offers ONLY the actions that the server advertises in `acciones`: the
 * transitions are NOT recreated in the browser, the backend is the authority
 * (`RN-A01`). An action that the server does not advertise is not a button.
 *
 * Every command carries the `expected_version` that the panel is drawing:
 * a write with an old version is rejected with `RESOURCE_CHANGED` and
 * nothing is written. The conflict is EXPLAINED and the data is reloaded
 * (the mutation invalidates the reads on settle), never retried a ciegas.
 */
export function AccionesEncuentro({
  encuentro,
  destinos = [],
  onConflicto,
}: AccionesEncuentroProps) {
  const [dialogo, setDialogo] = useState<DialogoAbierto>(null);

  const manejarError = (error: unknown) => {
    if (esConflictoDeVersion(error)) {
      onConflicto?.(mensajeDeError(error));
    }
  };

  const cerrar = () => setDialogo(null);

  const ofrecidas = encuentro.acciones.filter(
    (accion) => DIALOGO_POR_ACCION[accion] !== undefined,
  );

  /**
   * The actions the server admits and THIS surface does not offer.
   *
   * They are named, never hidden: the panel must not make the operator
   * believe that the backend refuses them (`RN-A01`).
   */
  const noOfrecidas = encuentro.acciones.filter(
    (accion) => DIALOGO_POR_ACCION[accion] === undefined,
  );

  return (
    <div className="flex flex-col gap-3">
      {encuentro.acciones.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          En este estado el servidor no admite cambios.
        </p>
      ) : null}
      {ofrecidas.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {ofrecidas.map((accion) => (
            <Button
              key={accion}
              type="button"
              variant="outline"
              className="min-h-11"
              onClick={() => setDialogo(DIALOGO_POR_ACCION[accion] ?? null)}
            >
              {etiquetaAccion(accion)}
            </Button>
          ))}
        </div>
      ) : null}
      {noOfrecidas.length > 0 ? (
        <div className="flex flex-col gap-1">
          <p className="text-caption text-muted-foreground">
            El servidor admite también
          </p>
          <ul className="flex flex-wrap gap-2">
            {noOfrecidas.map((accion) => (
              <li
                key={accion}
                className="rounded-full border border-border bg-surface-recessed px-2.5 py-1 text-xs text-foreground"
              >
                {etiquetaAccion(accion)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {/*
        Los diálogos se montan SÓLO cuando están abiertos: sus hooks de
        mutación necesitan el contexto de React Query y el panel es un
        componente PRESENTACIONAL (`GOV-02-RB-05a`).
      */}
      {dialogo === "programacion" ? (
        <DialogoProgramacionEncuentro
          encuentro={encuentro}
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("programacion") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "resultado" ? (
        <DialogoResultadoEncuentro
          encuentro={encuentro}
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("resultado") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "avance" ? (
        <DialogoAvanceEncuentro
          encuentro={encuentro}
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("avance") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "correccion" ? (
        <DialogoCorreccionEncuentro
          encuentro={encuentro}
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("correccion") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "enlace" ? (
        <DialogoEnlaceEncuentro
          encuentro={encuentro}
          destinos={destinos}
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("enlace") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "iniciar" ? (
        <DialogoEstadoEncuentro
          encuentro={encuentro}
          estado="EN_CURSO"
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("iniciar") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "desprogramar" ? (
        <DialogoEstadoEncuentro
          encuentro={encuentro}
          estado="BORRADOR"
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("desprogramar") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}
      {dialogo === "cancelar" ? (
        <DialogoEstadoEncuentro
          encuentro={encuentro}
          estado="CANCELADO"
          open
          onOpenChange={(abierto) =>
            abierto ? setDialogo("cancelar") : cerrar()
          }
          onError={manejarError}
        />
      ) : null}{" "}
    </div>
  );
}
