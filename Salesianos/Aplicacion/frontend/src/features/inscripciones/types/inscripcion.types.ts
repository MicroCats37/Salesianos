import type {
  Beneficio,
  CatalogoDisciplinas,
  CatalogoPaquetes,
  Disciplina,
  Paquete,
  Precio,
} from "../schemas/catalogo.schema";
import type { CompraCreada } from "../schemas/compra-cupos.schema";
import type {
  Compra,
  Equipo,
  InscripcionDetalle as InscripcionDetalleWrapper,
  InscripcionInicial,
} from "../schemas/inscripcion.schema";
import type {
  Impedimento,
  Participacion,
  Pool,
} from "../schemas/pool.schema";

/**
 * The view models of the registration area (SPORT-01 and ACCOUNT-03).
 *
 * They are DERIVED from the Zod mirrors of the target presenters: one shape,
 * one owner. There is no second description of the wire in this feature, so a
 * drift between the presenter and the browser is a parse error and not a
 * silently wrong field.
 *
 * No business rule lives here. A price, an eligibility, a capacity, a
 * payment state, a stock and a permission are DECLARED by the presenter and
 * never derived in the browser (`00-contrato-global-de-apply.md`, Hard
 * Prohibitions; `SH-01` T-03).
 */

// ── Catálogo ─────────────────────────────────────────────────────────────────

/** A discipline of the catalogue (mirrors `DisciplinaOut`). */
export type DisciplinaCatalogo = Disciplina;

/** The catalogue of packages of ONE edition (mirrors `CatalogoPaquetesOut`). */
export type CatalogoPaquetes = CatalogoPaquetesWrapper;

/** The catalogue of disciplines of ONE edition (mirrors `CatalogoDisciplinasOut`). */
export type CatalogoDisciplinas = CatalogoDisciplinasWrapper;

/** A package of the catalogue (mirrors `PaqueteOut`). */
export type PaqueteCatalogo = Paquete;

/** A benefit a package OFFERS (mirrors `BeneficioOut`). */
export type BeneficioCatalogo = Beneficio;

/** The price of the catalogue (mirrors `PrecioOut`). */
export type PrecioCatalogo = Precio;

// ── Inscripción ──────────────────────────────────────────────────────────────

/** A team declared in a registration (mirrors `EquipoOut`). */
export type EquipoInscripcion = Equipo;

/** The detail of a registration (mirrors `InscripcionDetalleOut`). */
export type InscripcionDetalle = InscripcionDetalleWrapper;

/** The pool of cupos of a registration (mirrors `PoolOut`). */
export type PoolInscripcion = Pool;

/** A participation of the pool (mirrors `ParticipacionOut`). */
export type ParticipacionPool = Participacion;

/** A concrete impediment of the pool (mirrors `ImpedimentoOut`). */
export type ImpedimentoPool = Impedimento;

/**
 * The purchase that finances the registration (mirrors `CompraOut`).
 *
 * It is a PROJECTION of the purchase of `commerce`: this feature never sees
 * the model of another domain.
 */
export type CompraInscripcion = Compra;

/** The purchase of extra cupos (mirrors `CompraCreadaOut`). */
export type CompraCupos = CompraCreada;

/** The answer of the alta (mirrors `InscripcionInicialOut`). */
export type AltaInscripcion = InscripcionInicial;

/**
 * The purchases of a registration.
 *
 * The initial purchase comes with the alta and every expansion comes with
 * its own answer (`RT-CM-01`). The target backend does not publish a route
 * that LISTS them, so the list is a seam and not an invented endpoint.
 */
export interface ComprasInscripcion {
  inicial: CompraInscripcion | null;
  expansiones: readonly CompraInscripcion[];
}

/**
 * A benefit GRANTED to a registration.
 *
 * `BeneficioConcedido` exists in the domain of DOM-02, but no presenter of
 * the target backend publishes it yet. The shape below is therefore the SEAM
 * of the section, and its absence is rendered honestly.
 */
export interface BeneficioConcedido {
  codigo: string;
  nombre: string;
  tipo: string;
  cantidad: number;
}

/**
 * The state a route of this area is in.
 *
 * The default of every view is `sin-datos`: the data has not arrived yet,
 * and the view says so instead of drawing data that does not exist.
 */
export type EstadoInscripcion = "sin-datos" | "listo" | "sin-permiso" | "error";

/**
 * The operational cause that the backend publishes with a pool answer.
 *
 * It is a STRING on purpose: the catalogue of public codes is not closed
 * (33 codes are still open), so the frontend prints it and never branches on
 * it (`SH-03` §6).
 */
export type CausaOperativa = string;
