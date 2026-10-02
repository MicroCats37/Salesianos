# Nginx Reverse Proxy -- Port 6666

Dockerized Nginx reverse proxy that routes browser traffic to the Next.js frontend (port 3000)
and Django API backend (port 8000), enabling same-origin API calls and Cloudflare tunnel access.

## Quick Start

```bash
# Start the proxy
docker compose -f proxy/docker-compose.yml up -d

# Verify it's running
curl -s -o /dev/null -w "%{http_code}" http://localhost:6666/

# Stop
docker compose -f proxy/docker-compose.yml down
```

## Architecture

| Path                   | Destination        | Purpose                          |
|------------------------|--------------------|----------------------------------|
| `/`                    | Next.js :3000      | Frontend UI                      |
| `/_next/*`             | Next.js :3000      | Static assets, HMR               |
| `/api/auth/refresh`    | Next.js :3000      | Token refresh (Next-owned)       |
| `/api/auth/logout`     | Next.js :3000      | Logout (Next-owned)              |
| `/backend/*`           | Django :8000 `/api/*` | All other API calls (path mapped) |
| `/proxy-health`        | Nginx (200)        | Container health check           |

## Exposing via Cloudflare Tunnel

```bash
cloudflared tunnel --url http://localhost:6666
```

> **Note:** Direct browser access to `http://localhost:6666` may fail with `ERR_UNSAFE_PORT`
> in modern browsers. Use the Cloudflare HTTPS URL instead -- the tunnel binds to port 443
> and is browser-safe.

## How Same-Origin API Works

When the frontend is accessed through the proxy (via Cloudflare or directly if browser allows),
the browser sees the proxy origin. API calls to `/backend/...` are same-origin requests -- no CORS,
no mixed content, no `.env` changes needed.

The proxy rewrites the path prefix transparently:

```
Browser -> /backend/inscripciones/
       -> Nginx (proxy)
       -> Django:8000/api/inscripciones/
```

## Requirements

- Docker and Docker Compose
- Frontend running on host port 3000
- Django running on host port 8000
- `host.docker.internal` reachable from inside the container (enabled by default on Docker Desktop)
