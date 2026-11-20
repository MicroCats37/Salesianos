import { z } from "zod";

/**
 * THE pagination shape of the target. And the only one.
 *
 * Frozen by `FREEZE-ENV-1.0.0` (evidence/contracts/FR-01 §4.3): the pagination
 * lives INSIDE `data` as `{ items, total, page, page_size, total_pages }`.
 * The old form (`PaginatedApiResponse`, with the pagination in `meta`) is
 * deprecated and NO route of `Aplicacion/backend` uses it.
 *
 * A cache writer that does not know the EXACT shape of a dataset must not
 * write into it: it invalidates instead (see `@/shared/utils/cache-policy`).
 */
export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * The Zod mirror of `PaginatedResult`.
 *
 * ONE factory, parametrized by the item schema: the shape of the envelope is
 * never replicated per module (FR-01 §8.5).
 */
export function paginatedResultSchema<T>(
  itemSchema: z.ZodType<T>,
): z.ZodType<PaginatedResult<T>> {
  return z.object({
    items: z.array(itemSchema),
    total: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive(),
    total_pages: z.number().int().nonnegative(),
  });
}

/**
 * The runtime guard of the shape.
 *
 * A cache writer asks this question BEFORE writing: "is what I am about to
 * overwrite a paginated envelope?". If the answer is no, the writer leaves the
 * cache alone and lets the invalidation do the work.
 */
export function isPaginatedResult(
  value: unknown,
): value is PaginatedResult<unknown> {
  if (typeof value !== "object" || value === null) return false;

  const candidate = value as Record<string, unknown>;

  return (
    Array.isArray(candidate.items) &&
    typeof candidate.total === "number" &&
    typeof candidate.page === "number" &&
    typeof candidate.page_size === "number" &&
    typeof candidate.total_pages === "number"
  );
}
