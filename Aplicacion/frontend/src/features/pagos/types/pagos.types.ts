/**
 * The view models of the payment area.
 *
 * They are TYPES, not Zod schemas, and they are NOT a mirror of a presenter.
 *
 * The reason is a FACT of the backend, not an omission: the wrappers of the
 * account (`RT-ID-04` `MiCuentaOut`, `RT-ID-05` the list of purchases,
 * `RT-ID-06` the detail of a purchase) have NO registered route in
 * `Aplicacion/backend/config/api.py` and NO frozen presenter to mirror. A Zod
 * mirror of a wrapper that does not exist would be an INVENTED contract.
 *
 * These types therefore describe the SHAPE the views expect, and they are the
 * seam where the real wrappers will land: when the backend owns those routes,
 * the mirror arrives next to these types and the views keep consuming the same
 * shape.
 *
 * No business rule lives here. A price, an eligibility, a capacity, a
 * payment state, a stock and a permission are DECLARED by the presenter and
 * never derived in the browser (`00-contrato-global-de-apply.md`, Hard
 * Prohibitions; `SH-01` T-03).
 */

/**
 * The verdict of the ACTIVATION of the rights of a paid purchase.
 *
 * It mirrors `EstadoActivacionOut` of the target backend
 * (`Aplicacion/backend/modules/pagos/presentation/schemas/pago_schemas.py`),
 * published by `EstadoOperativoPagoService` — the ONLY owner of the payment
 * verdicts (`FREEZE-ENV-1.0.0` §5, `FREEZE-CM-1.0.0` §6 · packet XCT-03).
 *
 * It is a channel SEPARATE from `estado_operativo`: the operator verdict
 * answers "is this paid?" and this one answers "is the right enabled?". The
 * browser NEVER crosses the sibling facts to answer either of them
 * (`RN-C07` · `contratos/01` §1.4).
 */
export interface EstadoActivacion {
  codigo: string;
  etiqueta: string;
  descripcion: string;
  /** Whether the incident admits a safe retry. */
  recuperable: boolean;
  /** The safe next step, as the backend names it. */
  proxima_accion: string;
}

/**
 * The visual bucket of a verdict.
 *
 * `SH-01` §3.2: the colour is a PRESENTATIONAL bucket, never the meaning.
 * The label and the meaning always come from the backend. The bucket is
 * resolved by the ADAPTER, never by the component: the component only
 * receives the bucket, so it never branches on a business code.
 */
export type RolActivacion =
  | "confirmado"
  | "pendiente"
  | "verificando"
  | "atencion"
  | "sin-confirmar"
  | "rechazado"
  | "desconocido";

/**
 * A verdict with its visual bucket.
 *
 * `estado` is what the backend says; `rol` is how the adapter decided to
 * paint it. Both travel together so the label and the colour can never
 * disagree (`D-UI01-02` · `D-UI04-03`).
 */
export interface VeredictoActivacion {
  estado: EstadoActivacion;
  rol: RolActivacion;
}
