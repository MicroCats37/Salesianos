"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import type { InscripcionDetalle } from "../schemas/inscripcion.schema";
import type { Pool } from "../schemas/pool.schema";
import {
  obtenerInscripcion,
  obtenerPool,
} from "../services/inscripcion.service";
import {
  clavesInscripcionDetalle,
  clavesInscripcionPool,
} from "../utils/inscripcion.claves.utils";
import { leerConEstado } from "../utils/inscripcion.errores.utils";

/**
 * The reads of ONE registration.
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the detail (with its teams) | `GET /inscripciones/{id}` (`RT-IN-02`) | `InscripcionDetalleOut` |
 * | the pool | `GET /inscripciones/{id}/pool` (`RT-IN-03`) | `PoolOut` |
 *
 * The teams travel inside the detail (`InscripcionDetalleOut.equipos`): they
 * have ONE owner in the cache. The route `GET /inscripciones/{id}/equipos`
 * (`RT-IN-04`) exists and is registered, but it is NOT bound here: binding
 * both would give the teams of a registration two sources of truth (FND-08,
 * rule 1).
 *
 * The detail and the pool are TRANSIENT data: the balance of the cupos
 * changes with every payment, every assignment and every movement, so their
 * staleness is the commercial one and they are invalidated by the mutations
 * that change them.
 *
 * The identifier of the registration travels in the key: two registrations
 * are two cache entries and never one.
 */

/** The detail of a registration and its balance of cupos. */
export function useInscripcionDetalle(inscripcionId: string | null) {
  return useQuery({
    ...datasetQueryOptions<InscripcionDetalle>({
      queryKey: clavesInscripcionDetalle.detail(inscripcionId ?? ""),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerInscripcion(inscripcionId ?? "");
          return respuesta.data;
        }),
      kind: "comercial",
    }),
    enabled: Boolean(inscripcionId),
  });
}

/**
 * The pool of cupos of a registration.
 *
 * The three counters and the impediments are the answer of the server
 * (`RN-I03`): the browser prints them and never subtracts them.
 */
export function useInscripcionPool(inscripcionId: string | null) {
  return useQuery({
    ...datasetQueryOptions<Pool>({
      queryKey: clavesInscripcionPool.detail(inscripcionId ?? ""),
      queryFn: () =>
        leerConEstado(async () => {
          const respuesta = await obtenerPool(inscripcionId ?? "");
          return respuesta.data;
        }),
      kind: "comercial",
    }),
    enabled: Boolean(inscripcionId),
  });
}
