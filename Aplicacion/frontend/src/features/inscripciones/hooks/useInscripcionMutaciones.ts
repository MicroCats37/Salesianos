"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  invalidateDatasets,
  updateCachedDetail,
} from "@/shared/utils/cache-policy";
import type { Respuesta } from "../services/respuesta.service";
import type {
  CompraCreada,
  ComprarCuposIn,
} from "../schemas/compra-cupos.schema";
import type {
  InscripcionInicial,
  InscripcionInicialIn,
} from "../schemas/inscripcion.schema";
import type { ParticipanteAsignarIn, Pool } from "../schemas/pool.schema";
import {
  agregarParticipante,
  comprarCupos,
  crearInscripcionInicial,
  retirarParticipante,
} from "../services/inscripcion.service";
import {
  clavesInscripcionDetalle,
  clavesInscripcionPool,
} from "../utils/inscripcion.claves.utils";

/**
 * The writes of the registration area.
 *
 * Every mutation declares the reads it dirties, and the invalidation lives
 * INSIDE the `mutationFn` (not in `onSettled`): a component that unmounts
 * while the mutation is in flight would never invalidate, and the cache
 * would keep the old answer (FND-08, rule 5).
 *
 * The invalidation happens when the mutation SETTLES, and not only when it
 * succeeds: a 409 means that ANOTHER actor changed the same registration, and
 * the reads have to be refreshed even though this mutation wrote nothing.
 *
 * ## Write or invalidate
 *
 * A write into the cache is only allowed when the answer of the mutation
 * HAS the exact shape of the cached read:
 *
 * - adding, moving or withdrawing a participant answer with the UPDATED
 *   `PoolOut`, so the pool is written into its entry (only when the entry
 *   already exists: a read that nobody made is not created);
 * - the purchase of extra cupos answers with `CompraCreadaOut`, which is NOT
 *   a pool, so the pool and the detail are INVALIDATED instead of written;
 * - the alta answers with `InscripcionInicialOut`, whose inscription is new,
 *   so the detail is INVALIDATED instead of written: the cache must not
 *   create the entry of a registration that nobody read.
 *
 * The browser NEVER computes the new balance: it writes what the server
 * answered or it invalidates. It never subtracts cupos and never derives an
 * eligibility (`RN-I03`, `RN-C02`).
 */

/**
 * The alta of a registration and of its PENDING purchase (`RT-IN-14`).
 *
 * The retry does not create a second inscription: the server answers with the
 * inscription that already exists and with its pending purchase
 * (`FR-04` I-4). The failure propagates the ORIGINAL error so that the 422
 * field errors reach the control that owns the field.
 */
export function useAltaInscripcion() {
  const queryClient = useQueryClient();

  return useMutation<Respuesta<InscripcionInicial>, unknown, InscripcionInicialIn>({
    mutationFn: async (payload) => {
      try {
        return await crearInscripcionInicial(payload);
      } finally {
        await invalidateDatasets(queryClient, [clavesInscripcionDetalle.all]);
      }
    },
  });
}

/** The arguments of the assignment (or movement) of a participant. */
export interface AsignarParticipanteArgs {
  /** The registration that owns the pool. */
  inscripcion_id: string;
  /** The payload of the assignment. */
  payload: ParticipanteAsignarIn;
}

/**
 * Adds a participant to the pool, or MOVES one (`RT-IN-05`).
 *
 * The answer is the UPDATED pool: the exact shape is preserved, so it is
 * written into the entry of the pool when that entry already exists.
 */
export function useAgregarParticipante() {
  const queryClient = useQueryClient();

  return useMutation<Respuesta<Pool>, unknown, AsignarParticipanteArgs>({
    mutationFn: async (args) => {
      try {
        const respuesta = await agregarParticipante(
          args.inscripcion_id,
          args.payload,
        );

        updateCachedDetail(
          queryClient,
          clavesInscripcionPool.detail(args.inscripcion_id),
          () => respuesta.data,
        );

        return respuesta;
      } finally {
        await invalidateDatasets(queryClient, [
          clavesInscripcionDetalle.detail(args.inscripcion_id),
        ]);
      }
    },
  });
}

/** The arguments of the withdrawal of a participant. */
export interface RetirarParticipanteArgs {
  /** The registration that owns the pool. */
  inscripcion_id: string;
  /** The participation that is withdrawn. */
  participacion_id: string;
}

/**
 * Withdraws a participant and frees its cupo (`RT-IN-06`).
 *
 * Withdrawing frees the cupo of THAT registration and does not cancel the
 * purchase, does not return money and does not touch the inventory
 * (`RN-I04`, `DEC-06`). The answer is the UPDATED pool.
 */
export function useRetirarParticipante() {
  const queryClient = useQueryClient();

  return useMutation<Respuesta<Pool>, unknown, RetirarParticipanteArgs>({
    mutationFn: async (args) => {
      try {
        const respuesta = await retirarParticipante(
          args.inscripcion_id,
          args.participacion_id,
        );

        updateCachedDetail(
          queryClient,
          clavesInscripcionPool.detail(args.inscripcion_id),
          () => respuesta.data,
        );

        return respuesta;
      } finally {
        await invalidateDatasets(queryClient, [
          clavesInscripcionDetalle.detail(args.inscripcion_id),
        ]);
      }
    },
  });
}

/** The arguments of the purchase of extra cupos. */
export interface ComprarCuposArgs {
  /** The registration that is amplified. */
  inscripcion_id: string;
  /** The payload of the purchase. */
  payload: ComprarCuposIn;
}

/**
 * The purchase of EXTRA cupos of a registration (`RT-CM-01`).
 *
 * The answer is `CompraCreadaOut`: it carries the capacity of the
 * registration but NOT the participations nor the impediments, so the exact
 * shape of the pool cannot be preserved and both reads are invalidated.
 *
 * The cupos that were just bought are NOT paid: the capacity only changes
 * when the payment is activated (`RN-I02`).
 */
export function useCompraCupos() {
  const queryClient = useQueryClient();

  return useMutation<Respuesta<CompraCreada>, unknown, ComprarCuposArgs>({
    mutationFn: async (args) => {
      try {
        return await comprarCupos(args.inscripcion_id, args.payload);
      } finally {
        await invalidateDatasets(queryClient, [
          clavesInscripcionPool.detail(args.inscripcion_id),
          clavesInscripcionDetalle.detail(args.inscripcion_id),
        ]);
      }
    },
  });
}
