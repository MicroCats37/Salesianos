# Salesianos Fest - Deployment Guide

## Architecture

The Salesianos Fest application is a **Next.js fullstack app** — UI, API routes, and backend logic all run in a single Next.js process. There is no separate backend service.

Database dialect is switched via the `DB_DIALECT` environment variable, allowing SQLite for development and PostgreSQL for production with zero code changes.

## Database Support

| Environment | Database | Dialect switch | Status |
|-------------|----------|----------------|--------|
| Development | SQLite (`file:./dev.db`) | `DB_DIALECT=sqlite` | ✅ Fully supported |
| Production (Docker) | PostgreSQL 16 | `DB_DIALECT=postgres` | ✅ Fully supported |

## Dialect Switch Architecture

```
Next.js → repositories (async API) → db/index.ts → db/sqlite.ts  OR  db/postgres.ts
                                                    ↓                    ↓
                                              sqlite schema        postgres schema
                                           (src/infra/db/          (src/infra/db/
                                            schema/sqlite.ts)      schema/postgres.ts)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_DIALECT` | `sqlite` | `sqlite` or `postgres` |
| `DATABASE_URL` | `file:./dev.db` (sqlite) | Connection string |
| `PORT` | `7000` | Container port |

**SQLite** (development default):
```
DB_DIALECT=sqlite
DATABASE_URL=file:./dev.db
```

**PostgreSQL** (production):
```
DB_DIALECT=postgres
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Repository Layer

All repository methods are `async` and return `Promise<T>`. SQLite uses synchronous Drizzle operations internally (which resolve immediately), while PostgreSQL uses `postgres-js` for truly async operations. The repository interface is identical for both dialects — no driver-specific APIs leak outside `db/`.

## Docker Deployment

### 1. Build and run

```bash
docker compose up --build -d
```

This starts:
- `db` — PostgreSQL 16 on port 6667 (host)
- `app` — Next.js fullstack on port 6666 (host)

Wait for both services to be healthy (check `docker compose ps`).

### 2. Initialize the database (manual — run from HOST)

After the stack is up, run these commands from your **host machine** (not inside the container). Your local `frontend/` directory has the required dev tools (`tsx`, `drizzle-kit`).

```bash
# Push the schema to PostgreSQL
DB_DIALECT=postgres DATABASE_URL=postgresql://salesianos:salesianos@localhost:6667/salesianos npm run db:push:postgres

# Run the seeds
DB_DIALECT=postgres DATABASE_URL=postgresql://salesianos:salesianos@localhost:6667/salesianos npm run db:seed

# Create an admin user
DB_DIALECT=postgres DATABASE_URL=postgresql://salesianos:salesianos@localhost:6667/salesianos npm run admin:create -- --dni 12345678 --password "your-password" --nombre "John" --apellido "Doe"
```

> **Note:** The runner stage uses a lean standalone image without dev tools (`tsx`/`drizzle-kit`). Seed and admin commands must be run from the host against `localhost:6667`.

### 3. Verify the app

```
curl http://localhost:6666/api/health
```

Expected: `{"status":"ok"}`

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `7000` | Container port (internal) |
| `FRONTEND_PORT` | `6666` | Host port for the app |
| `DB_EXTERNAL_PORT` | `6667` | Host port for PostgreSQL |
| `DB_DIALECT` | `sqlite` | `sqlite` or `postgres` |
| `DATABASE_URL` | `file:./dev.db` | SQLite path or PostgreSQL connection string |
| `DB_NAME` | `salesianos` | PostgreSQL database name (docker-compose) |
| `DB_USER` | `salesianos` | PostgreSQL user (docker-compose) |
| `DB_PASSWORD` | `salesianos` | PostgreSQL password (docker-compose) |
| `JWT_SECRET` | (required) | JWT signing secret (min 32 chars for jose) |
| `JWT_ACCESS_TOKEN_TTL_SECONDS` | `604800` | Access token TTL (7 days) |
| `JWT_REFRESH_TOKEN_TTL_SECONDS` | `2592000` | Refresh token TTL (30 days) |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:6666` | Public app URL |
| `COOKIE_SECURE` | `false` | Cookies require HTTPS |

## Creating Admin Users

### From host (recommended after docker compose up)

```bash
DB_DIALECT=postgres DATABASE_URL=postgresql://salesianos:salesianos@localhost:6667/salesianos \
  npm run admin:create -- --dni 12345678 --password "your-password" --nombre "John" --apellido "Doe"
```

### Via environment variables (before running seed commands)

```bash
# Set these in your .env before running db:seed / admin:create
ADMIN_DNI=12345678
ADMIN_PASSWORD=securePass123
ADMIN_EMAIL=admin@example.com
ADMIN_NOMBRE=John
ADMIN_APELLIDO=Doe
ADMIN_ROLE=admin_comite
```

**Important:**
- Admin creation is CLI-only (no public HTTP endpoint)
- Passwords are hashed with bcrypt (12 rounds)
- Admin creation is idempotent (can be re-run safely)

## Database Scripts

| Script | Description |
|--------|-------------|
| `npm run db:generate:sqlite` | Generate migrations for SQLite |
| `npm run db:generate:postgres` | Generate migrations for PostgreSQL |
| `npm run db:push:sqlite` | Push schema to SQLite |
| `npm run db:push:postgres` | Push schema to PostgreSQL |
| `npm run db:seed` | Seed database (dialect-aware) |
| `npm run db:studio:sqlite` | Open SQLite Studio |
| `npm run db:studio:postgres` | Open PostgreSQL Studio |
| `npm run admin:create` | Create/update admin user |

## Database Seeds

The seed script (`npm run db:seed`) populates:

- **Bases**: Version `BASES-SF26-2026-09-06`
- **Disciplines**: fulbito_var, fulbito_dam, voley_mix, basket_var
- **Categories**: Age-based categories per discipline
- **Promotions**: 1970 through current year (idempotent)
- **Admin user**: Test admin with DNI `00000000` (dev only)

The seed script is dialect-aware — it uses the same `DB_DIALECT` mechanism and works with both SQLite and PostgreSQL.

### Promotion Seed Behavior

- Creates promotions from **1970 to current year**
- **Idempotent**: Running multiple times is safe
- Uses `onConflictDoNothing` for non-disruptive inserts

## Development Workflow

```bash
# Start dev server (SQLite default)
npm run dev

# Push schema changes (SQLite)
npm run db:push:sqlite

# Push schema changes (PostgreSQL)
DB_DIALECT=postgres DATABASE_URL=postgresql://user:pass@host/db npm run db:push:postgres

# Run seeds
npm run db:seed

# Create admin
npm run admin:create -- --dni 12345678 --password "secret" --nombre "John" --apellido "Doe"
```

## Docker Volume

### PostgreSQL data

```bash
# PostgreSQL data is in the salesianos-pgdata volume (managed by Docker)
docker volume inspect salesianos-pgdata
```

## Health Check

The container exposes a health check endpoint:

```
http://localhost:6666/api/health
```

Expected response: `{"status":"ok"}`

The `db` service uses `pg_isready` for PostgreSQL health checks.

## Security Notes

- Admin/superuser creation is **CLI-only** — no HTTP endpoints exposed
- Default admin (`admin@salesianosfest.com` / `admin123`) is **dev-only**
- Production deployments must set custom admin credentials via environment
- JWT secret must be at least 32 characters in production
- Set `COOKIE_SECURE=true` when deploying behind HTTPS
