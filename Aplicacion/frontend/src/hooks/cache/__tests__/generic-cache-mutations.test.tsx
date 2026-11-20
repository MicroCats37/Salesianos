// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useGenericOptimisticUpdate } from "../useGenericOptimisticUpdate";
import { useGenericUpdateMutation } from "../useGenericUpdateMutation";

interface Item {
  id: number;
}

function createWrapper(client: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

describe("the optimistic update", () => {
  it("rolls the cache back when the mutation fails", async () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], [{ id: 1 } as Item]);

    const { result } = renderHook(
      () =>
        useGenericOptimisticUpdate<Item[], { id: number }>({
          queryKey: ["catalogo", "list"],
          mutationFn: async () => {
            throw new Error("boom");
          },
          updaterFn: (current, variables) =>
            (current ?? []).map((item) =>
              item.id === variables.id ? { id: 99 } : item,
            ),
          invalidateKeys: [["catalogo"]],
        }),
      { wrapper: createWrapper(client) },
    );

    await act(async () => {
      result.current.mutate({ id: 1 });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(client.getQueryData(["catalogo", "list"])).toEqual([{ id: 1 }]);
  });

  it("removes the optimistic entry when there was no cache before", async () => {
    const client = new QueryClient();

    const { result } = renderHook(
      () =>
        useGenericOptimisticUpdate<Item[], { id: number }>({
          queryKey: ["catalogo", "detail", 9],
          mutationFn: async () => {
            throw new Error("boom");
          },
          updaterFn: (current) => current ?? [],
        }),
      { wrapper: createWrapper(client) },
    );

    await act(async () => {
      result.current.mutate({ id: 1 });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(client.getQueryData(["catalogo", "detail", 9])).toBeUndefined();
  });

  it("invalidates the dataset when the mutation settles", async () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], [{ id: 1 } as Item]);

    const { result } = renderHook(
      () =>
        useGenericOptimisticUpdate<Item[], { id: number }>({
          queryKey: ["catalogo", "list"],
          mutationFn: async () => [{ id: 1 } as Item],
          updaterFn: (current) => current ?? [],
          invalidateKeys: [["catalogo"]],
        }),
      { wrapper: createWrapper(client) },
    );

    await act(async () => {
      result.current.mutate({ id: 1 });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(client.getQueryState(["catalogo", "list"])?.isInvalidated).toBe(true);
  });
});

describe("the update of a dataset", () => {
  it("does not write an array into a paginated envelope", async () => {
    const client = new QueryClient();
    const pagina = {
      items: [{ id: 1 } as Item],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    };
    client.setQueryData(["catalogo", "list"], pagina);

    const { result } = renderHook(
      () =>
        useGenericUpdateMutation<Item, void>({
          queryKey: ["catalogo", "list"],
          mutationFn: async () => ({ id: 2 } as Item),
        }),
      { wrapper: createWrapper(client) },
    );

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(client.getQueryData(["catalogo", "list"])).toEqual(pagina);
  });

  it("does not create a detail that was never read", async () => {
    const client = new QueryClient();

    const { result } = renderHook(
      () =>
        useGenericUpdateMutation<Item, void>({
          queryKey: ["catalogo", "list"],
          mutationFn: async () => ({ id: 2 } as Item),
          detailKey: (item) => ["catalogo", "detail", item.id],
        }),
      { wrapper: createWrapper(client) },
    );

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(client.getQueryData(["catalogo", "detail", 2])).toBeUndefined();
  });
});
