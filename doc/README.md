# Documentación — Salesianos FEST 2026

Índice de la documentación del proyecto.

| Documento | Descripción |
|-----------|-------------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Despliegue con Docker (PostgreSQL), seeds y creación de admin. |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Entorno local de desarrollo (SQLite). |
| [ENVIRONMENT.md](./ENVIRONMENT.md) | Referencia de variables de entorno. |

## Resumen rápido

- **App**: Next.js fullstack (frontend + API en un solo proceso). No hay backend separado.
- **Base de datos**: SQLite en desarrollo, PostgreSQL en producción. Se cambia con `DB_DIALECT`.
- **Puertos por defecto**:
  - App: host `4000` → contenedor `7000`
  - PostgreSQL: host `5433` → contenedor `5432`

> Nota: se usan `4000`/`5433` porque los navegadores bloquean los puertos `6665-6669`
> (`ERR_UNSAFE_PORT`, rango reservado de IRC).
