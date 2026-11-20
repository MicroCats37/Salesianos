// @vitest-environment jsdom
import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { createQueryClient } from "@/lib/query-client";
import { ApiQueryError, apiQueryOptions, useApiQuery } from "../useApiQuery";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api", () => ({
  default: { get: getMock },
  api: { get: getMock },
  apiSend: vi.fn(),
}));

vi.mock("@/errors", () => ({
  getErrorMessage: () => "fallo",
  notify: { error: vi.fn(), success: vi.fn() },
}));

function createWrapper(client: ReturnType<typeof createQueryClient>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  };
}

describe("the read of a resource", () => {
  it("puts every response-changing parameter in the key", () => {
    const options = apiQueryOptions({
      queryKey: ["catalogo", "list"],
      url: "/catalogo/paquetes",
      schema: z.object({ ok: z.boolean() }),
      params: { page: 2 },
    });

    expect(options.queryKey).toEqual(["catalogo", "list", { page: 2 }]);
  });

  it("turns a failed read into an ApiQueryError with the HTTP status", async () => {
    getMock.mockRejectedValue({ response: { status: 404 } });

    const client = createQueryClient();
    const { result } = renderHook(
      () =>
        useApiQuery({
          queryKey: ["catalogo", "list"],
          url: "/catalogo/paquetes",
          schema: z.object({ ok: z.boolean() }),
          showToast: false,
        }),
      { wrapper: createWrapper(client) },
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeInstanceOf(ApiQueryError);
    expect(result.current.error?.status).toBe(404);
  });
});
