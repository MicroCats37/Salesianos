import type { QueryClient } from "@tanstack/react-query";
import { adminClaves, type DatasetAdmin } from "./admin.claves.utils";

/**
 * The invalidation of the administration area.
 *
 * ## The rule that decides the invalidation
 *
 * A mutation declares EXACTLY the keys it dirties and NOTHING else
 * (`FND-08` §3 regla 6): a mutation that does not declare anything does not
 * dirty anything.
 *
 * The invalidation lives INSIDE the `mutationFn`, not in `onSettled`: a
 * component that unmounts while the mutation is in flight would never run
 * `onSettled` and the cache would keep an answer the server never gave
 * (`FND-08` §3 regla 5).
 *
 * ## What is NOT invalidated here
 *
 * The datasets that another feature owns: the pool of a registration belongs
 * to `features/inscripciones` and the verdict of a payment order belongs to
 * `features/pagos` (`XCT-03`). Their owner invalidates them.
 */
export async function invalidarAdmin(
  cliente: QueryClient,
  ...datasets: DatasetAdmin[]
): Promise<void> {
  for (const dataset of datasets) {
    await cliente.invalidateQueries({ queryKey: adminClaves[dataset].all });
  }
}
