import { z } from "zod";

/**
 * The exact mirror of the catalogue of the TARGET backend.
 *
 * Backend: `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/catalogo_schemas.py`
 * (packet DOM-01, freeze `FREEZE-PS-1.0.0`).
 *
 * Rules of the mirror (contract/api-wrapper-presenter-contract.md §7):
 *
 * - ONE field per field of the wrapper, with the SAME name and the SAME
 *   optionality. Nothing is added, nothing is dropped.
 * - No `z.any()`, no generic fields, no fields of another domain.
 * - The answer that does not match the mirror is a FAILURE, never a partially
 *   trusted value: the mirror parses LOUDLY.
 *
 * ## The money is a STRING
 *
 * `PrecioOut.monto` is a `Decimal` on the server. The wire shape is a JSON
 * STRING, and the reason is the chain that every answer of the target goes
 * through:
 *
 * 1. `core/responses.py::success_response` serialises the presenter with
 *    `model_dump(mode="json")`, and Pydantic v2 serialises a `Decimal` in JSON
 *    mode as a string.
 * 2. `ninja/operation.py::_result_to_response` re-validates the envelope
 *    against the declared response model and dumps it in the DEFAULT
 *    ("python") mode, so the `Decimal` survives as a `Decimal`.
 * 3. `ninja/responses.py::NinjaJSONEncoder` extends Django's
 *    `DjangoJSONEncoder`, whose `default()` renders a `Decimal` with
 *    `str(o)`.
 *
 * So the browser receives `"750.00"` and NEVER a number. The frontend prints
 * the amount exactly as it arrives: it never parses, sums nor formats money
 * (`RN-C02`).
 */
export const precioSchema = z.object({
  /** The amount of the catalogue, as the server sends it. */
  monto: z.string(),
  /** The ISO-4217 code of the currency. */
  moneda: z.string(),
  /** The start of the validity, as `YYYY-MM-DD`. */
  vigente_desde: z.string(),
  /** The end of the validity. `null` means an open validity. */
  vigente_hasta: z.string().nullable(),
});

export type Precio = z.infer<typeof precioSchema>;

/**
 * A benefit that a package OFFERS (`RN-P01`).
 *
 * The module DECLARES the benefit; it does not distribute it (`PD-09`). The
 * quantity is the declared one, never a sum computed in the browser.
 */
export const beneficioSchema = z.object({
  codigo: z.string(),
  nombre: z.string(),
  /** `FIJO_INICIAL` or `POR_CUPO`: the vocabulary the backend closes. */
  tipo: z.string(),
  cantidad: z.number().int().positive(),
});

export type Beneficio = z.infer<typeof beneficioSchema>;

/** A discipline of the edition (mirrors `DisciplinaOut`). */
export const disciplinaSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  nombre: z.string(),
  /** The identifier of the discipline. The backend publishes no `sigla`. */
  slug: z.string(),
  /** `ACTIVA` or `INACTIVA`. */
  estado: z.string(),
  /** `MIXTO`, `FEMENINO` or `MASCULINO`. */
  modalidad: z.string(),
  minimo_por_equipo: z.number().int().positive(),
  maximo_por_equipo: z.number().int().positive(),
});

export type Disciplina = z.infer<typeof disciplinaSchema>;

/** A package of the edition (mirrors `PaqueteOut`). */
export const paqueteSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  nombre: z.string(),
  slug: z.string(),
  descripcion: z.string(),
  /** `VIGENTE` or `RETIRADO`. */
  estado: z.string(),
  /** The cupos the package grants. Declared by the catalogue. */
  cupos_incluidos: z.number().int().positive(),
  precio: precioSchema,
  beneficios: z.array(beneficioSchema),
  disciplinas: z.array(disciplinaSchema),
});

export type Paquete = z.infer<typeof paqueteSchema>;

/** The catalogue of packages of ONE edition (mirrors `CatalogoPaquetesOut`). */
export const catalogoPaquetesSchema = z.object({
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  paquetes: z.array(paqueteSchema),
});

export type CatalogoPaquetes = z.infer<typeof catalogoPaquetesSchema>;

/** The catalogue of disciplines of ONE edition (mirrors `CatalogoDisciplinasOut`). */
export const catalogoDisciplinasSchema = z.object({
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  disciplinas: z.array(disciplinaSchema),
});

export type CatalogoDisciplinas = z.infer<typeof catalogoDisciplinasSchema>;
