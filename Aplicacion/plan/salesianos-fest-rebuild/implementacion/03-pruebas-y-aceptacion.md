# Implementación 03 — Pruebas y criterios de aceptación

**Acuerdo de trabajo:** los tests se escriben junto con la implementación de cada tarea; su **ejecución** se concentra en la **fase final F4**. El equipo de integración deberá revisar previamente los tests por consistencia sin declararlos pasados antes de ejecutarlos.

## 1. Niveles de prueba previstos

- **Dominio:** invariantes de pools, duplicados de personas, derechos, precios, inventario y competencias.
- **Integración API:** esquemas, autenticación, permisos, errores, paginación, idempotencia.
- **Integración externa simulada:** pago webhook duplicado/tardío, RENIEC no disponible, envío correo fallido.
- **Frontend por pantalla:** rutas, componentes, formularios, estados carga/errores, contratos Zod.
- **E2E negocio:** completar recorridos reales hasta efecto de backend.
- **Seguridad y concurrencia:** dos compras/validaciones simultáneas, escalado de privilegios, exposición de compra ajena.

## 2. Matriz principal de aceptación

| Caso | Resultado esperado | Prioridad |
|---|---|---|
| QA-E01 Ediciones 2026/2027 | Módulos compartidos, datos de registros separados, personas reusadas | Alta |
| QA-U01 Persona sin Usuario | Se puede asignar pase/participar sin crear cuenta | Alta |
| QA-U02 Documento existe/no existe | Local primero; externo solo si falta; sin duplicados | Alta |
| QA-U03 Compra ajena por DNI | No se puede acceder solo con DNI | Alta |
| QA-I01 Inscripción inicial pendiente | 0 cupos habilitados antes de pago | Crítica |
| QA-I02 Confirmación de compra | Aumentan cupos una vez, incluso con callback repetido | Crítica |
| QA-I03 Ampliación | Agrega cupos a misma inscripción, sin duplicar beneficio fijo | Alta |
| QA-I04 Retiro de participante | Cupo libre reutilizable, compra/importe intactos | Alta |
| QA-I05 Carrera de asignación | No se exceden cupos disponibles ni se duplica participación | Crítica |
| QA-P01 Compra de pase sin cuenta | Orden creada sin Usuario y habilitación tras pago | Alta |
| QA-P02 Beneficiarios | Asignación limitada y sin derecho duplicado | Alta |
| QA-P03 Cortesía admin | Derecho creado con motivo y sin transacción ficticia | Alta |
| QA-C01 Cerrar/reabrir modal | No se cancela ni duplica compra; estado coherente | Crítica |
| QA-C02 Doble webhook | Un pago y un efecto por compra | Crítica |
| QA-C03 Fallo posterior a pago | Cobro persiste; incidencia visible y recuperación idempotente | Crítica |
| QA-M01 Pedido y stock | Pedido pendiente no vende más del stock disponible | Crítica |
| QA-M02 Salida administrativa sin pago | Movimiento −5 con actor/motivo, no compra ficticia | Alta |
| QA-M03 Precio oferta cambiado | Compra antigua mantiene snapshot de precio | Alta |
| QA-M04 Entrega | Pedido pagado no equivale a entregado | Alta |
| QA-V01 Ticket usado dos veces | Segundo consumo denegado y auditado | Crítica |
| QA-V02 Escaneo simultáneo | Solo se consume cantidad permitida | Crítica |
| QA-K01 Elegibilidad | Equipo de edición/disciplina incorrecta no entra a competencia | Alta |
| QA-K02 Programación | No acepta solapamiento improcedente | Alta |
| QA-K03 Corregir resultado | Preview de impacto y confirmación sin cascada oculta | Alta |
| QA-A01 Pagos admin | Estado claro, filtro operativo y diagnóstico avanzado | Alta |
| QA-A02 Equipo admin | Pantalla detalle explica plantilla y estado | Alta |
| QA-A03 Acciones admin | En frontend oculta lo prohibido; backend rechaza el comando forzado | Crítica |
| QA-MEDIA01 Imágenes | N imágenes ordenadas, persistentes sin CDN | Media |
| QA-N01 Email no disponible | No revierte compra ni derecho | Alta |

## 3. Contratos visuales que debe aprobar el responsable

**Checkout:** compra/orden se recuperan después de cerrar modal; mensaje de pago confiable; estado en verificación.

**Inscripción:** botón siguiente acción y saldo (`pagados - asignados`) claros; equipo incompleto explica por qué; retiro libera cupo sin devolución.

**Pases:** entrada comprada y entrada de cortesía visibles con origen; comprador invitado gestiona solo su lote mediante vínculo seguro.

**Marketplace:** galería con imágenes locales; precio/oferta; pedido pagado vs entregado; inventario con movimientos auditados.

**Pagos admin:** una tabla entendible; estados técnicos solo en detalle; verificación del cobro separada de derechos otorgados.

**Competencias:** agenda, cuadro y detalle comparten información; ediciones avanzadas muestran impacto antes de confirmación.

**Validaciones:** escaneo preview no consume; confirmar sí; acceso/entrega con auditoría.

## 4. Datos para pruebas

Crear fixtures aisladas de eventos/ediciones, persona con y sin cuenta, admin/grupo Normal, dos paquetes con reglas distintas (fiesta fijo/por cupo), equipos válidos/incompletos, pase individual, producto con stock, patrocinador con dos imágenes, intento de pago exitoso/pending/duplicado, ticket usado/pendiente/revocado.

Los valores de seed de referencia (`04a-seeds-y-datos-iniciales.md`) **no son** precios/categorías obligatorios para el producto final. Usar valores de prueba explícitamente ficticios.

## 5. Criterios de salida de F4

- Suite acordada ejecutada; fallos críticos resueltos o bloqueo declarado.
- Flujos públicos y admin completados de extremo a extremo, incluidas ramas de error.
- Permisos y titularidad validados en backend.
- Contratos API/documentos coinciden con implementación; no mocks de datos reales en producción.
- Correo, tarifas, BOX u otros pendientes no se presentan como implementados si no fueron definidos.
- Los cambios de contrato se reflejan en todos los consumidores y documentación final.

## 6. Formato de evidencia por caso

`ID`; `escenario`; `precondiciones`; `pasos`; `resultado esperado`; `resultado obtenido`; `evidencias`; `versión`; `estado`; `incidencias`. **Nunca inventar ejecución exitosa de pruebas no corridas**.
