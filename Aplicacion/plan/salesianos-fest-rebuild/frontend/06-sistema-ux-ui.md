# Frontend 06 — Sistema UX/UI y criterios de diseño

**Objetivo:** la reconstrucción debe sentirse como una aplicación coherente, no como diferentes proyectos unidos por navegación. El diseño visual definitivo puede definirse después sin afectar flujos y contratos.

## 1. Arquitectura de interacción

- Estructura coherente: página pública → tarea → resultado → seguimiento.
- Navegación por intención, no por nombres técnicos de base de datos.
- Un único patrón visual de tablas con paginación, filtros, estados vacíos y detalles; variaciones para cuadros deportivos donde corresponda.
- Formularios con validación por campo; errores comprensibles y recuperables.
- Modales/drawers solo para acciones cortas; tareas largas en página con URL recuperable.
- Diseño responsive mobile-first para compradores, responsables y operadores de QR.

## 2. Lenguaje de interfaz

| Interno | Mostrar preferentemente |
|---|---|
| `settlement_status`, liquidación | “Beneficio habilitado”, “Cupos disponibles”, “Entrada activa” |
| `PENDIENTE` sin contexto | “Pago pendiente” o “Pendiente de asignación” según operación |
| `AL_LIMITE` | “Equipo completo: alcanzó máximo de jugadores” |
| `INCOMPLETO` | “Falta 1 jugador para competir” (motivo del backend) |
| `PASE_BENEFICIARIO_DUPLICADO` | “Esta persona ya tiene una entrada activa para esta edición” |
| `RESOURCE_CHANGED` | “Los datos cambiaron. Actualiza y revisa antes de guardar.” |

No inventar un mensaje en cliente para contradecir una regla; backend proporciona código y descripción de negocio.

## 3. Estados de todas las pantallas

1. **Carga inicial:** skeleton con estructura adecuada.
2. **Vacío inicial:** explica qué no existe y ofrece una acción relevante.
3. **Sin resultados de filtros:** conserva filtros y permite limpiarlos.
4. **Error recuperable:** explicar problema y mostrar “Reintentar”; distinguir 401, 403, 404, 409, 422, 5xx.
5. **Proceso en curso:** evitar doble submit, mostrar progreso verídico sin inventar tiempos.
6. **Éxito:** qué cambió, qué se puede hacer después.
7. **Proceso parcial/indeterminado:** por ejemplo, pago verificado pero aún no activado; ofrecer seguimiento sin duplicar operación.
8. **Operación irreversible:** confirmación y motivo si corresponde.

## 4. Componentes reutilizables sugeridos

`PageHeader`, `PageSection`, `StatusSummary`, `OperationalDataTable`, `FilterBar`, `DetailDrawer`, `FormField`, `ConfirmActionDialog`, `PaymentStatus`, `QrScanner`, `TicketValidationPreview`, `ProductImageGallery`, `InventoryMovementDialog`, `TeamRoster`, `MatchDetailPanel`.

Estos nombres son ilustrativos. El agente de frontend decidirá reutilización real y no construirá una librería de componentes innecesaria.

## 5. Reglas de presentación/datos

- Un cliente HTTP coherente, claves de caché por recurso, invalidaciones específicas tras mutación.
- Los schemas Zod validan respuestas API reales, no formas inventadas.
- El frontend muestra veredictos de backend: precio, saldo, permisos, siguiente acción, resultado de match.
- `src/app/**` sirve principalmente para rutas/layout; lógica y UI de dominio viven en features, si el stack elegido lo permite.
- No duplicar datos de catálogo en fallback estático. Si la API falla, comunicar fallo.
- Solo el backend autoriza. Ocultar un botón es ayuda de UX, no seguridad.

## 6. Accesibilidad

- Labels y mensajes de error asociados a campos; foco devuelto después de modal.
- Tablas y bracket navegables con teclado; tarjetas clicables semánticas.
- Estados de color acompañados de texto e icono; no usar solo rojo/verde.
- Lectura QR ofrece ingreso manual alternativo y control de permisos de cámara.
- Fotos de productos/patrocinadores con `alt` descriptivo; movimiento del carrusel controlable.

## 7. Entregables UX por página

Ficha de ruta; wireframe de escritorio/móvil; flujo de estados; contrato de datos; acciones/navegación; microcopy; pruebas de aceptación. Empezar por pagos, equipos, inscripción y competencias. Una vez aprobado, no rehacer contratos sin registro de cambio.

## 8. Métricas de calidad recomendadas (no metas cerradas)

- Comprador siempre puede identificar estado de su compra después de cerrar checkout.
- Responsable distingue inmediatamente cupos comprados vs asignados.
- Administrador comprende qué impide que equipo compita sin abrir consola o SQL.
- Operador puede validar entrada/entrega con confirmación y evidencia de uso previo.
- Cada error relevante ofrece siguiente acción y conserva la operación cuando es posible.
