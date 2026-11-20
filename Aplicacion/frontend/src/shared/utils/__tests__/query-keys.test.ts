import { describe, expect, it } from "vitest";
import {
  buildQueryKey,
  createDatasetQueryKeys,
  queryParams,
} from "../query-keys";

describe("the parameters of a read", () => {
  it("drops the parameter that does not change the answer", () => {
    expect(queryParams({ page: 1, q: undefined })).toEqual({ page: 1 });
  });
});

describe("the key of a read", () => {
  it("keeps the key of the family when there are no parameters", () => {
    expect(buildQueryKey(["catalogo", "list"])).toEqual(["catalogo", "list"]);
  });

  it("puts every response-changing parameter in the key", () => {
    expect(buildQueryKey(["catalogo", "list"], { page: 2, q: "x" })).toEqual([
      "catalogo",
      "list",
      { page: 2, q: "x" },
    ]);
  });

  it("treats an undefined parameter as no parameter at all", () => {
    expect(
      buildQueryKey(["catalogo", "list"], { page: 1, q: undefined }),
    ).toEqual(buildQueryKey(["catalogo", "list"], { page: 1 }));
  });

  it("keeps the key of the family when EVERY parameter is absent", () => {
    // `{ page: undefined }` is not a parameter object: the read is the read of
    // the family, so it is ONE cache entry and not two.
    expect(buildQueryKey(["catalogo", "list"], { page: undefined })).toEqual([
      "catalogo",
      "list",
    ]);
    expect(buildQueryKey(["catalogo", "list"], {})).toEqual([
      "catalogo",
      "list",
    ]);
  });
});

describe("the key factory of a dataset", () => {
  it("gives one namespace to the dataset", () => {
    const keys = createDatasetQueryKeys<{ page: number }>("catalogo");

    expect(keys.all).toEqual(["catalogo"]);
    expect(keys.list).toEqual(["catalogo", "list"]);
    expect(keys.listPage({ page: 3 })).toEqual([
      "catalogo",
      "list",
      { page: 3 },
    ]);
    expect(keys.detail(7)).toEqual(["catalogo", "detail", 7]);
  });

  it("keeps every read of the dataset under the same root", () => {
    const keys = createDatasetQueryKeys("catalogo");

    expect(keys.list[0]).toBe(keys.all[0]);
    expect(keys.detail(1)[0]).toBe(keys.all[0]);
  });
});
