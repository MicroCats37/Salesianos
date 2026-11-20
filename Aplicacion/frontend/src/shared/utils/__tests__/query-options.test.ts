import { describe, expect, it } from "vitest";
import {
  datasetQueryOptions,
  gcTimeFor,
  MIN_GC_TIME,
  STALE_TIME,
} from "../query-options";

describe("the staleness policy", () => {
  it("never lets `gcTime` be shorter than `staleTime`", () => {
    expect(gcTimeFor(STALE_TIME.catalogo)).toBeGreaterThanOrEqual(
      STALE_TIME.catalogo,
    );
    expect(gcTimeFor(STALE_TIME.listadoAdministrativo)).toBeGreaterThanOrEqual(
      STALE_TIME.listadoAdministrativo,
    );
  });

  it("keeps money and eligibility at least five minutes", () => {
    expect(gcTimeFor(STALE_TIME.comercial)).toBeGreaterThanOrEqual(MIN_GC_TIME);
    expect(gcTimeFor(STALE_TIME.vivo)).toBe(MIN_GC_TIME);
  });
});

describe("the options of a read", () => {
  it("applies the policy of the kind of the dataset", () => {
    const options = datasetQueryOptions({
      queryKey: ["catalogo"],
      queryFn: async () => 1,
      kind: "catalogo",
    });

    expect(options.staleTime).toBe(STALE_TIME.catalogo);
    expect(options.gcTime).toBe(gcTimeFor(STALE_TIME.catalogo));
  });

  it("lets the caller declare its own staleness", () => {
    const options = datasetQueryOptions({
      queryKey: ["catalogo"],
      queryFn: async () => 1,
      kind: "catalogo",
      staleTime: 1000,
    });

    expect(options.staleTime).toBe(1000);
    expect(options.gcTime).toBe(gcTimeFor(1000));
  });

  it("keeps the key of the read", () => {
    const options = datasetQueryOptions({
      queryKey: ["catalogo", "list", { page: 1 }],
      queryFn: async () => 1,
    });

    expect(options.queryKey).toEqual(["catalogo", "list", { page: 1 }]);
  });
});
