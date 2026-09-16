import { defineConfig } from "drizzle-kit";

const url = process.env.DATABASE_URL ?? "file:./dev.db";
const isSqlite = url.startsWith("file:");

export default defineConfig({
  schema: "./src/infra/drizzle/schema/index.ts",
  out: "./drizzle",
  dialect: isSqlite ? "sqlite" : "postgresql",
  dbCredentials: isSqlite ? { url: url.replace("file:", "") } : { url },
  verbose: true,
  strict: true,
});
