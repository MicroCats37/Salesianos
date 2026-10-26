"use client";

import { useState } from "react";

export interface EnvioEditor<TDatos> {
  /** Send the data of the form and remember it for a possible retry. */
  enviar: (datos: TDatos) => Promise<void>;
  /** Send again the last data, with the CURRENT version of the entity. */
  reintentar: () => Promise<void>;
  /** Whether there is something to retry. */
  hayEnvio: boolean;
}

/**
 * useEnvioEditor — the submission of ONE editor of the module.
 *
 * The editor remembers the LAST data that the administrator sent, but it
 * NEVER remembers the optimistic lock: the retry always travels with the
 * version that the server has right now, so a conflict (409
 * `RESOURCE_CHANGED`) can be retried after the data was refreshed.
 *
 * The payload itself is built by the mutation hook, never here
 * (`contract/next-app-architecture-contract.md` §5).
 */
export function useEnvioEditor<TDatos>(
  enviarDatos: (datos: TDatos) => Promise<unknown>,
): EnvioEditor<TDatos> {
  const [ultimosDatos, setUltimosDatos] = useState<TDatos | null>(null);

  return {
    enviar: async (datos: TDatos) => {
      setUltimosDatos(datos);
      await enviarDatos(datos);
    },
    reintentar: async () => {
      if (ultimosDatos === null) return;
      await enviarDatos(ultimosDatos);
    },
    hayEnvio: ultimosDatos !== null,
  };
}
