# Salesianos FEST — Especificación de reconstrucción

**Versión:** 0.1 · **Fecha:** 2026-11-18 · **Estado:** borrador funcional para revisión

## Propósito

Documentar el **sistema objetivo**, no copiar la implementación existente. El producto comienza con Salesianos FEST y sus ediciones anuales; podrá reutilizar módulos en otros eventos cuando exista una necesidad concreta. La documentación actual del proyecto (15 archivos de auditoría, 2026-11-18) es **referencia de comportamiento existente**, no contrato para preservar sus pantallas o estructura técnica.

Esta carpeta reúne **18 documentos**, con objetivos distintos:

| Orden | Documento | Para qué sirve |
|---|---|---|
| 1 | [00 — Decisiones y alcance](00-decisiones-y-alcance.md) | Acuerdos, supuestos y preguntas abiertas. **Leer primero** |
| 2 | [Funcional: módulos](funcional/01-modulos-y-responsabilidades.md) | Límites de dominio y dependencias |
| 3 | [Funcional: reglas](funcional/02-reglas-de-negocio.md) | Invariantes y condiciones |
| 4 | [Funcional: datos](funcional/03-modelo-de-datos.md) | Entidades, relaciones y cambios conceptuales |
| 5 | [Funcional: flujos](funcional/04-flujos-end-to-end.md) | Recorridos y condiciones de éxito/fallo |
| 6 | [Frontend: mapa de rutas](frontend/01-mapa-rutas-y-navegacion.md) | **Inventario objetivo de páginas, accesos y navegación** |
| 7 | [Frontend: público y usuarios](frontend/02-paginas-publicas-y-usuarios.md) | Fichas de portada, autenticación, cuenta, inscripciones |
| 8 | [Frontend: compras](frontend/03-paginas-comerciales.md) | Fichas de pases, tienda, checkout y recuperación |
| 9 | [Frontend: administración](frontend/04-panel-administrativo.md) | Operaciones del administrador; pagos y equipos claros |
| 10 | [Frontend: encuentros](frontend/05-competencias-y-encuentros.md) | Agenda, cuadro, resultados y correcciones |
| 11 | [Frontend: sistema UX/UI](frontend/06-sistema-ux-ui.md) | Diseño, estados, formularios, microcopy y accesibilidad |
| 12 | [Contratos: API](contratos/01-api-wrappers-presenters.md) | Respuestas y contratos orientados a operaciones |
| 13 | [Contratos: identidad](contratos/02-autenticacion-y-permisos.md) | Personas, cuentas, grupos y titularidad |
| 14 | [Contratos: integraciones](contratos/03-integraciones-y-eventos-internos.md) | Izipay, RENIEC, email y activación de derechos |
| 15 | [Implementación: dependencias](implementacion/01-arquitectura-y-dependencias.md) | Fronteras, orden y acuerdos de integración |
| 16 | [Implementación: tareas y agentes](implementacion/02-plan-de-tareas-y-agentes.md) | Backlog con IDs, dependencias, paralelización |
| 17 | [Implementación: aceptación](implementacion/03-pruebas-y-aceptacion.md) | Casos E2E, pruebas y definición de terminado |

> El archivo 00 más los 16 de subcarpetas y este README suman **18 archivos**.

## Convenciones de decisión

- **[ACORDADO]**: decisión expresamente validada en las conversaciones.
- **[PROPUESTO]**: diseño recomendado, debe ser revisado antes de fijar contrato técnico.
- **[PENDIENTE]**: no inventar una regla; asignar responsable de decisión.
- **[REFERENCIA ACTUAL]**: comportamiento observado por la documentación recibida, **no una obligación de reconstruirlo**.

Las **rutas Next.js**, nombres de **endpoints** y nombres de **tablas nuevos** son **propuestas** salvo indicación expresa. Los contratos públicos se congelarán después de validar flujos y UX. El agente de arquitectura local decide la organización física final de código, sin alterar reglas de negocio aprobadas.

## Cómo deben utilizarse los documentos

1. Agente de producto/UX valida mapa de pantallas y flujos.
2. Agente de arquitectura consensúa entidades y contratos compartidos.
3. Agentes por módulo implementan en paralelo sin inventar dependencias y con áreas de archivos definidas.
4. Un integrador conecta pantallas, servicios, permisos, pagos y derechos.
5. Las pruebas se **redactan durante la implementación** y se **ejecutan en la fase final de validación**, según la planificación acordada.

No se implementa un carrito mixto; no se configura todavía branding ni SMTP. No introducir un motor genérico de plugins o módulos innecesarios.

## Referencias de origen (auditoría actual, no especificación objetivo)

- `README(1).md`, `00-cobertura-y-trazabilidad.md`, `01-arquitectura-y-runtime(1).md`.
- `02-backend-y-api(1).md`, `02a-inventario-de-endpoints(1).md`, `02b-proposito-y-consumidores-de-endpoints.md`.
- `03-frontend(1).md`, `03a-paginas-publicas-y-compra.md`, `03b-paginas-administrativas-y-operativas.md`.
- `04-datos-y-dominio(1).md`, `04a-seeds-y-datos-iniciales.md`, `05-flujos-end-to-end(1).md`, `05a-matriz-pagina-flujo-endpoint-datos.md`, `06-operacion-y-deuda-tecnica(1).md`, `07-guia-para-ui-ux(1).md`.

En particular, la documentación existente contabiliza 20 páginas, 111 rutas HTTP registradas y 27 flujos principales. **No son objetivos numéricos del sistema nuevo**.
