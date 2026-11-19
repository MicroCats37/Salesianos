import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

/**
 * Vitest setup of the frontend.
 *
 * Two decisions live here:
 *
 * 1. The `@` alias points to `src`, exactly like `tsconfig.json`: a test and
 *    the module it verifies MUST resolve the same file.
 * 2. The environment is `node` by default: the suites of this repository
 *    verify schemas, mappings and URL contracts, which are dependency-free
 *    modules. A COMPONENT suite declares `// @vitest-environment jsdom` at
 *    the top of its file: only the suites that render React pay the cost of
 *    the DOM.
 *
 * The legacy exclusions of the previous configuration pointed at suites of
 * `src/features/admin/**` and `src/features/inscripciones/**` that no longer
 * exist: the rebuild emptied `src/features/**` and the suites went with it.
 * A Vitest run does not fail because a pattern matches nothing, but the dead
 * list was misleading, so it is gone.
 */
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    environment: "node",
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    exclude: [
      "**/node_modules/**",
      "**/dist/**",
      "**/.{idea,git,cache,output,temp}/**",
    ],
  },
});
