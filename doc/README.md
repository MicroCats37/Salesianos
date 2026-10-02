# Documentación — Salesianos FEST 2026

Índice de la documentación del proyecto.

| Documento | Descripción |
|-----------|-------------|
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Despliegue con Docker (PostgreSQL), seeds y creación de admin. |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Entorno local de desarrollo (SQLite). |
| [ENVIRONMENT.md](./ENVIRONMENT.md) | Referencia de variables de entorno. |
| [FRONTEND_MOCKUP_FLOW.md](./FRONTEND_MOCKUP_FLOW.md) | Flujo de referencia del `frontend-mokup` para registro, inscripción, dashboard y Comité. |
| [BACKEND_DOMAIN_PLAN.md](./BACKEND_DOMAIN_PLAN.md) | Plan de dominio backend: módulos, modelos, reglas de negocio y fases de implementación. |
| [BACKEND_CREATEAPP_PLAN.md](./BACKEND_CREATEAPP_PLAN.md) | Plan de creación de Django apps: comandos, estructura de carpetas, archivos y registro de módulos. |
| [USUARIOS_MODULE_EXPLORE.md](./USUARIOS_MODULE_EXPLORE.md) | Exploración del módulo `usuarios` existente: qué conservar, adaptar o remover para el dominio Salesianos. |
| [USUARIOS_REGISTRATION_FLOW_EXPLORE.md](./USUARIOS_REGISTRATION_FLOW_EXPLORE.md) | Exploración del flujo de registro: endpoints, servicios, validaciones y edge cases para crear cuentas de usuario responsable. |
| [MODULAR_APPLY_TASKS.md](./MODULAR_APPLY_TASKS.md) | Plan de tareas modulares para `sdd-apply`: batches autónomos verificables para usuarios, login e inscripciones. |
| [FRONTEND_IMPLEMENTATION_FLOW.md](./FRONTEND_IMPLEMENTATION_FLOW.md) | Análisis de gaps entre frontend mockup y backend Django: endpoints faltantes, payloads y acciones previas al desarrollo frontend. |
| [FRONTEND_ARCHITECTURE_EXPLORE.md](./FRONTEND_ARCHITECTURE_EXPLORE.md) | Arquitectura frontend real + plan de migración UI desde mockup: qué copiar visualmente, qué reconstruir con GenericForm, gaps de backend y plan de SDD apply por batches. |
| [FRONTEND_MODULAR_TASKS.md](./FRONTEND_MODULAR_TASKS.md) | Plan de tareas modulares SDD apply: F1-LANDING, F2-FRONT-SCAFFOLD, F3-AUTH, F4-CATALOGS, F5-INSCRIPCION-WIZARD, F6-DASHBOARD. |

## Resumen rápido

- **App**: Next.js fullstack (frontend + API en un solo proceso). No hay backend separado.
- **Base de datos**: SQLite en desarrollo, PostgreSQL en producción. Se cambia con `DB_DIALECT`.
- **Puertos por defecto**:
  - App: host `4000` → contenedor `7000`
  - PostgreSQL: host `5433` → contenedor `5432`

> Nota: se usan `4000`/`5433` porque los navegadores bloquean los puertos `6665-6669`
> (`ERR_UNSAFE_PORT`, rango reservado de IRC).
