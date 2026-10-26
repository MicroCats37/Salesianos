import { z } from "zod";

/**
 * adminPaginadoSchema — factory of the 1:1 mirror of the backend
 * `core.pagination.PaginatedData[T]`.
 *
 * The administration area does NOT reuse the third, incompatible
 * `shared/types/api.types.ts::PaginatedResponse` shape: the canonical
 * container of every admin list is
 * `{ items[], total, page, page_size, total_pages }`
 * (`sdd/administracion-operativa-fest/admin-surface` §5.1).
 *
 * The factory keeps the item type EXPLICIT: there is no `z.any()` and no
 * generic `data` contract anywhere in the admin layer
 * (`contract/api-wrapper-presenter-contract.md` §5 and §7).
 */
export function adminPaginadoSchema<TItem extends z.ZodType>(item: TItem) {
  return z.object({
    items: z.array(item),
    total: z.number(),
    page: z.number(),
    page_size: z.number(),
    total_pages: z.number(),
  });
}

/** Shape of the canonical administration pagination container. */
export interface AdminPaginado<TItem extends z.ZodType> {
  items: z.infer<TItem>[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
