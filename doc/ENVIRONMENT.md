# Variables de entorno

Referencia de variables usadas por la aplicación. El archivo base es
`frontend/.env.example`; cópialo a `frontend/.env` (o `.env.local`).

## Base de datos

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `DB_DIALECT` | `sqlite` \| `postgres` | Selecciona el adaptador. Por defecto `sqlite`. |
| `DATABASE_URL` | `file:./dev.db` (SQLite) / `postgresql://user:pass@host:5432/db` (PostgreSQL) | Cadena de conexión. |
| `DB_NAME` | `salesianos` | Nombre de la base (solo Docker Compose). |
| `DB_USER` | `salesianos` | Usuario de PostgreSQL (solo Docker Compose). |
| `DB_PASSWORD` | `salesianos` | Password de PostgreSQL (solo Docker Compose). |
| `DB_EXTERNAL_PORT` | `5433` | Puerto del host mapeado al `5432` de PostgreSQL. |

### Desarrollo (SQLite)

```env
DB_DIALECT="sqlite"
DATABASE_URL="file:./dev.db"
```

### Producción / Docker (PostgreSQL)

Dentro de Docker Compose, el host es el nombre del servicio (`db`):

```env
DB_DIALECT="postgres"
DATABASE_URL="postgresql://salesianos:salesianos@db:5432/salesianos"
```

Desde el **host** (para seeds/admin) se usa `localhost` y el puerto externo:

```
postgresql://salesianos:salesianos@localhost:5433/salesianos
```

## Aplicación

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `FRONTEND_PORT` | `4000` | Puerto del host para la app. |
| `PORT` | `7000` | Puerto interno del contenedor. |
| `NODE_ENV` | `development` \| `production` | Entorno de ejecución. |
| `NEXT_PUBLIC_APP_URL` | `http://localhost:4000` | URL pública de la app. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:4000` | URL pública de la API (mismo proceso). |

### Frontend ↔ Backend: dos URLs distintas

El navegador y el servidor de Next.js **no** llaman al backend por la misma URL:

| Variable | Ejemplo | Quién la usa | Descripción |
|----------|---------|--------------|-------------|
| `NEXT_PUBLIC_API_URL` | `/backend` | El **navegador** | URL relativa que reescribe el proxy nginx hacia `/api` de Django. Se compila en el bundle del cliente. |
| `BACKEND_INTERNAL_URL` | `http://backend:8000/api` | El **servidor** de Next.js | URL interna real del backend (Server Components y Route Handlers). **No** es `NEXT_PUBLIC_*`: se lee en runtime y nunca llega al navegador. |

Reglas:

- `BACKEND_INTERNAL_URL` **debe** ser absoluta. Un valor relativo (`/backend`) no lo
  resuelve un `fetch` de Node y todas las llamadas del servidor a la API fallan.
- En Docker Compose el valor por defecto es `http://backend:8000/api` (el nombre
  del servicio en la red de Docker). Fuera de Docker, `http://localhost:8000/api`.
- Es una variable de **runtime**: cambiarla no exige recompilar la imagen (a
  diferencia de cualquier `NEXT_PUBLIC_*`, que se compila en el build).

## Autenticación

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `JWT_SECRET` | (obligatorio) | Clave de firma JWT. **Mínimo 32 caracteres** (`jose` falla si es menor). |
| `JWT_ACCESS_TOKEN_TTL_SECONDS` | `604800` | TTL del access token (7 días). |
| `JWT_REFRESH_TOKEN_TTL_SECONDS` | `2592000` | TTL del refresh token (30 días). |
| `COOKIE_SECURE` | `false` | `true` requiere HTTPS (producción). |

## Creación de admin (CLI)

Usadas por `npm run admin:create` cuando no se pasan por argumentos:

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `ADMIN_DNI` | `00000000` | DNI del admin (requerido). |
| `ADMIN_PASSWORD` | `admin123` | Password (requerido, mínimo 8 caracteres). |
| `ADMIN_EMAIL` | `admin@salesianosfest.com` | Email (opcional). |
| `ADMIN_NOMBRE` | `Comite` | Nombres (opcional). |
| `ADMIN_APELLIDO` | `Salesianos` | Apellidos (opcional). |
| `ADMIN_ROLE` | `admin_comite` \| `admin_finanzas` | Rol (opcional, por defecto `admin_comite`). |

## Notas

- **Nunca** subas `.env` ni `.env.local` al repositorio (ya están en `.gitignore`).
- Los puertos `4000`/`5433` se eligieron porque los navegadores bloquean `6665-6669`
  (`ERR_UNSAFE_PORT`).
- En producción, define `JWT_SECRET` propio y `COOKIE_SECURE=true`.
