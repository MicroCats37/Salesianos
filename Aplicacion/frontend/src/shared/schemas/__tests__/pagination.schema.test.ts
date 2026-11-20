import { describe, expect, it } from "vitest";
import { z } from "zod";
import { isPaginatedResult, paginatedResultSchema } from "../pagination.schema";

describe("the only pagination shape of the target", () => {
  it("mirrors the frozen envelope", () => {
    const schema = paginatedResultSchema(z.object({ id: z.number() }));

    const parsed = schema.parse({
      items: [{ id: 1 }],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    });

    expect(parsed.items).toHaveLength(1);
    expect(parsed.page_size).toBe(25);
  });

  it("rejects the deprecated form with the pagination outside `data`", () => {
    const schema = paginatedResultSchema(z.object({ id: z.number() }));

    expect(() =>
      schema.parse({
        data: [],
        count: 0,
        page: 1,
        pageSize: 25,
        totalPages: 0,
      }),
    ).toThrow();
  });

  it("recognises the envelope and only the envelope", () => {
    expect(
      isPaginatedResult({
        items: [],
        total: 0,
        page: 1,
        page_size: 25,
        total_pages: 0,
      }),
    ).toBe(true);

    expect(isPaginatedResult([])).toBe(false);
    expect(isPaginatedResult({ items: [] })).toBe(false);
    expect(isPaginatedResult(null)).toBe(false);
    expect(isPaginatedResult(undefined)).toBe(false);
  });
});
