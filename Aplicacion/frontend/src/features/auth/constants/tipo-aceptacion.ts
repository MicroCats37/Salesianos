import { z } from "zod";

/**
 * TipoAceptacion — literal types for accepted document categories.
 * These are shared across all acceptance-related fields in the app.
 */
export const TIPO_ACEPTACION = {
  BASES: "BASES",
  APTITUD_FISICA: "APTITUD_FISICA",
  IMAGEN: "IMAGEN",
} as const;

export type TipoAceptacion = (typeof TIPO_ACEPTACION)[keyof typeof TIPO_ACEPTACION];

/**
 * TipoDocumento — document type identifiers used in registration.
 */
export const TIPO_DOCUMENTO = {
  DNI: "DNI",
  CE: "CE",
  PAS: "PAS",
} as const;

export type TipoDocumento = (typeof TIPO_DOCUMENTO)[keyof typeof TIPO_DOCUMENTO];

/**
 * Genero — gender identifiers used in registration.
 */
export const GENERO = {
  M: "M",
  F: "F",
} as const;

export type Genero = (typeof GENERO)[keyof typeof GENERO];
