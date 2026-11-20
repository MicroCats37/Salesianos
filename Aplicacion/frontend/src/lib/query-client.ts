import { QueryClient } from "@tanstack/react-query";

/**
 * The default staleness of a read that does not declare its own.
 *
 * The data contract gives a staleness per KIND of dataset (catalogues 5-10
 * min, administrative lists 30 s, commercial/transient state 15 s, live
 * previews 0). The client default is the commercial one: a read that does not
 * declare its policy is a transient read.
 */
export const DEFAULT_STALE_TIME = 15 * 1000;

/** The minimum lifetime of a cached entry that nobody is looking at. */
export const DEFAULT_GC_TIME = 5 * 60 * 1000;

/**
 * The HTTP status of a failed read, when the error carries one.
 *
 * `ApiQueryError` exposes it directly; an axios error carries it inside
 * `response`.
 */
function statusOf(error: unknown): number | undefined {
  const candidate = error as
    | { status?: number; response?: { status?: number } }
    | undefined;

  return candidate?.status ?? candidate?.response?.status;
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: DEFAULT_STALE_TIME,
        gcTime: DEFAULT_GC_TIME,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        /**
         * A rejected read is NOT repeated when the answer will not change:
         * 401, 403, 404, 409 and 422 are DECISIONS of the server, not
         * accidents of the network. Only 408 and 429 are worth retrying.
         */
        retry: (failureCount, error) => {
          const status = statusOf(error);

          if (status !== undefined && status >= 400 && status < 500) {
            return status === 408 || status === 429;
          }

          return failureCount < 2;
        },
      },
      mutations: {
        /**
         * A mutation is NEVER repeated automatically: the exactly-once rules
         * (idempotency keys, activations) belong to the server.
         */
        retry: false,
      },
    },
  });
}
