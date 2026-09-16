/**
 * E2E smoke test for salesianos-fest-2026
 *
 * Run with:
 *   cd frontend && npm run dev   (in background, on port 3000)
 *   cd frontend && npx tsx scripts/smoke-e2e.ts
 *
 * Or with custom URL:
 *   NEXT_PUBLIC_APP_URL=http://localhost:3000 npx tsx scripts/smoke-e2e.ts
 */

import "dotenv/config";
import { readdirSync, readFileSync } from "fs";
import { join } from "path";

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

async function step(name: string, fn: () => Promise<void>) {
  process.stdout.write(`  ${name}... `);
  try {
    await fn();
    console.log("✓ PASS");
  } catch (error) {
    console.log("✗ FAIL");
    console.error(`    ${(error as Error).message}`);
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Task 8.2 + 8.3 + 8.4 — Auth flow smoke test
// ---------------------------------------------------------------------------

async function runAuthSmokeTest() {
  console.log("\n=== Auth Flow E2E Smoke Test ===\n");

  const timestamp = Date.now();
  const email = `test-${timestamp}@example.com`;
  const password = "TestPassword123";

  // Cookies will be captured from Set-Cookie headers
  let cookies = "";

  await step("POST /api/auth/register (201/200 — new user)", async () => {
    const res = await fetch(`${BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        nombre: "Test",
        apellido: "User",
        dni: String(timestamp).slice(-8),
        telefono: "987654321",
      }),
    });
    if (res.status !== 201 && res.status !== 200) {
      throw new Error(`expected 201|200, got ${res.status}`);
    }
    const setCookie = res.headers.get("set-cookie");
    if (!setCookie) throw new Error("no Set-Cookie header received");
    cookies = setCookie.split(";")[0] ?? "";
    const json = await res.json();
    if (!json.success)
      throw new Error(`response not success: ${JSON.stringify(json)}`);
  });

  await step("POST /api/auth/register (409 — duplicate email)", async () => {
    const res = await fetch(`${BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        nombre: "Dup",
        apellido: "User",
        dni: "99999999",
        telefono: "111111111",
      }),
    });
    if (res.status !== 409) throw new Error(`expected 409, got ${res.status}`);
  });

  await step("GET /api/auth/me (200 — session restored)", async () => {
    const res = await fetch(`${BASE_URL}/api/auth/me`, {
      headers: { Cookie: cookies },
    });
    if (res.status !== 200) throw new Error(`expected 200, got ${res.status}`);
    const json = await res.json();
    if (!json.success || json.data?.email !== email) {
      throw new Error(`expected user ${email}, got: ${JSON.stringify(json)}`);
    }
  });

  await step("POST /api/auth/login (200 — valid credentials)", async () => {
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: email, password }),
    });
    if (res.status !== 200) throw new Error(`expected 200, got ${res.status}`);
    const setCookie = res.headers.get("set-cookie");
    if (!setCookie) throw new Error("no Set-Cookie on login");
    cookies = setCookie.split(";")[0] ?? "";
  });

  await step(
    "POST /api/auth/logout (200 — clears session cookie)",
    async () => {
      const res = await fetch(`${BASE_URL}/api/auth/logout`, {
        method: "POST",
        headers: { Cookie: cookies },
      });
      if (res.status !== 200)
        throw new Error(`expected 200, got ${res.status}`);
      const setCookie = res.headers.get("set-cookie");
      if (!setCookie || !setCookie.includes("Max-Age=0")) {
        throw new Error(`logout should set Max-Age=0, got: ${setCookie}`);
      }
    },
  );

  console.log("\n  Auth flow tests: ALL PASSED\n");
}

// ---------------------------------------------------------------------------
// Task 8.4 — Verify HttpOnly flag on session cookie
// ---------------------------------------------------------------------------

async function verifyHttpOnlyFlag() {
  console.log("\n=== HttpOnly Cookie Verification ===\n");

  const timestamp = Date.now();
  const email = `test-httponly-${timestamp}@example.com`;
  const password = "TestPassword123";

  // Register first
  await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      nombre: "HttpOnly",
      apellido: "Test",
      dni: String(timestamp).slice(-8),
      telefono: "987654321",
    }),
  });

  await step(
    "POST /api/auth/login — Set-Cookie has HttpOnly flag",
    async () => {
      const res = await fetch(`${BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier: email, password }),
      });
      if (res.status !== 200)
        throw new Error(`expected 200, got ${res.status}`);
      const setCookie = res.headers.get("set-cookie");
      if (!setCookie) throw new Error("no Set-Cookie header");
      if (!setCookie.toLowerCase().includes("httponly")) {
        throw new Error(`HttpOnly flag missing in: ${setCookie}`);
      }
    },
  );

  console.log("\n  HttpOnly verification: PASSED\n");
}

// ---------------------------------------------------------------------------
// Task 8.5 — Verify schema is driver-agnostic (SQLite-only for MVP)
// and that db:push succeeds
// ---------------------------------------------------------------------------

async function verifySchemaCompatibility() {
  console.log("\n=== Schema Compatibility Verification ===\n");

  const schemaDir = join(process.cwd(), "src/infra/drizzle/schema");

  await step(
    "All schema files use sqlite-core (no pg-core mixed in)",
    async () => {
      const files = readdirSync(schemaDir).filter(
        (f) => f.endsWith(".ts") && f !== "index.ts",
      );

      for (const file of files) {
        const content = readFileSync(join(schemaDir, file), "utf-8");
        const hasSqliteCore = content.includes("drizzle-orm/sqlite-core");
        const hasPgCore = content.includes("drizzle-orm/pg-core");
        if (hasPgCore) {
          throw new Error(
            `Schema file "${file}" imports pg-core — not driver-agnostic. ` +
              "For Postgres parity, schemas must be duplicated (Phase 8 spec).",
          );
        }
        if (!hasSqliteCore) {
          throw new Error(
            `Schema file "${file}" has no sqlite-core import — unknown driver.`,
          );
        }
      }
    },
  );

  await step(
    "npm run db:push — schema pushes to SQLite successfully",
    async () => {
      const { exec } = await import("child_process");
      const cwd = process.cwd();

      const result = await new Promise<{
        stdout: string;
        stderr: string;
        code: number;
      }>((resolve, reject) => {
        exec(
          "npm run db:push",
          { cwd, timeout: 60_000 },
          (err, stdout, stderr) => {
            if (err) reject(err);
            else resolve({ stdout, stderr, code: 0 });
          },
        );
      }).catch((e: Error & { code?: number }) => ({
        stdout: "",
        stderr: e.message,
        code: e.code ?? 1,
      }));

      if (result.code !== 0) {
        throw new Error(
          `db:push failed (exit ${result.code}): ${result.stderr}`.slice(
            0,
            300,
          ),
        );
      }
    },
  );

  console.log("\n  Schema compatibility: PASSED\n");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log("\n========================================");
  console.log("  E2E Smoke Tests — salesianos-fest-2026");
  console.log("========================================");
  console.log(`  BASE_URL: ${BASE_URL}`);

  try {
    await runAuthSmokeTest();
    await verifyHttpOnlyFlag();
    await verifySchemaCompatibility();

    console.log("\n========================================");
    console.log("  ALL TESTS PASSED");
    console.log("========================================\n");
  } catch (err) {
    console.error("\n========================================");
    console.error("  SMOKE TEST FAILED");
    console.error("========================================\n");
    process.exit(1);
  }
}

main();
