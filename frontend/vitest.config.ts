import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

/**
 * Vitest setup of the frontend.
 *
 * Two decisions live here:
 *
 * 1. The `@` alias points to `src`, exactly like `tsconfig.json`: a test and
 *    the module it verifies MUST resolve the same file.
 * 2. The legacy suites of the administration and registration areas still run
 *    with the Node test runner (`node --experimental-strip-types --test`).
 *    Vitest reports a file without a Vitest suite as an error, so those
 *    directories are EXCLUDED here: the Vitest run stays green and the
 *    legacy runner keeps owning its own suites.
 *
 * The environment is `node` by default: the suites of this repository verify
 * schemas, mappings and URL contracts, which are dependency-free modules. A
 * COMPONENT suite declares `// @vitest-environment jsdom` at the top of its
 * file: only the suites that render React pay the cost of the DOM.
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
      "src/features/admin/schemas/*.test.ts",
      "src/features/admin/utils/*.test.ts",
      "src/features/inscripciones/utils/*.test.ts",
      "**/node_modules/**",
      "**/dist/**",
      "**/.{idea,git,cache,output,temp}/**",
    ],
  },
});
