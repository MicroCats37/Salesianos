# Guía de desarrollo local

Entorno local con **SQLite** (no requiere Docker).

## Requisitos

- Node.js 20+
- npm

## Setup

```bash
cd frontend

# 1. Instalar dependencias
npm install

# 2. Crear el archivo de entorno
#    (copia .env.example a .env y ajusta si hace falta)
cp .env.example .env

# 3. Aplicar el schema a SQLite
npm run db:push:sqlite

# 4. Sembrar catálogos + admin
npm run db:seed

# 5. Levantar el dev server
npm run dev
```

Abre: http://localhost:3000

> En desarrollo el dialecto por defecto es SQLite (`DB_DIALECT=sqlite`),
> así que no necesitas PostgreSQL ni Docker.

## Credenciales de desarrollo

- **DNI**: `00000000`
- **Password**: `admin123`
- **Rol**: `admin_comite`

## Scripts

| Script | Descripción |
|--------|-------------|
| `npm run dev` | Dev server (Next.js) |
| `npm run build` | Build de producción |
| `npm run start` | Start de producción |
| `npm run typecheck` | Verificación de tipos (`tsc --noEmit`) |
| `npm run lint` | Biome check + fix |
| `npm run format` | Biome format |
| `npm run db:push:sqlite` | Aplicar schema a SQLite |
| `npm run db:push:postgres` | Aplicar schema a PostgreSQL |
| `npm run db:generate:sqlite` | Generar migraciones SQLite |
| `npm run db:generate:postgres` | Generar migraciones PostgreSQL |
| `npm run db:studio:sqlite` | Abrir Drizzle Studio (SQLite) |
| `npm run db:studio:postgres` | Abrir Drizzle Studio (PostgreSQL) |
| `npm run db:seed` | Sembrar la base de datos (según `DB_DIALECT`) |
| `npm run admin:create` | Crear/actualizar usuario admin |

## Cambiar entre SQLite y PostgreSQL

El dialecto se controla con `DB_DIALECT`:

```bash
# SQLite (por defecto)
DB_DIALECT=sqlite DATABASE_URL=file:./dev.db npm run db:push:sqlite

# PostgreSQL
DB_DIALECT=postgres DATABASE_URL=postgresql://user:pass@localhost:5432/db npm run db:push:postgres
```

Ninguna capa fuera de `src/infra/db/` conoce el dialecto en uso. Los repositorios
exponen siempre una API **async**.

## Estructura relevante

```
frontend/
├── src/
│   ├── app/            # Rutas + Route Handlers (API)
│   ├── core/           # Dominio puro (sin Next/Drizzle)
│   ├── infra/
│   │   ├── db/         # Adaptadores (index, sqlite, postgres, dialect) + schemas
│   │   └── drizzle/    # Repositorios + seed
│   └── features/       # Lógica de negocio por feature
├── scripts/            # create-admin.ts, deploy-init.sh
├── Dockerfile
└── docker-compose.yml
```

## Documentación relacionada

- [DEPLOYMENT.md](./DEPLOYMENT.md) — Despliegue con Docker + PostgreSQL
- [ENVIRONMENT.md](./ENVIRONMENT.md) — Variables de entorno
