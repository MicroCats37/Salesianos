import { defineConfig } from "drizzle-kit";

const url = process.env.DATABASE_URL;
if (!url) {
  throw new Error("DATABASE_URL is required for PostgreSQL drizzle config");
}

export default defineConfig({
  schema: "./src/infra/db/schema/postgres.ts",
  out: "./drizzle/postgres",
  dialect: "postgresql",
  dbCredentials: { url },
  verbose: true,
  strict: true,
});
