import {
  type MutationFunction,
  type QueryKey,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  invalidateDatasets,
  updateCachedDetail,
  updateCachedList,
} from "@/shared/utils/cache-policy";

interface UseGenericUpdateMutationOptions<
  TItem extends { id: string | number },
  TVars = unknown,
> {
  /** The EXACT key of the list read that is updated in place. */
  queryKey: QueryKey;
  mutationFn: MutationFunction<TItem, TVars>;
  /**
   * The EXACT key of the detail read.
   *
   * Without it NO detail is written: the key of a detail is not
   * `[...listKey, id]` by convention, it is whatever the owning dataset
   * declares.
   */
  detailKey?: (item: TItem) => QueryKey;
  /** The keys invalidated when the mutation settles. */
  invalidateKeys?: readonly QueryKey[];
}

/**
 * An update that writes into the cache ONLY when it knows the exact shape.
 *
 * A list that is a plain array of items is updated in place. A list that is a
 * paginated envelope is NOT: the page that holds the item is unknown, so the
 * invalidation does the work. A detail is NOT created: only a detail that was
 * already read is updated.
 */
export function useGenericUpdateMutation<
  TItem extends { id: string | number },
  TVars = unknown,
>({
  queryKey,
  mutationFn,
  detailKey,
  invalidateKeys,
}: UseGenericUpdateMutationOptions<TItem, TVars>) {
  const queryClient = useQueryClient();

  return useMutation<TItem, Error, TVars>({
    mutationFn: async (variables, context) => {
      try {
        const updatedItem = await mutationFn(variables, context);

        updateCachedList<TItem>(queryClient, queryKey, (items) =>
          items.map((item) =>
            item.id === updatedItem.id ? updatedItem : item,
          ),
        );

        if (detailKey) {
          updateCachedDetail<TItem>(
            queryClient,
            detailKey(updatedItem),
            () => updatedItem,
          );
        }

        return updatedItem;
      } finally {
        await invalidateDatasets(queryClient, invalidateKeys ?? [queryKey]);
      }
    },
  });
}
