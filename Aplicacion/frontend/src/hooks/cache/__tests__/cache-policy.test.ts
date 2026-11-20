import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import {
  invalidateDatasets,
  removeCachedEntry,
  updateCachedDetail,
  updateCachedList,
  updateCachedPage,
} from "@/shared/utils/cache-policy";

const PAGINA = {
  items: [{ id: 1 }],
  total: 1,
  page: 1,
  page_size: 25,
  total_pages: 1,
};

describe("the shape-safe cache policy", () => {
  it("does not write an array into a paginated envelope", () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], PAGINA);

    const written = updateCachedList<{ id: number }>(
      client,
      ["catalogo", "list"],
      (items) => [...items, { id: 2 }],
    );

    expect(written).toBe(false);
    expect(client.getQueryData(["catalogo", "list"])).toEqual(PAGINA);
  });

  it("does not create a list that was never read", () => {
    const client = new QueryClient();

    const written = updateCachedList<{ id: number }>(
      client,
      ["catalogo", "list"],
      (items) => [...items, { id: 2 }],
    );

    expect(written).toBe(false);
    expect(client.getQueryData(["catalogo", "list"])).toBeUndefined();
  });

  it("writes into a paginated envelope preserving its shape", () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], PAGINA);

    const written = updateCachedPage<{ id: number }>(
      client,
      ["catalogo", "list"],
      (current) => ({ ...current, total: current.total + 1 }),
    );

    expect(written).toBe(true);
    expect(client.getQueryData(["catalogo", "list"])).toEqual({
      ...PAGINA,
      total: 2,
    });
  });

  it("does not create a detail that was never read", () => {
    const client = new QueryClient();

    const written = updateCachedDetail<{ id: number }>(
      client,
      ["catalogo", "detail", 9],
      (detail) => detail,
    );

    expect(written).toBe(false);
    expect(client.getQueryData(["catalogo", "detail", 9])).toBeUndefined();
  });

  it("removes exactly one entry and never a family", () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "detail", 9], { id: 9 });
    client.setQueryData(["catalogo", "detail", 10], { id: 10 });

    removeCachedEntry(client, ["catalogo", "detail", 9]);

    expect(client.getQueryData(["catalogo", "detail", 9])).toBeUndefined();
    expect(client.getQueryData(["catalogo", "detail", 10])).toEqual({ id: 10 });
  });
});

describe("the invalidation policy", () => {
  it("invalidates only the affected dataset", async () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], [{ id: 1 }]);
    client.setQueryData(["pagos", "list"], [{ id: 2 }]);

    await invalidateDatasets(client, [["catalogo"]]);

    expect(client.getQueryState(["catalogo", "list"])?.isInvalidated).toBe(
      true,
    );
    expect(client.getQueryState(["pagos", "list"])?.isInvalidated).toBe(false);
  });

  it("does nothing when no key is declared", async () => {
    const client = new QueryClient();
    client.setQueryData(["catalogo", "list"], [{ id: 1 }]);

    await invalidateDatasets(client);

    expect(client.getQueryState(["catalogo", "list"])?.isInvalidated).toBe(
      false,
    );
  });
});
