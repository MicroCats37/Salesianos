"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { consultarDocumento } from "../services/inscripcion.service";

export interface DocumentoLookupData {
  tipo_documento: string;
  numero_documento: string;
  razon_social: string;
  nombres: string;
  apellidos: string;
}

function splitRazonSocial(razonSocial: string): {
  nombres: string;
  apellidos: string;
} {
  if (!razonSocial) return { nombres: "", apellidos: "" };

  const trimmed = razonSocial.replace(/\s+/g, " ").trim();

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
 * Hook para consultar datos de un DNI/RUC en el servicio externo
 * (endpoint /personas/busqueda/{documento}).
 *
 * Devuelve `{ tipo_documento, numero_documento, razon_social, nombres, apellidos }`.
 * Para DNI, `razon_social` viene como "APELLIDOS, NOMBRES".
 */
export function useDocumentoLookup() {
  return useMutation<DocumentoLookupData, Error, string>({
    mutationFn: async (documento: string) => {
      const res = await consultarDocumento(documento);
      if (!res.success || !res.data) {
        throw new Error(
          res.error?.message ?? "No se encontraron datos para este documento",
        );
      }
      const { nombres, apellidos } = splitRazonSocial(
        res.data.razon_social ?? "",
      );
      return { ...res.data, nombres, apellidos };
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
