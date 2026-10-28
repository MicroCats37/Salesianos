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
 *    LEGACY FILES are excluded BY NAME here: the Vitest run stays green, the
 *    legacy runner keeps owning its own suites, and the NEW suites of the
 *    same directories (`admin.capacidades.test.ts`, `admin.secciones.test.ts`)
 *    DO run under Vitest.
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
      // Legacy suites of the Node test runner (NOT Vitest suites).
      "src/features/admin/schemas/admin.esquemas.test.ts",
      "src/features/admin/utils/admin.estado.utils.test.ts",
      "src/features/admin/utils/admin.lista.utils.test.ts",
      "src/features/admin/utils/admin.orden.utils.test.ts",
      "src/features/admin/utils/admin.resumen.utils.test.ts",
      // Legacy suite of the registration area, out of the scope of this
      // change: it stays owned by the Node test runner.
      "src/features/inscripciones/utils/*.test.ts",
      "**/node_modules/**",
      "**/dist/**",
      "**/.{idea,git,cache,output,temp}/**",
    ],
  },
});
