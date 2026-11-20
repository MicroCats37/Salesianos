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
  /**
   * The commercial minimum of the package: the number of cupos that a
   * purchase of this package starts from.
   *
   * It is the floor of the stepper of the wizard and the value the quantity
   * is INITIALIZED at. It is DECLARED by the catalogue, so the browser reads
   * it and never invents it (and never widens it).
   */
  minimo_compra_inicial: z.number().int().positive(),
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

/**
 * A cohort (mirrors `PromocionOut`).
 *
 * The cohort is the YEAR of a person, not a band: it is what the visitor
 * EXPLICITLY selects when the registration is created, and it is the only
 * input from which the server derives the competitive band.
 *
 * The cohort is a GLOBAL fact (it belongs to a person, not to an edition),
 * so it carries NO edition: the edition that scopes it is the one of the
 * wrapper of the catalogue.
 */
export const promocionSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  /** The year of the cohort. */
  anio: z.number().int(),
  /** The name the organisation gives to the cohort. */
  nombre: z.string(),
  /** `ACTIVA` or `INACTIVA`. */
  estado: z.string(),
});

export type Promocion = z.infer<typeof promocionSchema>;

/**
 * A competitive age band of ONE edition (mirrors `CategoriaOut`).
 *
 * The band is DECLARED by the catalogue with the range of cohorts it covers
 * (`promocion_desde` / `promocion_hasta`). The browser NEVER derives which
 * band a cohort belongs to: the server resolves it and publishes the band on
 * the team it creates (`RN-C02`, `QA-K01`).
 */
export const categoriaSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  /** The name of the band: `Junior`, `Senior`, `Máster`… */
  nombre: z.string(),
  /** The first year of the cohort range that the band covers. */
  promocion_desde: z.number().int(),
  /** The last year of the cohort range that the band covers. */
  promocion_hasta: z.number().int(),
  /** `ACTIVA` or `INACTIVA`. */
  estado: z.string(),
});

export type Categoria = z.infer<typeof categoriaSchema>;

/** The catalogue of cohorts of ONE edition (mirrors `CatalogoPromocionesOut`). */
export const catalogoPromocionesSchema = z.object({
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  promociones: z.array(promocionSchema),
});

export type CatalogoPromociones = z.infer<typeof catalogoPromocionesSchema>;

/** The catalogue of bands of ONE edition (mirrors `CatalogoCategoriasOut`). */
export const catalogoCategoriasSchema = z.object({
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  categorias: z.array(categoriaSchema),
});

export type CatalogoCategorias = z.infer<typeof catalogoCategoriasSchema>;
