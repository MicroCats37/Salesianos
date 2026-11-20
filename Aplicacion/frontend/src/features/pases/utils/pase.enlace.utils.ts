import { RUTAS } from "@/lib/routes";
import type { CompraPaseCreada } from "../schemas/pase.schema";

/**
 * The management link of a purchase.
 *
 * The link carries TWO facts and they travel in two places:
 *
 * - The **TOKEN**, in the path, because the route map of the product
 *   declares the guest link as a path token (`RUTAS.publico.paseGestionar`)
 *   and `P-01` leaves that channel provisional.
 * - The **identifier of the batch**, in the query string, because the
 *   backend opens a batch by its identifier
 *   (`GET /pases/compras/{compra_pase_id}`) and the token alone does not
 *   resolve it.
 *
 * The identifier is NOT a credential: the access of the batch is decided by
 * the token, which the backend reads from the `X-Pase-Token` header and
 * never from the query string (`F-61`, `D-DOM03-04`). The query string only
 * travels the name of the thing to open.
 */
export function enlaceGestionCompra(compra: CompraPaseCreada): string {
  const id = encodeURIComponent(compra.compra_pase_id);
  return `${RUTAS.publico.paseGestionar(compra.token)}?compra=${id}`;
}
