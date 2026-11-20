/**
 * The query keys of the edition dataset.
 *
 * They live HERE and nowhere else: a component never spells a key
 * (`salesianos-api-data`, "one dataset, one namespace").
 *
 * The dataset is the CURRENT EDITION (`RT-ED-01`). It is a singleton read:
 * it has no filter and no page, so its key carries the edition identity only.
 * The scope is `edicion` — NOT `public` — because the edition is one dataset
 * of the whole product: the catalogue, the store and the inscription wizard
 * read the same edition and must share this namespace.
 *
 * The factory lives in the feature that consumes it first (`features/public`).
 * When the roots are widened to a dedicated `features/edition/**`, the move is
 * a one-file change: the literals are here and nowhere else.
 */
export const edicionClaves = {
  todas: ["edicion"] as const,
  actual: () => [...edicionClaves.todas, "actual"] as const,
};
