import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the SPONSORS area (`DOM-08`).
 *
 * They are a 1:1 mirror of the presenter and of the input schema of the
 * target backend
 * (`Aplicacion/backend/modules/patrocinadores/presentation/schemas/patrocinadores_schemas.py`):
 * `PatrocinadorIdentidadOut`, `PatrocinadorGeneralOut`,
 * `PatrocinadorEspecificaOut`, `PatrocinadorLogoOut`,
 * `PatrocinadorImagenOut` and `PatrocinadorOut` (the COMPOSITION of the
 * three blocks), plus `ImagenPatrocinadorIn` and `CrearPatrocinadorIn`.
 *
 * ## THE RULES OF THE MIRROR
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The envelope is the FROZEN one** (`FREEZE-ENV-1.0.0`): the factory
 *   `apiResponseSchema` of the project builds it.
 * - **The identifiers of `DOM-08` are `UUID`**, so the mirror is strict about
 *   the shape of a UUID.
 * - **The media is DECLARED, never derived.** `url` may be `null` and
 *   `disponible` says whether the file is still readable in the volume: the
 *   interface shows the GAP, never a broken image (`FR-06` §2.7).
 * - **THERE ARE NO MONETARY FIELDS.** A sponsor has a name, a logo, an
 *   ordered gallery and a visibility: never an amount, a contribution or a
 *   commission (`GOV-02-RB-08b`). A mirror that grew a `monto` field would be
 *   inventing a contract.
 *
 * ## THIS MIRROR IS NOT BOUND
 *
 * `PatrocinadorController` is **NOT registered** in
 * `Aplicacion/backend/config/api.py` and `modules.patrocinadores` is **NOT**
 * in `LOCAL_APPS`, so its ONE route (`POST /patrocinadores`, `RT-MD-02`)
 * DOES NOT EXIST at runtime (`A0-RTV-01` / `A0-RTV-02`). A client that
 * called it would be calling a route that the API does not serve, so **this
 * package binds none of them** (`FR-07` §3.1 regla 2).
 *
 * What this file IS is the frozen contract of the area, written down so that
 * the day A0 registers the controller the binding is a client and ZERO
 * rewrites of the views.
 *
 * There is also NO READ route for the sponsors: the ledger declares ONE row
 * (`RT-MD-02`) and the presenter publishes ONLY the sponsor that was just
 * created. The list of the sponsors of the edition is a MISSING CAPABILITY,
 * not a missing implementation (`D-DOM08-05` / `A0-API05-03`).
 */

/** An identifier of the domain: `DOM-08` declares its identifiers as `UUID`. */
const id = z.string().uuid();

/** An instant published by the presenter (`datetime`). */
const marcaTiempo = z.string().min(1);

// ── Salidas ───────────────────────────────────────────────────────────────────

/** The block of identity of a sponsor (`PatrocinadorIdentidadOut`). */
export const patrocinadorIdentidadSchema = z.object({
  id,
  created_at: marcaTiempo,
  updated_at: marcaTiempo,
});

/** The block of scope of a sponsor (`PatrocinadorGeneralOut`). */
export const patrocinadorGeneralSchema = z.object({
  edicion_id: id,
  edicion_nombre: z.string(),
});

/** The block of the record of a sponsor (`PatrocinadorEspecificaOut`). */
export const patrocinadorEspecificaSchema = z.object({
  nombre: z.string(),
  /**
   * The identifier of the sponsor inside the edition.
   *
   * It is kebab-case on purpose: the multipart protocol scans the raw payload
   * looking for tokens (`file_<uuid>`) and an identifier with an underscore
   * could collide with that pattern (`D-DOM08-04`).
   */
  slug: z.string(),
  descripcion: z.string(),
  sitio_web: z.string(),
  /** The public visibility of the sponsor. */
  visible: z.boolean(),
  orden: z.number().int(),
});

/** The logo of identity of a sponsor (`PatrocinadorLogoOut`). */
export const patrocinadorLogoSchema = z.object({
  /** The public URL of the file; `null` when there is none. */
  url: z.string().nullable(),
  /** Whether the file is still readable in the volume. */
  disponible: z.boolean(),
});

/** One image of the ordered gallery (`PatrocinadorImagenOut`). */
export const patrocinadorImagenSchema = z.object({
  id,
  /** The canonical order of the image inside the gallery. */
  orden: z.number().int(),
  /** The public URL of the file; `null` when there is none. */
  url: z.string().nullable(),
  /** The alternative text of the image. */
  texto_alternativo: z.string(),
  /** Whether the file is still readable in the volume. */
  disponible: z.boolean(),
  created_at: marcaTiempo,
});

/**
 * A sponsor of the edition (`PatrocinadorOut`).
 *
 * It is the COMPOSITION of the three blocks (`SCHEMA_DRY_INTENTION`), not a
 * monolithic schema: the mirror reproduces the composition instead of
 * repeating the fields.
 */
export const patrocinadorSchema = patrocinadorIdentidadSchema
  .extend(patrocinadorGeneralSchema.shape)
  .extend(patrocinadorEspecificaSchema.shape)
  .extend({
    /** The logo of identity; `null` when the sponsor has none. */
    logo: patrocinadorLogoSchema.nullable(),
    /** The ordered gallery of the sponsor. */
    imagenes: z.array(patrocinadorImagenSchema),
  });

// ── Entradas ─────────────────────────────────────────────────────────────────

/**
 * One image declared in the payload of the alta (`ImagenPatrocinadorIn`).
 *
 * `token` is the token of the multipart protocol (`file_<uuid>`). The token
 * appears EXACTLY ONCE in the payload: that is why the alternative text
 * travels here and not in a second field (a duplicated token would be a
 * duplicated token).
 */
export const imagenPatrocinadorInSchema = z.object({
  token: z.string().min(1),
  texto_alternativo: z.string().max(200),
});

/**
 * The creation of a sponsor (`CrearPatrocinadorIn`).
 *
 * `imagenes` is the ORDERED gallery: the order of the array IS the canonical
 * order of the images (`FR-06` §2.4).
 *
 * `logo` is the token of the identity logo. It is OPTIONAL: a sponsor can
 * exist without a logo.
 */
export const crearPatrocinadorSchema = z.object({
  nombre: z.string().min(1).max(200),
  /** Kebab-case: the multipart protocol must not be able to confuse it with a token. */
  slug: z
    .string()
    .min(1)
    .max(200)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
  descripcion: z.string().max(5000),
  sitio_web: z.string().max(300),
  visible: z.boolean(),
  /** The token of the identity logo; `null` when there is none. */
  logo: z.string().nullable(),
  /** The ordered gallery of the sponsor. */
  imagenes: z.array(imagenPatrocinadorInSchema),
});

/**
 * The FORM of the record of a sponsor.
 *
 * It is the mirror of what the operator fills in, NOT of what the server
 * publishes: the files travel AS FILES (the multipart protocol turns them
 * into their `file_<uuid>` token) and the identifier of the edition is
 * resolved by the server.
 */
export const formularioPatrocinadorSchema = z.object({
  nombre: z
    .string()
    .trim()
    .min(1, "Escribe el nombre del patrocinador.")
    .max(200, "El nombre admite 200 caracteres como máximo."),
  slug: z
    .string()
    .trim()
    .min(1, "El identificador es obligatorio.")
    .max(200, "El identificador admite 200 caracteres como máximo.")
    .regex(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      "El identificador va en minúsculas y con guiones, por ejemplo colegio-norte.",
    ),
  descripcion: z
    .string()
    .max(5000, "La descripción admite 5000 caracteres como máximo."),
  sitio_web: z
    .string()
    .trim()
    .max(300, "El sitio web admite 300 caracteres como máximo."),
  visible: z.boolean(),
  logo: z
    .custom<File>(
      (valor) => typeof File !== "undefined" && valor instanceof File,
      "Selecciona un archivo válido.",
    )
    .nullable()
    .optional(),
  imagenes: z.array(
    z.custom<File>(
      (valor) => typeof File !== "undefined" && valor instanceof File,
      "Selecciona un archivo válido.",
    ),
  ),
});

export type FormularioPatrocinadorDatos = z.infer<
  typeof formularioPatrocinadorSchema
>;

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The sponsor that was just created (`POST /patrocinadores`). */
export const patrocinadorEnvelope = apiResponseSchema(patrocinadorSchema);

/** The list of the sponsors of the edition. */
export const listaPatrocinadoresEnvelope = apiResponseSchema(
  z.array(patrocinadorSchema),
);

// ── Inferred types ───────────────────────────────────────────────────────────

export type PatrocinadorLogo = z.infer<typeof patrocinadorLogoSchema>;
export type ImagenPatrocinador = z.infer<typeof patrocinadorImagenSchema>;
export type Patrocinador = z.infer<typeof patrocinadorSchema>;
export type ImagenPatrocinadorIn = z.infer<typeof imagenPatrocinadorInSchema>;
export type CrearPatrocinador = z.infer<typeof crearPatrocinadorSchema>;

/**
 * The error codes of the media family of `RT-MD-02`.
 *
 * They come from the frozen ledger
 * (`evidence/contracts/route-to-wrapper-ledger.csv`): the wording is the
 * wording of this interface and it never contradicts the rule of the server.
 */
export const CODIGOS_ERROR_MEDIO = [
  "MEDIA_TIPO_NO_PERMITIDO",
  "MEDIA_ARCHIVO_HUERFANO",
  "MEDIA_TOKEN_NO_RESOLTO",
  "MEDIA_TOKEN_DUPLICADO",
  "MEDIA_TAMANO_EXCEDIDO",
  "MEDIA_NO_PERMITIDO",
] as const;

export type CodigoErrorMedio = (typeof CODIGOS_ERROR_MEDIO)[number];
