# Deployment Guide

La documentación de despliegue está centralizada en la carpeta `doc/` en la raíz del proyecto:

- [../doc/DEPLOYMENT.md](../doc/DEPLOYMENT.md) — Despliegue con Docker + PostgreSQL, seeds y creación de admin.
- [../doc/DEVELOPMENT.md](../doc/DEVELOPMENT.md) — Entorno local con SQLite.
- [../doc/ENVIRONMENT.md](../doc/ENVIRONMENT.md) — Variables de entorno.

## Resumen

- App (Next.js fullstack): host `4000` → contenedor `7000`
- PostgreSQL: host `5433` → contenedor `5432`

```bash
cd frontend
docker compose up --build -d
```

Luego, desde el host, correr las seeds y crear el admin (ver la guía completa
en `doc/DEPLOYMENT.md`).
