/**
 * Returns the configured database dialect.
 * Defaults to 'sqlite' if DB_DIALECT is not set or is 'sqlite'.
 */
export function getDbDialect(): "sqlite" | "postgres" {
  const dialect = process.env.DB_DIALECT?.toLowerCase();
  if (dialect === "postgres") return "postgres";
  return "sqlite";
}
