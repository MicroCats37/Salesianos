import {
  drizzle as drizzlePg,
  type PostgresJsDatabase,
} from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as pgSchema from "@/infra/db/schema/postgres";

const url =
  process.env.DATABASE_URL ?? "postgresql://localhost:5432/salesianos";

function createPgClient(): PostgresJsDatabase<typeof pgSchema> {
  const client = postgres(url, { prepare: false });
  return drizzlePg(client, { schema: pgSchema });
}

let pgDb: PostgresJsDatabase<typeof pgSchema> | undefined;

export function getPgDb(): PostgresJsDatabase<typeof pgSchema> {
  if (process.env.NODE_ENV !== "production") {
    if (!pgDb) {
      pgDb = createPgClient();
    }
    return pgDb;
  }
  return createPgClient();
}

export { pgSchema };
