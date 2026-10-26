# Informe SDD Explore: Rediseño Destructivo de Salesianos FEST

**Estado:** exploración consolidada; no autoriza implementación por sí sola.  
**Fecha:** 2026-10-17  
**Método:** lectura directa de código y contratos, sin CodeGraph.  
**Fuente de negocio:** `ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md`.  
**Decisión de corte:** reemplazo destructivo. No se conserva compatibilidad, datos, migraciones ni APIs del dominio heredado `inscripciones`.

---

## 1. Resultado ejecutivo

El módulo actual `backend/modules/inscripciones` implementa una inscripción grupal con un pago único por paquete. No representa el modelo objetivo: compra de cupos, ampliaciones, asignaciones pagadas, acreditación por evento y beneficios con múltiples orígenes.

La solución no es evolucionarlo gradualmente ni copiar sus relaciones: se crean los módulos `eventos` y `salesianos_fest`, se desacopla `pagos` mediante `OrdenPago` y se reemplaza el frontend que consume `/inscripciones/*` y `/pagos/izipay/*/{inscripcion_id}`.

La reconstrucción se realiza en bloques verificables. Cada bloque exige un **SDD Explore sin CodeGraph** seguido de un **SDD Apply** que relee `contract/` antes de editar código.

---

## 2. Límites del rediseño

### Dentro del alcance

- Módulo genérico mínimo `eventos`.
- Módulo de negocio `salesianos_fest` con catálogo, inscripción deportiva, compra, cupos, acreditación, consentimiento y control de acceso.
- Refactor de `pagos` para que sea agnóstico al dominio y use `OrdenPago`.
- Reemplazo de endpoints, schemas, presenters, DI, seeds, admin, tests y frontend asociados a `inscripciones`.
- Mensajes públicos seguros: códigos estables, sin UUID, IDs internos, trazas ni detalles SQL.
- Reinicio destructivo de entorno de desarrollo cuando el apply de corte lo autorice.

### Fuera del alcance actual

- Migrar registros del dominio anterior.
- Adaptadores, dual-write, compatibilidad de endpoints o pantallas heredadas.
- CMS, motor genérico de eventos o plugins.
- Tienda de productos heterogéneos mediante `CompraDetalle`.
- Tabla de reglas de fusión de promociones sin una regla aprobada.
- Trazabilidad de canje de box/cerveza hasta que se confirme la operación real.

---

## 3. Inventario actual y destino

| Área actual | Evidencia | Destino | Motivo |
|---|---|---|---|
| `backend/modules/inscripciones/` | Modelos, controladores, presenters, DI, seeds, admin y tests propios | Eliminar y reemplazar | Su modelo no representa `Compra`, `AsignacionCupo` ni `AcreditacionEvento`. |
| `inscripciones.Evento` | Evento pertenece al módulo deportivo actual | Reemplazar por `eventos.Evento` | `Evento` debe ser genérico y no importar reglas deportivas. |
| `Categoria -> Disciplina` | Categoría actual depende de disciplina | Eliminar la relación | La categoría es general por rango de promoción, no por deporte. |
| `Paquete` heredado | Precios directos y configuración insuficiente | Reemplazar | Faltan tipo, etapas de precio, mínimo comercial y beneficios. |
| `Inscripcion.estado` | Incluye estados de pago | Reemplazar | Estado deportivo y estado económico son independientes. |
| `EquipoInscrito` y participantes actuales | Modelan roster directo | Reemplazar por `Equipo`, `InscripcionPersona`, `Participacion` | Una persona puede jugar varias disciplinas con un único cupo comercial por inscripción. |
| `Persona.acepto_*` | Flags globales y reutilizables | Retirar en la fase de consentimientos | El consentimiento es por persona e inscripción, con evidencia y versión. |
| `pagos.IzipayTransaccion -> Inscripcion` | Acoplamiento directo al dominio heredado | Reemplazar por `TransaccionPago -> OrdenPago` | Pagos no debe depender de Salesianos FEST. |
| `/inscripciones/*` | Frontend y dashboard los consumen | Eliminar y reemplazar | API nueva refleja compras, cupos y acreditaciones. |
| `/pagos/izipay/preparar/{inscripcion_id}` | `frontend/src/features/pagos/services/pago.service.ts` | Reemplazar | La unidad cobrable es `OrdenPago` asociada a `Compra`, no inscripción. |
| Wizard y detalle frontend | `features/inscripciones` y rutas `/inscripcion`, dashboard | Reemplazar | Formulario y detalle actual mezclan roster, consentimiento y pago único. |

---

## 4. Arquitectura objetivo

```text
usuarios
  Persona + Usuario/autenticación
          │
eventos   │  Evento mínimo, aislado del deporte
          │
salesianos_fest
  Catálogos -> Inscripción deportiva -> Compra/cupos -> Acreditación/acceso
          │
pagos
  OrdenPago -> TransaccionPago -> proveedor Izipay
```

### Dependencias permitidas

- `salesianos_fest` puede referenciar `eventos.Evento`, `usuarios.Persona` y `pagos.OrdenPago`.
- `pagos` no importa modelos, servicios ni schemas de `salesianos_fest`.
- `eventos` no importa modelos deportivos.
- La comunicación entre módulos pasa por servicios, selectors, results y contratos explícitos, no por imports inversos.

### Capas obligatorias

| Capa | Responsabilidad |
|---|---|
| Controller | Parsear HTTP, delegar y devolver éxito con mensaje fijo contextual. |
| Orchestrator | Fachada async: un método por endpoint, sin lógica de negocio. |
| Flujo | Caso de uso async, `transaction.atomic()`, bloqueos e idempotencia. |
| Core | Operaciones ORM sync reutilizables. |
| Selector | Consultas complejas reutilizables. |
| Presenter | Transformar results/modelos a schema HTTP; no consulta DB ni crea mensajes. |
| `core/exceptions.py` | Traducir códigos estables a mensajes públicos seguros y registrar detalle técnico. |

---

## 5. Modelo objetivo y reglas de integridad

### 5.1 `eventos`

| Modelo | Campos esenciales | Reglas |
|---|---|---|
| `Evento` | `nombre`, `fecha_inicio`, `fecha_fin`, `esta_activo` | Módulo mínimo y genérico; no contiene disciplina, paquetes ni lógica deportiva. |

### 5.2 Catálogos de `salesianos_fest`

| Modelo | Responsabilidad | Integridad requerida |
|---|---|---|
| `Disciplina` | Catálogo deportivo | `sigla` única; modalidad M/F/X; mínimos/máximos deportivos por equipo. |
| `Promocion` | Promoción Salesianos | `anio` único; sin `colegio`. |
| `Categoria` | Rango general de promociones | Sin FK a disciplina; rango válido y sin solapes activos en el ámbito aprobado. |
| `Paquete` | Las ocho ofertas comerciales | FK a evento; tipo PACK/DISCIPLINA; modo FIJO/ELEGIBLE; mínimo inicial; paquete inmutable después de selección confirmada. |
| `PaqueteDisciplina` | Disciplinas fijas o elegibles | Único `(paquete, disciplina)`. |
| `PaquetePrecio` | Precio vigente por etapa | PREVENTA/REGULAR; impedir períodos solapados; la compra congela snapshot. |
| `PaqueteBeneficio` | Configuración, no saldo | Fiesta individual por cupo; box/cerveza grupal y fijo inicial. |

### 5.3 Inscripción deportiva

| Modelo | Responsabilidad | Integridad requerida |
|---|---|---|
| `Inscripcion` | Responsable, paquete, promoción, fusión y estado deportivo | Todo pertenece al mismo evento; sin estado PAGADA; una sola fusión opcional. |
| `Equipo` | Equipo por disciplina de inscripción | Disciplina permitida por paquete; categoría calculada desde promoción principal; validar cantidad definida. |
| `InscripcionPersona` | Persona registrada dentro de una inscripción | Único `(inscripcion, persona)`; estado ACTIVO/RETIRADO; no implica cupo pagado. |
| `Participacion` | Persona en equipo/disciplina | Una persona puede estar en varios equipos de la misma inscripción; constraint parcial activo `(evento, disciplina, persona)` para R11. |

### 5.4 Comercio, pago y derechos

| Modelo | Responsabilidad | Integridad requerida |
|---|---|---|
| `Compra` | Cupos homogéneos de una inscripción | INICIAL/AMPLIACION; una inicial válida; cantidad, precio unitario y total congelados; estado económico propio. |
| `OrdenPago` | Unidad cobrable genérica en `pagos` | Una compra la referencia; reintentos crean transacciones, no compras ni derechos extra. |
| `TransaccionPago` | Intentos del proveedor | FK a orden; idempotencia por proveedor/transaction_id; respuesta saneada. |
| `AsignacionCupo` | Vínculo cupo pagado-persona | Solo se crea tras pago; origen compra e inscripción coinciden; una activa por inscripción/persona; nunca hay filas de cupos vacíos. |
| `AcreditacionEvento` | Permisos efectivos persona-evento | Único `(evento, persona)`; múltiples orígenes; override BLOQUEADA/AUTORIZADA prevalece sobre cálculo automático. |
| `ControlAcceso` | Resultado de lectura QR | Ingreso de uso único y operación concurrente atómica. |
| `AceptacionInscripcion` | Consentimiento trazable | Por `InscripcionPersona`, versión, fecha, actor y medio según decisión legal. |

---

## 6. Flujos que reemplazan al modelo actual

| Flujo | Cambio real | Invariantes principales |
|---|---|---|
| F1 Crear inscripción + compra inicial | El wizard crea inscripción deportiva, equipos, personas y compra pendiente | Personas registradas <= cupos contratados; no hay derechos ni asignaciones antes de pagar. |
| F2 Confirmar Izipay | Callback seguro marca orden/compra una vez y asigna cupos | Importe, moneda, proveedor, idempotencia y lock de registros. |
| F3 Añadir persona con saldo | Una persona nueva consume saldo pagado de esa inscripción | No transferir cupos; participación adicional misma inscripción no consume otro cupo. |
| F4 Ampliación | Nueva compra sin repetir mínimo inicial | Precio vigente congelado; beneficios fijos iniciales no se duplican. |
| F5 Retiro/reemplazo | Retira participación y libera cupo si no queda otra participación | Recalcular acreditación con todos los orígenes pagados. |
| F6 Override de fiesta | Admin autoriza/bloquea con motivo y auditoría | Un pago posterior no revierte un bloqueo explícito. |
| F7 Escaneo QR | Evalúa acreditación efectiva y registra intento | Solo un ingreso exitoso ante concurrencia. |

---

## 7. Brecha frontend

### Estado actual comprobado

- `features/inscripciones/schemas/inscripcion.schema.ts` captura tres declaraciones globales y las envía con la inscripción.
- `features/inscripciones/services/inscripcion.service.ts` depende de IDs de inscripción, equipo y participante, y muestra flags de consentimiento del responsable/persona.
- `features/pagos/services/pago.service.ts` prepara Izipay a partir de `inscripcionId`.
- Dashboard, sidebar, landing y páginas `/inscripcion`/`/dashboard/inscripcion/[id]` están enlazados al flujo heredado.

### Reemplazo requerido

| Área | Cambio |
|---|---|
| Catálogo público | Consumir ofertas/precios/beneficios del nuevo módulo. |
| Creación | Capturar paquete, cupos iniciales, promoción, disciplinas y roster parcial; no activar derechos antes del pago. |
| Compra y pago | Preparar una `OrdenPago` de una `Compra`; no enviar ni derivar montos en cliente. |
| Detalle | Separar estado deportivo, compras, cupos contratados/pagados/disponibles, participantes, acreditación y acciones permitidas. |
| Participantes | Agregar, mover, retirar o reemplazar conforme al saldo y a R11. |
| Consentimientos | Recabar evidencia por persona/inscripción, no como flags globales del formulario. |
| Administración | Acciones auditables de revisión, autorización/bloqueo y control de acceso. |
| Mensajes | Mostrar `error.message` público; nunca fabricar texto desde UUIDs o respuestas técnicas. |

---

## 8. Contrato de respuestas públicas

Los contratos ya revisados establecen este objetivo:

- Controller: mensaje fijo de éxito, por ejemplo `"La compra fue registrada correctamente."`.
- Excepción de dominio: subclase tipada con código estable, por ejemplo `COMPRA_NOT_FOUND`.
- Handler global: único dueño del mensaje público y status HTTP.
- Logs: detalle técnico, excepción original y correlación solo del lado del servidor.
- Respuesta pública: nunca UUID, ID interno, `str(exc)`, SQL, traceback, path, secreto ni payload de proveedor.

Ejemplo de jerarquía:

```text
HttpError -> NotFoundError -> CompraNotFoundError
```

---

## 9. Pendientes que no se deben inventar

| Pendiente | Bloque que bloquea |
|---|---|
| Versionado/ámbito de `Categoria` | Catálogos si se requiere configurar por edición. |
| Política de fusión de promoción | Inscripción deportiva. |
| Entrega de box/cerveza | Beneficios colectivos/acreditación. |
| Registro de jugador antes de pagar ampliación | Compra y cupos. |
| Momento de congelar precio y vencimiento | Compra/orden de pago. |
| Pago manual, reembolso y pagos duplicados | Pago y conciliación. |
| Quién acepta consentimientos y versionado legal | Consentimientos. |
| Plazo de edición y excepciones admin | Flujos de modificación. |
| Cardinalidad compra-orden en reemisiones | Pago. |
| Acceso individual a box | Acreditación. |
| Estados definitivos de acreditación | Acreditación/QR. |
| Máximos deportivos validados | Catálogo y validación final. |

---

## 10. Verificación obligatoria

- Pruebas de aceptación T01 a T23 de la especificación.
- Tests de contrato de mensajes públicos: sin UUID, IDs, SQL ni excepciones crudas.
- Tests de integración por flujo.
- Tests E2E HTTP async con el cliente establecido por `contract/`.
- PostgreSQL real para T14 (último cupo concurrente) y T15 (doble escaneo QR concurrente).
- Seeds de las ocho ofertas solo cuando sus disciplinas elegibles estén confirmadas.
- Ningún bloque se declara completo sin ejecutar sus pruebas y revisar su diff.

---

## 11. Siguiente artefacto

El orden ejecutable está en `PLAN_MODULAR_REDISENO_SALESIANOS_FEST.md`. Cada fase debe iniciar desde su propio SDD Explore, incluso cuando parezca una continuación obvia.
