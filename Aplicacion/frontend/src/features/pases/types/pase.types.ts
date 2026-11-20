/**
 * The view models of the pass area (`PASS-01`, `PASS-02`).
 *
 * The SHAPE of the wire is owned by the Zod mirror
 * (`schemas/pase.schema.ts`), which mirrors the target presenters of `DOM-03`
 * (`Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pase_schemas.py`):
 * `PaseCatalogoOut`, `PaseOut`, `PrecioPaseOut`, `PaseBeneficiariosOut` and
 * `PaseCompraDetalleOut`.
 *
 * These types only add what the interface needs ON TOP of the wire: the
 * LABEL of a machine code. The backend publishes codes and no wording
 * (`A0-UI03-04`), so the ADAPTER resolves the label and both travel
 * together: the interface never shows a code (`SH-03` §6) and never rewrites
 * the wording of the backend.
 *
 * No business rule lives here. A price, a total, an availability, a capacity,
 * a payment state and a permission are DECLARED by the presenter and never
 * derived in the browser (`00-contrato-global-de-apply.md`, Hard
 * Prohibitions; `SH-01` T-03).
 */

import type {
  AsignacionPaseData,
  CompradorPaseData,
} from "../schemas/comprador-pase.schema";
import type {
  BeneficiarioPaseWire,
  CompraPaseCreada,
  CompraPasesWire,
  PaseCatalogo,
} from "../schemas/pase.schema";

export type {
  BeneficiariosPase,
  CatalogoPases,
  CompraPaseCreada,
  PaseCatalogo,
  PaseDetalle,
  PrecioPase,
} from "../schemas/pase.schema";

/**
 * The visual bucket of a payment verdict.
 *
 * `SH-01` §3.2: the colour is a PRESENTATIONAL bucket, never the meaning.
 * The label and the meaning always come from the backend. The bucket is
 * resolved by the ADAPTER, never by the component.
 *
 * The five buckets are exactly the five presentable payment states of
 * `SH-03` §3 and of `frontend/03` ("Componente compartido de pago").
 */
export type RolPago =
  | "pendiente"
  | "verificando"
  | "confirmado"
  | "sin-confirmar"
  | "atencion";

/**
 * The verdict of the backend (`EstadoOperativo`, `FREEZE-ENV-1.0.0` §5).
 *
 * The machine code, the label in plain language and the explanation. The
 * frontend NEVER rewrites the label and NEVER shows the code (`SH-03` §6).
 */
export interface EstadoPagoOperativo {
  codigo: string;
  etiqueta: string;
  descripcion: string;
}

/**
 * A payment verdict with its visual bucket.
 *
 * `estado` is what the backend says; `rol` is how the adapter decided to
 * paint it. Both travel together so the label and the colour can never
 * disagree (`D-UI01-02`).
 */
export interface VeredictoPago {
  estado: EstadoPagoOperativo;
  rol: RolPago;
}

/**
 * An entry right of a person (`PaseBeneficiarioOut` + its label).
 *
 * The counts of consumed and available units are DECLARED by the presenter:
 * the browser never subtracts them.
 *
 * `estado` is the machine code the presenter publishes and `estado_etiqueta`
 * is the label the ADAPTER resolved from it. Both travel together because
 * the interface never shows a code (`SH-03` §6) and never rewrites the
 * wording of the backend. Same rule as `D-UI01-02`.
 */
export type BeneficiarioPase = BeneficiarioPaseWire & {
  estado_etiqueta: string;
};

/**
 * The purchase of a batch of passes (`PaseCompraDetalleOut` + its label).
 *
 * `cantidad`, `asignados` and `disponibles` are three FACTS the backend
 * publishes. The frontend shows them side by side and never computes the
 * third one from the first two.
 */
export type CompraPases = Omit<CompraPasesWire, "beneficiarios"> & {
  estado_etiqueta: string;
  beneficiarios: BeneficiarioPase[];
};

/**
 * The state a route is in.
 *
 * The default of every view is `sin-datos`: the service is not connected
 * yet, and the view says so instead of drawing a catalogue that does not
 * exist.
 */
export type EstadoVistaPases =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";


/**
 * The delivery state of a pass batch.
 *
 * It is a SEPARATE fact from the payment state (`RN-M07`): a paid batch whose
 * entries are not assigned yet is not a failure, it is a pending fact.
 */
export interface EstadoAsignacion {
  codigo: string;
  etiqueta: string;
}

/**
 * The transport of the purchase, seen by the checkout.
 *
 * The component NEVER builds the payload: it says WHICH pass, HOW MANY and
 * WHAT the buyer typed, and the mutation builds the wire from it.
 */
export type EnviarCompraPase = (
  pase: PaseCatalogo,
  cantidad: number,
  datos: CompradorPaseData,
) => Promise<CompraPaseCreada | void>;

/** The transport of the assignment of a pass to a person. */
export type EnviarAsignacionPase = (
  datos: AsignacionPaseData,
) => Promise<void>;

/** The transport of the revocation of an entry right. */
export type RevocarBeneficiario = (
  beneficiario: BeneficiarioPase,
  motivo: string,
) => Promise<void>;

