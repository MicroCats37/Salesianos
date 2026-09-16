/**
 * @deprecated Use '@/infra/db' instead.
 * This file re-exports from the unified db module for backward compatibility.
 */
import { getDbDialect } from "@/infra/db/dialect";

// Re-export the dialect getter
export { getDbDialect } from "@/infra/db/dialect";

// Initialize the correct db and schema at module load time
// based on DB_DIALECT so that all imports get the same singleton.
let _db: any;
let _schema: any;

function initDb(): { db: any; schema: any } {
  const dialect = getDbDialect();
  if (dialect === "postgres") {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { getPgDb, pgSchema } = require("@/infra/db/postgres");
    return { db: getPgDb(), schema: pgSchema };
  }
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { getSqliteDb, sqliteSchema } = require("@/infra/db/sqlite");
  return { db: getSqliteDb(), schema: sqliteSchema };
}

const cached = initDb();
_db = cached.db;
_schema = cached.schema;

// Export db and schema directly (not as Proxy) so that db.schema works correctly
// eslint-disable-next-line @typescript-eslint/no-require-imports
export const db: any = _db;
// eslint-disable-next-line @typescript-eslint/no-require-imports
export const schema: any = _schema;
