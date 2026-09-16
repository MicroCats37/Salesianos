/**
 * @deprecated Use '@/infra/db' (schema export) instead.
 * This file re-exports from the SQLite schema for backward compatibility.
 * For PostgreSQL, use '@/infra/db' and set DB_DIALECT=postgres.
 */
export * from "@/infra/db/schema/sqlite";
