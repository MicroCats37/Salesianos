"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { consultarDocumento } from "../services/identidad.service";

export interface DocumentoLookupData {
  tipo_documento: string;
  numero_documento: string;
  /** The full name exactly as the external source publishes it. */
  nombre_completo: string;
  nombres: string;
  apellidos: string;
}

function splitNombreCompleto(nombreCompleto: string): {
  nombres: string;
  apellidos: string;
} {
  if (!nombreCompleto) return { nombres: "", apellidos: "" };

  const trimmed = nombreCompleto.replace(/\s+/g, " ").trim();

  const sepIndex = trimmed.indexOf(",");
  if (sepIndex !== -1) {
    const apellidos = trimmed.slice(0, sepIndex).trim();
    const nombres = trimmed.slice(sepIndex + 1).trim();
    return { nombres, apellidos };
  }

  const tokens = trimmed.split(" ").filter(Boolean);
  if (tokens.length <= 3) {
    if (tokens.length === 1) return { nombres: tokens[0], apellidos: "" };
    if (tokens.length === 2) {
      return { nombres: tokens[1], apellidos: tokens[0] };
    }
    return {
      nombres: `${tokens[2]} ${tokens[1]}`.trim(),
      apellidos: tokens[0],
    };
  }

  const apellidos = tokens.slice(0, 2).join(" ");
  const nombres = tokens.slice(2).join(" ");
  return { nombres, apellidos };
}

/**
 * Consulta los datos de un DNI o RUC (`GET /personas/busqueda/{documento}`).
 *
 * Devuelve `{ tipo_documento, numero_documento, nombre_completo, nombres,
 * apellidos }`.
 * Para un DNI, `nombre_completo` viene como "APELLIDOS, NOMBRES".
 *
 * The service is the ONE owner of the route `RT-ID-01` and it parses the
 * answer with the exact mirror of `DocumentoConsultaOut`: an answer that does
 * not match the presenter is a failure, never a partially trusted value.
 */
export function useDocumentoLookup() {
  return useMutation<DocumentoLookupData, Error, string>({
    mutationFn: async (documento: string) => {
      const res = await consultarDocumento(documento);
      const { nombres, apellidos } = splitNombreCompleto(res.nombre_completo ?? "");
      return { ...res, nombres, apellidos };
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al consultar el documento",
      );
    },
  });
}
