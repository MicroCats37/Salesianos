import {
  type MutationFunction,
  type QueryKey,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { invalidateDatasets } from "@/shared/utils/cache-policy";

interface UseGenericOptimisticUpdateOptions<TData, TVars> {
  /**
   * The EXACT key of the entry that is written optimistically.
   *
   * It is the key of ONE read (a list, a page or a detail), never the
   * namespace of a family: an optimistic write that hits every page of a
   * list duplicates the item in all of them.
   */
  queryKey: QueryKey;
  mutationFn: MutationFunction<TData, TVars>;
  /**
   * The optimistic writer.
   *
   * It receives the EXACT cached value — whatever shape the dataset has (a
   * plain list, a paginated envelope, a detail object) — and returns the
   * value to write. It must NOT change the shape: the shape is the contract
   * of the dataset.
   */
  updaterFn: (currentData: TData | undefined, variables: TVars) => TData;
  /** The keys invalidated when the mutation settles. */
  invalidateKeys?: readonly QueryKey[];
}

/**
 * An optimistic update with a snapshot, a rollback and an invalidation.
 *
 * The whole cycle lives INSIDE the mutation function and not in `onMutate` /
 * `onError` / `onSettled`: a component that unmounts while the mutation is in
 * flight would never roll back and never invalidate, and the cache would keep
 * an answer that the server never gave.
 */
export function useGenericOptimisticUpdate<TData, TVars>({
  queryKey,
  mutationFn,
  updaterFn,
  invalidateKeys,
}: UseGenericOptimisticUpdateOptions<TData, TVars>) {
  const queryClient = useQueryClient();

  return useMutation<TData, Error, TVars>({
    mutationFn: async (variables, context) => {
      // An in-flight refetch must not overwrite the optimistic answer.
      await queryClient.cancelQueries({ queryKey });

      const existed = queryClient.getQueryData(queryKey) !== undefined;
      const previousData = queryClient.getQueryData<TData>(queryKey);

      queryClient.setQueryData<TData>(queryKey, (current) =>
        updaterFn(current, variables),
      );

      try {
        return await mutationFn(variables, context);
      } catch (error) {
        if (existed) {
          queryClient.setQueryData(queryKey, previousData);
        } else {
          /**
           * The optimistic write CREATED the entry. It is removed: a cache
           * that keeps an entry nobody read is an orphan.
           */
          queryClient.removeQueries({ queryKey, exact: true });
        }
        throw error;
      } finally {
        await invalidateDatasets(queryClient, invalidateKeys ?? [queryKey]);
      }
    },
  });
}
