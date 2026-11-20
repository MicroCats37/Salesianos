"use client";

import { useMutation } from "@tanstack/react-query";
import {
  confirmarTicket,
  previewTicket,
} from "../services/validacion.service";
import type { ConfirmarTicketDatos } from "../schemas/validacion.schema";

/**
 * The CHECK of a credential (`RT-RT-01`).
 *
 * It is a MUTATION and not a query: the credential is a secret that travels in
 * the body, and a cache would keep it in memory and could publish it in a
 * later request. The check does NOT consume (`RN-P06`).
 */
export function usePreviewTicket() {
  return useMutation({
    mutationFn: (codigo: string) => previewTicket(codigo),
  });
}

/**
 * The CONFIRMATION of a credential (`RT-RT-02`).
 *
 * The caller owns the `idempotency_key`: repeating the SAME key returns the
 * same record and never consumes twice (`FR-04` §2.2).
 */
export function useConfirmarTicket() {
  return useMutation({
    mutationFn: (datos: ConfirmarTicketDatos) => confirmarTicket(datos),
  });
}
