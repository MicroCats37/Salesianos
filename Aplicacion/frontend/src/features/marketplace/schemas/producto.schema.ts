import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import { paginatedResultSchema } from "@/shared/schemas/pagination.schema";

/**
 * The Zod mirrors of the STORE (`DOM-04`).
 *
 * They are a 1:1 mirror of the presenters of the target backend
 * (`Aplicacion/backend/modules/marketplace/presentation/schemas/producto_schemas.py`):
 * `CategoriaListaOut`, `ProductoListItemOut`, `ProductoImagenOut` and
 * `ProductoDetalleOut`.
 *
 * The rules of the mirror:
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The envelope is the FROZEN one** (`FREEZE-ENV-1.0.0`): the factory
 *   `apiResponseSchema` of the project builds it and the pagination has the
 *   ONE shape of the target (`{ items, total, page, page_size, total_pages }`
 *   INSIDE `data`).
 * - **The machine codes are `string`, not enums.** The backend owns the
 *   vocabulary and a new value must NOT break the whole read.
 * - **The amounts are NUMBERS.** The target serialises `Decimal` as a float.
 * - **The catalogue declares NO stock.** The stock belongs to `DOM-06`
 *   (`RN-M06`) and this wrapper does not publish it: the interface never
 *   invents an availability (`D-DOM04-06`).
 */

/** An identifier of the domain: a UUID published by the presenter. */
const id = z.string().uuid();

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant published by the presenter. */
const marcaTiempo = z.string().min(1);

/** A category of the catalogue (`CategoriaListaOut`). */
export const categoriaListaSchema = z.object({
  id,
  nombre: z.string(),
  slug: z.string(),
  orden: z.number().int(),
});

/** An image of the gallery of a product (`ProductoImagenOut`). */
export const productoImagenSchema = z.object({
  id,
  orden: z.number().int(),
  url: z.string().nullable(),
  es_principal: z.boolean(),
  texto_alternativo: z.string(),
  disponible: z.boolean(),
  created_at: marcaTiempo,
});

/** A product of the catalogue (`ProductoListItemOut`). */
export const productoListItemSchema = z.object({
  id,
  nombre: z.string(),
  slug: z.string(),
  categoria_id: id.nullable(),
  categoria_nombre: z.string().nullable(),
  precio: z.number(),
  precio_oferta: z.number().nullable(),
  precio_efectivo: z.number(),
  oferta_activa: z.boolean(),
  estado: codigo,
  imagen_principal_url: z.string().nullable(),
  cantidad_imagenes: z.number().int(),
});

/**
 * The detail of a product (`ProductoDetalleOut`).
 *
 * The gallery travels ORDERED (`orden ASC, id ASC`) and every image says if
 * its file is still available in the volume (`FR-06` §2.7).
 */
export const productoDetalleSchema = productoListItemSchema.extend({
  created_at: marcaTiempo,
  updated_at: marcaTiempo,
  edicion_id: id,
  edicion_nombre: z.string(),
  descripcion: z.string(),
  oferta_inicia: marcaTiempo.nullable(),
  oferta_termina: marcaTiempo.nullable(),
  imagenes: z.array(productoImagenSchema),
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The categories of the catalogue (`RT-MK-01`). */
export const categoriasEnvelope = apiResponseSchema(
  z.array(categoriaListaSchema),
);

/** The catalogue of products (`RT-MK-02`). */
export const productosEnvelope = apiResponseSchema(
  paginatedResultSchema(productoListItemSchema),
);

/** The detail of a product (`RT-MK-03`). */
export const productoDetalleEnvelope = apiResponseSchema(productoDetalleSchema);

// ── Inferred types ───────────────────────────────────────────────────────────

export type CategoriaLista = z.infer<typeof categoriaListaSchema>;
export type ProductoImagen = z.infer<typeof productoImagenSchema>;
export type ProductoListItem = z.infer<typeof productoListItemSchema>;
export type ProductoDetalle = z.infer<typeof productoDetalleSchema>;
