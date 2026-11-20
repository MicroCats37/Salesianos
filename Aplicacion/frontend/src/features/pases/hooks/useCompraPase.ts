"use client";

import { useApiCreate } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { compraPaseCreadaEnvelope } from "../schemas/pase.schema";
import { rutaCompras } from "../services/pase.service";
import { paseClaves } from "../utils/pase.claves.utils";
import {
  aPayloadComprarPase,
  type SolicitudCompraPase,
} from "../utils/pase.payload.utils";

/**
 * The purchase of a batch of passes (`RT-CM-02`).
 *
 * The mutation is CREATE-ONLY: the payload is the whole validated shape of
 * `ComprarPaseIn`, never an update diff. It is BUILT HERE, in the mutation,
 * and not in the component: the component never spells a field of the wire.
 *
 * **The invalidation lives INSIDE the mutation**, not in `onSettled`: a
 * component that unmounts while the request is in flight would never
 * invalidate, and the cache would keep the old answer (`FND-08` §3 regla 5).
 *
 * It declares the purchases namespace and NOTHING else: a purchase does not
 * change the catalogue of passes, and the browser never decides the price,
 * the availability or the state of the batch.
 */
export function useCompraPase() {
  const mutacion = useApiCreate({
    url: rutaCompras(),
    schema: datosDelEnvelope(compraPaseCreadaEnvelope),
    invalidateKeys: [paseClaves.compras()],
  });

  return {
    ...mutacion,
    mutateAsync: (solicitud: SolicitudCompraPase) =>
      mutacion.mutateAsync(aPayloadComprarPase(solicitud)),
  };
}
