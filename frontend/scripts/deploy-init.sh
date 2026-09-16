#!/bin/sh
#
# Deployment initialization script.
# Runs the database setup (schema push, seeds, admin creation) inside the
# app container before the Next.js server starts, or manually on the host.
#
# Usage:
#   ./scripts/deploy-init.sh
#
# Environment variables (optional - for admin creation):
#   DB_DIALECT          - sqlite | postgres (default: sqlite)
#   DATABASE_URL        - Connection string (required for postgres)
#   ADMIN_DNI           - DNI number for admin user
#   ADMIN_PASSWORD      - Password for admin user
#   ADMIN_EMAIL         - Email for admin user (optional)
#   ADMIN_NOMBRE        - First name for admin user (optional)
#   ADMIN_APELLIDO      - Last name for admin user (optional)
#   ADMIN_ROLE          - Role: admin_comite | admin_finanzas (optional, default: admin_comite)
#
# Idempotent: safe to run on every container boot.
#
# Examples:
#   # Seed only (SQLite default)
#   ./scripts/deploy-init.sh
#
#   # Seed and create admin
#   ADMIN_DNI=12345678 ADMIN_PASSWORD=securePass123 ./scripts/deploy-init.sh
#
#   # PostgreSQL production
#   DB_DIALECT=postgres DATABASE_URL=postgresql://user:pass@host:5432/db ./scripts/deploy-init.sh

set -e

DB_DIALECT="${DB_DIALECT:-sqlite}"

echo "=== Salesianos Fest Deployment Init ==="
echo "DB_DIALECT: $DB_DIALECT"
echo ""

# Step 1: Push schema (creates/updates tables)
echo "Step 1: Pushing database schema..."
if [ "$DB_DIALECT" = "postgres" ]; then
    npm run db:push:postgres
else
    npm run db:push:sqlite
fi
echo ""

# Step 2: Run seeds
echo "Step 2: Running database seeds..."
npm run db:seed
echo ""

# Step 3: Create admin user from env vars (if provided)
if [ -n "$ADMIN_DNI" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "Step 3: Creating admin user from environment variables..."
    npm run admin:create -- \
        --dni "$ADMIN_DNI" \
        --password "$ADMIN_PASSWORD" \
        ${ADMIN_EMAIL:+--email "$ADMIN_EMAIL"} \
        ${ADMIN_NOMBRE:+--nombre "$ADMIN_NOMBRE"} \
        ${ADMIN_APELLIDO:+--apellido "$ADMIN_APELLIDO"} \
        ${ADMIN_ROLE:+--role "$ADMIN_ROLE"}
    echo ""
else
    echo "Step 3: Skipping admin creation (ADMIN_DNI or ADMIN_PASSWORD not set)"
    echo ""
fi

echo "=== Deployment Init Complete ==="
