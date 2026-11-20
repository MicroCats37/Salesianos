import { z } from "zod";
import { paginatedResultSchema } from "@/shared/schemas/pagination.schema";
import { apiResponseSchema } from "@/types/api.types";

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
  precio: z.coerce.number(),
  precio_oferta: z.coerce.number().nullable(),
  precio_efectivo: z.coerce.number(),
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
export const productoDetalleSchema = productoListItemSchema
  .omit({ cantidad_imagenes: true })
  .extend({
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

/** The response returned after an administrator creates a product (`RT-MD-01`). */
export const productoCreadoSchema = productoDetalleSchema;
export const productoCreadoEnvelope = apiResponseSchema(productoCreadoSchema);

const fechaOpcionalSchema = z
  .preprocess(
    (valor) => (valor === "" || valor === undefined ? null : valor),
    z.coerce.date().nullable(),
  )
  .transform((valor) => valor?.toISOString() ?? null);

const imagenProductoFormSchema = z.object({
  archivo: z.custom<File>(
    (valor) => typeof File !== "undefined" && valor instanceof File,
    "Selecciona una imagen válida.",
  ),
  texto_alternativo: z.string().trim().max(200),
  es_principal: z.boolean(),
});

/**
 * Validated values for the administrator product form.
 *
 * Files stay in this schema until the mutation assigns their multipart tokens.
 */
export const productoCrearFormSchema = z
  .object({
    nombre: z.string().trim().min(1, "Indica el nombre del producto.").max(200),
    slug: z
      .string()
      .trim()
      .min(1, "Indica el identificador del producto.")
      .max(200)
      .regex(
        /^[-a-zA-Z0-9_]+$/,
        "Usa letras, números, guiones o guiones bajos.",
      ),
    descripcion: z.string().trim().max(5000),
    categoria_id: z.string().uuid().nullable(),
    precio: z.coerce
      .number()
      .finite()
      .min(0, "El precio no puede ser negativo."),
    precio_oferta: z.preprocess(
      (valor) => (valor === "" || valor === undefined ? null : valor),
      z.coerce
        .number()
        .finite()
        .min(0, "El precio de oferta no puede ser negativo.")
        .nullable(),
    ),
    oferta_inicia: fechaOpcionalSchema,
    oferta_termina: fechaOpcionalSchema,
    estado: z.enum(["ACTIVO", "INACTIVO"]),
    stock_inicial: z.coerce
      .number()
      .int("El stock inicial debe ser un número entero.")
      .min(0, "El stock inicial no puede ser negativo."),
    imagenes: z
      .array(imagenProductoFormSchema)
      .min(1, "Carga al menos una imagen del producto.")
      .refine(
        (imagenes) =>
          imagenes.filter((imagen) => imagen.es_principal).length === 1,
        "Elige una única imagen principal.",
      ),
  })
  .refine(
    (producto) =>
      !producto.oferta_inicia ||
      !producto.oferta_termina ||
      producto.oferta_termina >= producto.oferta_inicia,
    {
      message: "El fin de la oferta debe ser posterior a su inicio.",
      path: ["oferta_termina"],
    },
  );

// ── Inferred types ───────────────────────────────────────────────────────────

export type CategoriaLista = z.infer<typeof categoriaListaSchema>;
export type ProductoImagen = z.infer<typeof productoImagenSchema>;
export type ProductoListItem = z.infer<typeof productoListItemSchema>;
export type ProductoDetalle = z.infer<typeof productoDetalleSchema>;
export type ProductoCreado = z.infer<typeof productoCreadoSchema>;
export type ProductoCrearFormData = z.infer<typeof productoCrearFormSchema>;

export interface ProductoCrearPayload {
  nombre: string;
  slug: string;
  descripcion: string;
  categoria_id: string | null;
  precio: number;
  precio_oferta: number | null;
  oferta_inicia: string | null;
  oferta_termina: string | null;
  estado: "ACTIVO" | "INACTIVO";
  imagenes: Array<{
    token: File;
    texto_alternativo: string;
    es_principal: boolean;
  }>;
}
