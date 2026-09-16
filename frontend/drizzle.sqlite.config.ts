import { defineConfig } from "drizzle-kit";

const url = process.env.DATABASE_URL ?? "file:./dev.db";
const path = url.replace(/^file:/, "");

export default defineConfig({
  schema: "./src/infra/db/schema/sqlite.ts",
  out: "./drizzle/sqlite",
  dialect: "sqlite",
  dbCredentials: { url: path },
  verbose: true,
  strict: true,
});
