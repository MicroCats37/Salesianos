import { PasesRuta } from "@/features/pases/views";

/**
 * PASS-01 - Comprar un pase de fiesta
 *
 * The page is ROUTING-ONLY: the container (`PasesRuta`) owns the read of
 * the catalogue and the mutation of the purchase.
 */
export default function Page() {
  return <PasesRuta />;
}
