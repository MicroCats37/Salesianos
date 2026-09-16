# Guía de despliegue — Docker + PostgreSQL

Esta guía cubre el despliegue del proyecto con Docker Compose, la inicialización
de la base de datos (schema + seeds) y la creación del usuario administrador.

## Arquitectura

La aplicación es un **Next.js fullstack**: la interfaz y la API (Route Handlers)
corren en el mismo proceso. **No existe un backend separado.**

```
Navegador ──► Next.js (app) ──► repositorios (async) ──► db/index.ts
                                                          ├── db/sqlite.ts    (dev)
                                                          └── db/postgres.ts  (prod)
```

La base de datos se selecciona con la variable `DB_DIALECT`:

| Entorno | Dialecto | `DB_DIALECT` | Base de datos |
|---------|----------|--------------|---------------|
| Desarrollo | SQLite | `sqlite` | `file:./dev.db` |
| Producción (Docker) | PostgreSQL | `postgres` | `postgresql://...` |

## Requisitos

- Docker Desktop (con el engine iniciado).
- Node.js 20+ y `npm` en el host (para correr seeds/admin manualmente).
- Puertos libres: `4000` (app) y `5433` (PostgreSQL).

## 1. Levantar el stack

Desde la carpeta `frontend`:

```bash
cd frontend
docker compose up --build -d
```

Esto levanta dos servicios:

| Servicio | Imagen | Host | Contenedor |
|----------|--------|------|------------|
| `app` | Next.js (build local) | `4000` | `7000` |
| `db` | `postgres:16-alpine` | `5433` | `5432` |

Verifica que ambos estén **healthy**:

```bash
docker compose ps
```

Salida esperada:

```
salesianos-app   Up (healthy)   0.0.0.0:4000->7000/tcp
salesianos-db    Up (healthy)   0.0.0.0:5433->5432/tcp
```

## 2. Inicializar la base de datos (manual)

> Las seeds y la creación de admin **no** se ejecutan automáticamente.
> Se corren manualmente desde el **host** contra PostgreSQL en `localhost:5433`.
> La imagen final es "lean" (standalone) y no incluye `tsx`/`drizzle-kit`.

### 2.1 Aplicar el schema

**PowerShell (Windows):**

```powershell
$env:DB_DIALECT="postgres"
$env:DATABASE_URL="postgresql://salesianos:salesianos@localhost:5433/salesianos"
npm run db:push:postgres
```

**Bash (Linux/macOS):**

```bash
DB_DIALECT=postgres \
DATABASE_URL="postgresql://salesianos:salesianos@localhost:5433/salesianos" \
npm run db:push:postgres
```

### 2.2 Correr las seeds

```powershell
npm run db:seed
```

Las seeds crean:

- **Bases**: `BASES-SF26-2026-09-06`
- **Disciplinas**: `fulbito_var`, `fulbito_dam`, `voley_mix`, `basket_var`
- **Categorías**: por disciplina y rango de años
- **Promociones**: desde **1970 hasta el año actual** (idempotente)
- **Admin de prueba**: DNI `00000000` (solo desarrollo)

> Las seeds son idempotentes: se pueden correr varias veces sin duplicar datos.

### 2.3 Crear el usuario administrador

```powershell
npm run admin:create -- --dni 00000000 --password "admin123" --nombre "Comite" --apellido "Salesianos"
```

Opciones disponibles:

| Opción | Requerido | Descripción |
|--------|-----------|-------------|
| `--dni` | Sí | Número de documento |
| `--password` | Sí | Contraseña (mínimo 8 caracteres) |
| `--email` | No | Email (por defecto `admin@local`) |
| `--nombre` | No | Nombres |
| `--apellido` | No | Apellidos |
| `--role` | No | `admin_comite` \| `admin_finanzas` (por defecto `admin_comite`) |

También se puede usar variables de entorno:

```powershell
$env:ADMIN_DNI="00000000"
$env:ADMIN_PASSWORD="admin123"
$env:ADMIN_EMAIL="admin@salesianosfest.com"
$env:ADMIN_ROLE="admin_comite"
npm run admin:create
```

> **Importante:**
> - La creación de admin es **solo por CLI** (no hay endpoint HTTP público).
> - La contraseña se hashea con **bcrypt**.
> - Es idempotente: si el usuario existe, se actualiza.

## 3. Verificar

```bash
curl http://localhost:4000/api/health
```

Respuesta esperada: `{"status":"ok"}`

Login de prueba (REST):

```bash
curl -X POST http://localhost:4000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"identifier\":\"00000000\",\"password\":\"admin123\"}"
```

Respuesta esperada: `200` con `"success":true` y rol `admin_comite`.

Abre la aplicación en:

```
http://localhost:4000
```

## Comandos útiles de Docker

```bash
# Ver estado
docker compose ps

# Ver logs del app
docker compose logs app --tail 60

# Reiniciar el stack
docker compose restart

# Reconstruir y recrear
docker compose up --build -d --force-recreate

# Detener
docker compose down

# Detener y borrar datos de PostgreSQL (CUIDADO: borra la DB)
docker compose down -v
```

## Exponer en internet (opcional)

Para una prueba rápida con un túnel temporal:

```bash
cloudflared tunnel --url http://127.0.0.1:4000
```

Cloudflare entrega una URL `https://<aleatorio>.trycloudflare.com`.
Los quick tunnels no garantizan uptime y la URL cambia al reiniciar.
Para producción, usa un **tunnel nombrado** con tu cuenta de Cloudflare.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `ERR_UNSAFE_PORT` en el navegador | Puerto bloqueado (6665-6669) | Usa `4000`/`5433` |
| `no configuration file provided` | `docker compose` ejecutado en la raíz | Ejecuta desde `frontend/` |
| `app` marcado `unhealthy` | Healthcheck con `localhost` (IPv6) | Usa `127.0.0.1` en el healthcheck |
| `Cannot read properties of undefined (reading 'personas')` | Script usando `db.schema.*` | Importa `schema` desde `@/infra/drizzle/client` |
| `JWT_SECRET` error | Falta o es menor a 32 caracteres | Define un `JWT_SECRET` válido |
| Seeds/admin "cuelgan" | El pool de PostgreSQL no cierra el proceso | Ya se resuelve con `process.exit(0)` |

## Seguridad

- La creación de admin es **solo CLI**; no hay endpoint HTTP público.
- El admin por defecto (`00000000` / `admin123`) es **solo para desarrollo**.
- En producción define credenciales propias y un `JWT_SECRET` de al menos 32 caracteres.
- Con HTTPS, define `COOKIE_SECURE=true`.
