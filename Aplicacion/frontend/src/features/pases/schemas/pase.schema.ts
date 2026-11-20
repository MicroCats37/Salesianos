import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the PASS domain (`DOM-03`).
 *
 * They are a 1:1 mirror of the presenters of the target backend
 * (`Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pase_schemas.py`):
 * `PrecioPaseOut`, `PaseOut`, `PaseDetalleOut`, `PaseCatalogoOut`,
 * `PaseBeneficiarioOut`, `PaseBeneficiariosOut`, `PaseCompraDetalleOut`,
 * `CompraPaseCreadaOut` and `PaseBeneficiarioRevocadoOut`.
 *
 * The rules of the mirror:
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The envelope is the FROZEN one** (`FREEZE-ENV-1.0.0`): the factory
 *   `apiResponseSchema` of the project builds it, so the shape is not
 *   replicated per endpoint.
 * - **The machine codes are `string`, not enums.** The backend owns the
 *   vocabulary (`EstadoCompraPase`, `EstadoDerechoPase`, `EstadoPase`) and a
 *   new value must NOT break the whole read. The label of a code is
 *   resolved by the ADAPTER (`utils/pase.adaptador.utils.ts`), never shown
 *   raw.
 * - **The amounts are NUMBERS.** The target serialises `Decimal` as a float
 *   (`core/types.py` → `BaseSchema.ser_json_decimal_to_float`).
 * - **The instants are STRINGS.** The backend may publish a naive or an aware
 *   ISO-8601 instant depending on the storage; the frontend never parses it,
 *   it shows the text the server sent.
 */

/**
 * The header that carries the private token of the management link.
 *
 * It is the channel frozen by `DOM-03` (`D-DOM03-04`): the token is a
 * CREDENTIAL, so it never travels in the query string, which stays in the
 * logs.
 */
export const CABECERA_TOKEN_PASE = "X-Pase-Token";

/** An identifier of the domain: a UUID published by the presenter. */
const id = z.string().uuid();

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant or a date published by the presenter. */
const marcaTiempo = z.string().min(1);

/** An ISO-4217 currency code. */
const moneda = z.string().min(1).max(3);

/**
 * The catalogue price of a pass (`PrecioPaseOut`).
 *
 * `monto` is a `Decimal` on the server and the wire publishes it as a float
 * (`core/types.py` → `BaseSchema.ser_json_decimal_to_float`).
 */
export const precioPaseSchema = z.object({
  monto: z.number(),
  moneda,
  vigente_desde: marcaTiempo,
  vigente_hasta: marcaTiempo.nullable(),
});

/** A pass of the catalogue (`PaseOut`). */
export const paseCatalogoSchema = z.object({
  id,
  created_at: marcaTiempo,
  updated_at: marcaTiempo,
  edicion_id: id,
  edicion_nombre: z.string(),
  nombre: z.string(),
  slug: z.string(),
  descripcion: z.string(),
  estado: codigo,
  precio: precioPaseSchema,
});

/**
 * The detail of a pass (`PaseDetalleOut`).
 *
 * `precio` is NULL when the pass has no current price: there is no reserved
 * price invented (`FL-01` paso 3).
 */
export const paseDetalleSchema = z.object({
  id,
  created_at: marcaTiempo,
  updated_at: marcaTiempo,
  edicion_id: id,
  edicion_nombre: z.string(),
  nombre: z.string(),
  slug: z.string(),
  descripcion: z.string(),
  estado: codigo,
  precio: precioPaseSchema.nullable(),
});

/** The catalogue of ONE edition (`PaseCatalogoOut`). */
export const catalogoPasesSchema = z.object({
  edicion_id: id,
  edicion_nombre: z.string(),
  pases: z.array(paseCatalogoSchema),
});

/** An entry right of a person (`PaseBeneficiarioOut`). */
export const beneficiarioPaseSchema = z.object({
  id,
  pase_id: id,
  pase_nombre: z.string(),
  edicion_id: id,
  persona_id: id,
  persona_nombres: z.string(),
  persona_apellidos: z.string(),
  persona_tipo_documento: z.string(),
  persona_numero_documento: z.string(),
  origen: codigo,
  estado: codigo,
  cantidad: z.number().int(),
  cantidad_consumida: z.number().int(),
  cantidad_disponible: z.number().int(),
  asignado_en: marcaTiempo,
  motivo: z.string(),
  revocado_en: marcaTiempo.nullable(),
  motivo_revocacion: z.string(),
});

/** The rights granted in a batch (`PaseBeneficiariosOut`). */
export const beneficiariosPaseSchema = z.object({
  compra_pase_id: id,
  estado: codigo,
  cantidad: z.number().int(),
  asignados: z.number().int(),
  disponibles: z.number().int(),
  beneficiarios: z.array(beneficiarioPaseSchema),
});

/**
 * The detail of a batch purchase (`PaseCompraDetalleOut`).
 *
 * It is the shape of the beneficiary list PLUS the commercial facts of the
 * batch. The three counts (`cantidad`, `asignados`, `disponibles`) are
 * DECLARED by the server: the browser never subtracts them.
 */
export const compraPasesSchema = beneficiariosPaseSchema.extend({
  compra_id: id.nullable(),
  orden_pago_id: id.nullable(),
  pase_id: id,
  pase_nombre: z.string(),
  edicion_nombre: z.string(),
  precio_unitario: z.number(),
  total: z.number(),
  moneda,
  causa_operativa: codigo,
});

/**
 * The answer of a purchase (`CompraPaseCreadaOut`).
 *
 * `token` travels HERE and ONLY here: it is the credential of the management
 * link and it never appears in a listing.
 */
export const compraPaseCreadaSchema = z.object({
  compra_pase_id: id,
  compra_id: id,
  orden_pago_id: id.nullable(),
  estado: codigo,
  pase_id: id,
  pase_nombre: z.string(),
  edicion_id: id,
  edicion_nombre: z.string(),
  cantidad: z.number().int(),
  precio_unitario: z.number(),
  total: z.number(),
  moneda,
  comprador_persona_id: id,
  comprador_nombres: z.string(),
  token: z.string().min(1),
  token_expira_en: marcaTiempo,
  reutilizada: z.boolean(),
  causa_operativa: codigo,
});

/** The answer of a revocation (`PaseBeneficiarioRevocadoOut`). */
export const beneficiarioRevocadoSchema = z.object({
  compra_pase_id: id,
  derecho_id: id,
  persona_id: id,
  estado: codigo,
  revocado_en: marcaTiempo,
  ya_revocado: z.boolean(),
  motivo: z.string(),
});

/**
 * The payload of a purchase (`ComprarPaseIn`).
 *
 * It admits NO amount: the price is resolved by the server against the
 * current catalogue (`RN-C02`) and the quantity limit is a rule of the
 * domain, which rejects it with `CANTIDAD_INVALIDA` (422).
 */
export const comprarPaseSchema = z.object({
  pase_id: id,
  cantidad: z.number().int().positive(),
  tipo_documento: z.string().min(1).max(3),
  numero_documento: z.string().min(1).max(20),
  nombres: z.string().min(1).max(255),
  apellidos: z.string().max(255),
  contacto_email: z.string().max(255),
});

/**
 * The payload of an assignment (`AsignarBeneficiarioIn`).
 *
 * The person may arrive by IDENTIFIER or by DOCUMENT. Every field is
 * optional and nullable: the client sends what it knows and omits the rest.
 */
export const asignarBeneficiarioSchema = z.object({
  persona_id: z.string().uuid().nullable().optional(),
  tipo_documento: z.string().max(3).nullable().optional(),
  numero_documento: z.string().max(20).nullable().optional(),
  nombres: z.string().max(255).optional(),
  apellidos: z.string().max(255).optional(),
  motivo: z.string().max(500).optional(),
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The envelope of every pass read and write (`FREEZE-ENV-1.0.0`). */
export const catalogoPasesEnvelope = apiResponseSchema(catalogoPasesSchema);
export const paseDetalleEnvelope = apiResponseSchema(paseDetalleSchema);
export const compraPaseCreadaEnvelope = apiResponseSchema(
  compraPaseCreadaSchema,
);
export const compraPasesEnvelope = apiResponseSchema(compraPasesSchema);
export const beneficiariosPaseEnvelope = apiResponseSchema(
  beneficiariosPaseSchema,
);
export const beneficiarioRevocadoEnvelope = apiResponseSchema(
  beneficiarioRevocadoSchema,
);

// ── Inferred types ───────────────────────────────────────────────────────────

export type PrecioPase = z.infer<typeof precioPaseSchema>;
export type PaseCatalogo = z.infer<typeof paseCatalogoSchema>;
export type PaseDetalle = z.infer<typeof paseDetalleSchema>;
export type CatalogoPases = z.infer<typeof catalogoPasesSchema>;
export type BeneficiarioPaseWire = z.infer<typeof beneficiarioPaseSchema>;
export type BeneficiariosPase = z.infer<typeof beneficiariosPaseSchema>;
export type CompraPasesWire = z.infer<typeof compraPasesSchema>;
export type CompraPaseCreada = z.infer<typeof compraPaseCreadaSchema>;
export type BeneficiarioRevocado = z.infer<typeof beneficiarioRevocadoSchema>;
export type ComprarPaseDatos = z.infer<typeof comprarPaseSchema>;
export type AsignarBeneficiarioDatos = z.infer<
  typeof asignarBeneficiarioSchema
>;
