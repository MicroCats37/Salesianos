/**
 * Unified DB factory — single entry point for all database access.
 * Chooses SQLite or PostgreSQL based on DB_DIALECT env var.
 *
 * DB_DIALECT=sqlite  (default) → better-sqlite3
 * DB_DIALECT=postgres               → postgres-js
 *
 * Usage:
 *   import { db, schema } from '@/infra/db';
 *
 * All repository methods must be async and await all db calls.
 * No driver-specific API may leak outside this layer.
 */

import { getDbDialect } from "./dialect";

// Module-level singleton — initialized once per process
let _db: any;
let _schema: any;

function createDb(): { db: any; schema: any } {
  const dialect = getDbDialect();
  if (dialect === "postgres") {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { getPgDb, pgSchema } = require("./postgres");
    return { db: getPgDb(), schema: pgSchema };
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { getSqliteDb, sqliteSchema } = require("./sqlite");
  return { db: getSqliteDb(), schema: sqliteSchema };
}

function getDatabase(): { db: any; schema: any } {
  if (_db === undefined) {
    const result = createDb();
    _db = result.db;
    _schema = result.schema;
  }
  return { db: _db, schema: _schema };
}

// Re-exported from dialect-aware adapters
export { getDbDialect } from "./dialect";

// db is a Proxy so property access delegates to the cached singleton
// eslint-disable-next-line @typescript-eslint/no-require-imports
export const db: any = new Proxy({} as any, {
  get(_target, prop) {
    return getDatabase().db[prop];
  },
});

// schema resolves to the cached schema (assign once so it doesn't re-evaluate)
export const schema: any = getDatabase().schema;
