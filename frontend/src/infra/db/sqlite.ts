import Database from "better-sqlite3";
import {
  type BetterSQLite3Database,
  drizzle as drizzleSqlite,
} from "drizzle-orm/better-sqlite3";
import * as sqliteSchema from "@/infra/db/schema/sqlite";

const url = process.env.DATABASE_URL ?? "file:./dev.db";

function createSqliteClient(): BetterSQLite3Database<typeof sqliteSchema> {
  const path = url.replace(/^file:/, "");
  const sqlite = new Database(path);
  return drizzleSqlite(sqlite, { schema: sqliteSchema });
}

let sqliteDb: BetterSQLite3Database<typeof sqliteSchema> | undefined;

export function getSqliteDb(): BetterSQLite3Database<typeof sqliteSchema> {
  if (process.env.NODE_ENV !== "production") {
    if (!sqliteDb) {
      sqliteDb = createSqliteClient();
    }
    return sqliteDb;
  }
  return createSqliteClient();
}

export { sqliteSchema };
