import { beforeEach, describe, expect, it, vi } from "vitest";

const { useApiQueryMock } = vi.hoisted(() => ({
  useApiQueryMock: vi.fn(),
}));

vi.mock("@/hooks", () => ({
  useApiQuery: useApiQueryMock,
}));

import { useVideosLista } from "./useVideos";

describe("useVideosLista", () => {
  beforeEach(() => {
    useApiQueryMock.mockReset();
    useApiQueryMock.mockReturnValue({});
  });

  it("polls every ten seconds while the videos page is active", () => {
    useVideosLista();

    expect(useApiQueryMock).toHaveBeenCalledWith(
      expect.objectContaining({
        queryOptions: expect.objectContaining({
          refetchInterval: 10_000,
          refetchIntervalInBackground: false,
        }),
      }),
    );
  });
});
