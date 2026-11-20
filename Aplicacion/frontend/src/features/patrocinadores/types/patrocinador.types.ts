/**
 * The view models of the sponsors area (`ADM-21`).
 *
 * They are the VIEW CONTRACT of the area, and they are a faithful 1:1
 * projection of the presenter of the target backend, read directly from
 * `Aplicacion/backend/modules/patrocinadores/presentation/schemas/patrocinadores_schemas.py`:
 * `PatrocinadorOut` with its three blocks (`PatrocinadorIdentidadOut`,
 * `PatrocinadorGeneralOut`, `PatrocinadorEspecificaOut`), plus
 * `PatrocinadorLogoOut` and `PatrocinadorImagenOut`.
 *
 * The WIRE mirror lives NEXT to these types, in
 * `schemas/patrocinador.schema.ts`, and it is the one that parses the
 * answers of the server. These types are what the components draw, so they
 * carry the presentation decorations (the state, the role) and they never
 * carry a field that the presenter does not publish.
 *
 * `PatrocinadorController` is NOT registered in
 * `Aplicacion/backend/config/api.py` and `modules.patrocinadores` is NOT in
 * `LOCAL_APPS`, so its ONE route DOES NOT EXIST at runtime (`A0-RTV-01` /
 * `A0-RTV-02`) and this area is not bound. The mirror exists anyway: it is
 * the frozen contract of the area, so that the day A0 registers the
 * controller the binding is a client and zero rewrites of the views.
 *
 * THERE ARE NO MONETARY FIELDS, and that is deliberate: a sponsor carries a
 * name, a logo, a gallery and a visibility, never a contribution, a
 * commission or an amount (`GOV-02-RB-08b`, `frontend/04` §9).
 *
 * No business rule lives here. A visibility, an order of the gallery and a
 * media availability are DECLARED by the presenter and never derived in the
 * browser (`SH-01` T-03).
 */

/** The logo of identity of a sponsor (`PatrocinadorLogoOut`). */
export interface LogoPatrocinador {
  /**
   * The URL of the stored file.
   *
   * It is `null` when the presenter published no URL: a stored file can be
   * missing on disk, and the interface shows the GAP instead of a broken
   * image.
   */
  url: string | null;
  /**
   * Whether the file is READABLE.
   *
   * The presenter publishes it because a stored file can be missing on disk:
   * the interface shows the gap instead of a broken image.
   */
  disponible: boolean;
}

/** One image of the ordered gallery (`PatrocinadorImagenOut`). */
export interface ImagenPatrocinador {
  id: string;
  /**
   * The canonical order of the image.
   *
   * The order of the array IS the order (`FR-06` §2.4): the client never
   * renumbers it.
   */
  orden: number;
  /** The URL of the stored file; `null` when there is none. */
  url: string | null;
  /** The alternative text of the image. */
  texto_alternativo: string;
  /** Whether the file is readable. */
  disponible: boolean;
  /** The moment the image was stored. */
  created_at: string;
}

/** A sponsor of the edition (`PatrocinadorOut`). */
export interface Patrocinador {
  id: string;
  created_at: string;
  updated_at: string;
  edicion_id: string;
  edicion_nombre: string;
  nombre: string;
  /**
   * The identifier of the sponsor inside the edition.
   *
   * It is kebab-case on purpose: the multipart protocol scans the raw
   * payload looking for tokens (`file_<uuid>`) and an identifier with an
   * underscore could collide with that pattern (`D-DOM08-04`).
   */
  slug: string;
  descripcion: string;
  sitio_web: string;
  /** The public visibility of the sponsor. */
  visible: boolean;
  /** The logo of identity; `null` when the sponsor has none. */
  logo: LogoPatrocinador | null;
  /** The ordered gallery of the sponsor. */
  imagenes: ImagenPatrocinador[];
}

/**
 * The media error family of `RT-MD-02`.
 *
 * The codes come from the ledger
 * (`evidence/contracts/route-to-wrapper-ledger.csv`) and from the controller
 * of `DOM-08`; the wording is the wording of this interface and it never
 * contradicts the rule of the server.
 *
 * The OWNER of the union is the mirror (`schemas/patrocinador.schema.ts`):
 * the error family of a route belongs to the contract of that route and it
 * is not declared twice.
 */
export type { CodigoErrorMedio } from "../schemas/patrocinador.schema";

/**
 * The state a route is in.
 *
 * The default of every view is `sin-datos`: the service is not connected yet
 * and the view says so instead of drawing a sponsor that does not exist.
 */
export type EstadoVistaPatrocinadores =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";
