import {
  type MutationFunction,
  type QueryKey,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  invalidateDatasets,
  removeCachedEntry,
  updateCachedList,
} from "@/shared/utils/cache-policy";

interface UseGenericDeleteMutationOptions<
  TItem extends { id: string | number },
  TId extends string | number = TItem["id"],
> {
  /** The EXACT key of the list read the item is removed from. */
  queryKey: QueryKey;
  mutationFn: MutationFunction<void, TId>;
  /**
   * The EXACT key of the detail read.
   *
   * Without it NO detail is removed: the key of a detail is not
   * `[...listKey, id]` by convention, it is whatever the owning dataset
   * declares.
   */
  detailKey?: (id: TId) => QueryKey;
  /** The keys invalidated when the mutation settles. */
  invalidateKeys?: readonly QueryKey[];
}

/**
 * A deletion that writes into the cache ONLY when it knows the exact shape.
 *
 * The item is removed from a plain list. A paginated envelope is NOT touched:
 * the page that holds the item is unknown, so the invalidation does the work.
 * An absent list is NOT turned into an empty list: there was nothing there.
 */
export function useGenericDeleteMutation<
  TItem extends { id: string | number },
  TId extends string | number = TItem["id"],
>({
  queryKey,
  mutationFn,
  detailKey,
  invalidateKeys,
}: UseGenericDeleteMutationOptions<TItem, TId>) {
  const queryClient = useQueryClient();

  return useMutation<void, Error, TId>({
    mutationFn: async (variables, context) => {
      try {
        await mutationFn(variables, context);

        updateCachedList<TItem>(queryClient, queryKey, (items) =>
          items.filter((item) => item.id !== variables),
        );

        if (detailKey) {
          removeCachedEntry(queryClient, detailKey(variables));
        }
      } finally {
        await invalidateDatasets(queryClient, invalidateKeys ?? [queryKey]);
      }
    },
  });
}
