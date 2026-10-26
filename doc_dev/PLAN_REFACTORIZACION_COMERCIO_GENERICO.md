# Plan de Refactorización: Comercio Genérico

> **Proyecto:** Salesianos
> **Fecha:** 19 de octubre de 2026
> **Autor:** SDD Explore — `generic-commerce-refactor`
> **Estado:** Plan destructivo — todos los datos locales son datos de prueba y pueden eliminarse/reiniciarse

---

## 1. Resumen Ejecutivo

El módulo `pagos` ya es agnóstico del dominio. El problema es `Compra` en `salesianos_fest` que combina lógica comercial genérica con una FK directa a `Inscripcion`, imposibilitando la reutilización por una tienda futura.

**Decisión central del plan:** Crear un módulo `commerce` con un modelo `Compra` puramente genérico — sin conocimiento de entidades de negocio — y composición explícita mediante FK reales desde los módulos de dominio. `salesianos_fest` composiciona sobre `commerce.Compra` mediante `CompraInscripcion`. `pagos.OrdenPago` apuntará a `commerce.Compra` y ganará `descripcion` + `referencia_externa` como snapshots de auditoría.

**Se rechaza:** `entity_type`, `entity_id`, `GenericForeignKey` y todo patrón que simule polimorfismo sin FK real.

---

## 2. ER Actual vs. Objetivo

### Estado Actual

```
salesianos_fest.Compra ───────────── OneToOne ──► pagos.OrdenPago
       │
       │ FK (PROTECT)
       ▼
  salesianos_fest.Inscripcion
```

### Estado Objetivo

```
commerce.Compra ◄────────────────── OneToOne ──► pagos.OrdenPago
   │ (genérico, sin FK a negocio)                  │
   │                                                │ 1:N
   │                   ┌───────────────────────────┘
   │                   ▼
   │          pagos.TransaccionPago
   │
   │ OneToOne (PROTECT)
   ▼
salesianos_fest.CompraInscripcion
   │ FK → Inscripcion (PROTECT)
   │ tipo: INICIAL | AMPLIACION
   │ cantidad, precio_unitario, total (snapshots)
   │ UniqueConstraint: (inscripcion, tipo=INICIAL) — una sola compra inicial

(Futuro) store.CompraTiendaItem
   │ FK → commerce.Compra (PROTECT)
   │ FK → Producto (PROTECT)
   │ cantidad, precio_unitario (snapshots)
```

---

## 3. Mapeo Current → Target por Modelo

### 3.1 `commerce.Compra` (nuevo)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado de `BaseModel` |
| `responsable` | FK → `usuarios.Persona` (PROTECT, nullable) | Persona que realiza la compra. Nullable para compras futuras sin responsable autenticado |
| `descripcion` | CharField(255) | Descripción genérica de la compra para display/auditoría |
| `referencia_externa` | CharField(100, nullable) | Referencia libre del negocio (ej. "Inscripción FEST", "Pedido Tienda") |
| `total` | Decimal(10,2) | Total snapshot |
| `estado` | CharField(15) | `PENDIENTE`, `PAGADA`, `CANCELADA` |
| `orden_pago` | OneToOne → `pagos.OrdenPago` (PROTECT) | La orden de pago asociada |

**Restricciones:**
- Sin `entity_type`, `entity_id` o cualquier referencia a entidades de negocio.
- Sin `GenericForeignKey`.

### 3.2 `salesianos_fest.CompraInscripcion` (nuevo)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado de `BaseModel` |
| `compra` | OneToOne → `commerce.Compra` (PROTECT) | Compra genérica asociada |
| `inscripcion` | FK → `Inscripcion` (PROTECT) | Inscripción FEST asociada |
| `tipo` | CharField(15) | `INICIAL` o `AMPLIACION` |
| `cantidad` | PositiveInteger | Cupos comprados |
| `precio_unitario` | Decimal(10,2) | Precio snapshot en momento de la compra |
| `total` | Decimal(10,2) | Total snapshot = cantidad × precio_unitario |

**Restricciones:**
- UniqueConstraint parcial: `(inscripcion, tipo=INICIAL)` — solo una compra inicial por inscripción.
- `cantidad` para AMPLIACION no está sujeta al mínimo comercial (el mínimo aplica solo a INICIAL).

### 3.3 `pagos.OrdenPago` (modificado)

| Campo | Tipo | Notas |
|-------|------|-------|
| `numero` | CharField(20) | Sin cambios |
| `monto_total` | Decimal(10,2) | Sin cambios |
| `moneda` | CharField(3) | Sin cambios |
| `estado` | CharField(15) | Sin cambios |
| `pagada_en` | DateTimeField | Sin cambios |
| `expires_at` | DateTimeField | Sin cambios |
| `descripcion` | CharField(255) | **NUEVO** — descripción de la orden para display/auditoría |
| `referencia_externa` | CharField(100, nullable) | **NUEVO** — referencia del negocio (ej. "Compra FEST #123") |
| `compra` | OneToOne → `commerce.Compra` (PROTECT) | **MODIFICADO** — ya no apunta a `salesianos_fest.Compra` |

### 3.4 `salesianos_fest.Compra` (eliminar)

El modelo `Compra` actual se elimina. Sus datos migran a `commerce.Compra` + `CompraInscripcion`.

### 3.5 Futura tienda (`store`)

```
store.CompraTiendaItem (futuro)
   compra: FK → commerce.Compra (PROTECT)
   producto: FK → Producto (PROTECT)
   cantidad: PositiveInteger
   precio_unitario: Decimal(10,2)
   total: Decimal(10,2)
```

Este modelo no existe aún; se documenta para mostrar que la composición explícita con FK reales es el patrón también para la tienda futura.

---

## 4. Dirección de Dependencias y Propiedad de Módulo

```
commerce/
  domain/models/compra.py     ← Compra genérica, sin imports de módulos de negocio
  domain/constants.py          ← EstadoCompraChoices
  domain/services/core/       ← Lógica de compra genérica
  presentation/              ← No exponer endpoints genéricos de compra sin contexto

salesianos_fest/
  domain/models/compra_inscripcion.py  ← CompraInscripcion: FK real a commerce.Compra
  domain/services/flujos/     ← CrearCompraFEST Flujo
  presentation/controllers/   ← Endpoints FEST-specific

pagos/
  domain/models/pago.py       ← OrdenPago y TransaccionPago (ya agnósticos)
  domain/models/__init__.py   ← Actualizar exports
```

**Regla respetada:** `commerce` no importa ningún modelo de negocio. `pagos` no importa ningún módulo de negocio. La composición va en dirección negocio → commerce → pagos (el módulo de dominio crea `commerce.Compra`, y `pagos.OrdenPago` la referencia).

---

## 5. Decisiones Confirmadas

| # | Decisión | Justificación |
|---|----------|---------------|
| D1 | `commerce.Compra` → `OrdenPago`: OneToOne | Cada obligación de pago corresponde a una compra. Reintentos generan nuevas `TransaccionPago`, no nuevas órdenes |
| D2 | `OrdenPago` → `TransaccionPago`: 1:N | Reintentos de pasarela crean nuevas transacciones sobre la misma orden |
| D3 | `commerce.Compra` no tiene FK a entidades de negocio | Separa lo genérico de lo específico; la composición vive en el módulo de dominio |
| D4 | `salesianos_fest.CompraInscripcion` tiene FK real a `commerce.Compra` | Integridad referencial a nivel DB; sin `GenericForeignKey` ni discriminadores |
| D5 | No `entity_type`, no `entity_id` | Rechazado por el usuario — se usa composición explícita con FK reales |
| D6 | `pagos` no se modifica en estructura, solo la FK y campos nuevos | `pagos` ya es agnóstico; mantiene su rol de módulo de pagos genérico |
| D7 | Todos los datos de prueba pueden eliminarse | Usuario autorizó explícitamente |

---

## 6. Impacto en API y Frontend

### 6.1 Endpoints afectados

| Endpoint actual | Acción | Notas |
|-----------------|--------|-------|
| `POST /api/compras/` | Refactorizar | El flujo FEST crea `commerce.Compra` + `CompraInscripcion` + `OrdenPago` en una transacción |
| `GET /api/compras/{id}` | Refactorizar | Resuelve `CompraInscripcion` → `commerce.Compra` |
| `POST /api/compras/{id}/iniciar-pago` | Sin cambios en firma | El flujo usa `commerce.Compra.orden_pago` |
| `POST /api/compras/confirmar-pago` | Sin cambios | Flujo igual |
| `GET /api/compras/inscripciones/{id}/compras` | Sin cambios en filtro | Ahora filtra por `CompraInscripcion.inscripcion` |

**No hay endpoints genéricos de commerce.** El módulo `commerce` no expone API propia; los endpoints viven en los módulos de dominio que lo composicionan. Esto respeta la regla de que un módulo no conoce a los demás.

### 6.2 Frontend

- Los esquemas TypeScript para compra FEST se actualizan para incluir `compra_id` (genérico) y campos de `CompraInscripcion`.
- El flujo de pago Izipay no cambia — `OrdenPago` sigue siendo la orden de pago.
- Los campos nuevos `descripcion` y `referencia_externa` en `OrdenPago` se muestran en el admin y en el portal de pagos.

### 6.3 Contratos de presentación

- `commerce.Compra` no tiene presenter de API propia.
- El presenter de compra FEST (`salesianos_fest/presentation/presenters/compra_presenter.py`) composiciona datos de `commerce.Compra` + `CompraInscripcion` y produce `CompraFESTOut`.
- `OrdenPagoOut` en `pagos/presentation/schemas/pago_schema.py` se amplía con `descripcion` y `referencia_externa`.

---

## 7. Estrategia de Migración de Datos (Destructiva)

Todos los datos son de prueba. La estrategia es **drop + reseed**.

### Fase de migración

```bash
# 1. Crear app commerce
python manage.py startapp commerce backend/modules/commerce

# 2. Makemigrations commerce (crea commerce_compra)
python manage.py makemigrations commerce

# 3. Migración personalizada en salesianos_fest:
#    a) Copiar datos de compras → commerce_compra
#    b) Crear salesianos_fest_comprainscripcion con los datos
#    c) Eliminar columna FK a Inscripcion de commerce_compra (si se agregó)
#    d) Eliminar tabla old compras de salesianos_fest
# 4. Makemigrations pagos (actualizar FK de OrdenPago → commerce.Compra, agregar campos)
# 5. Seed
```

### Detalle de la migración personalizada

La migración personalizada en `salesianos_fest` hace:

1. `INSERT INTO commerce_compra (id, responsable_id, descripcion, referencia_externa, total, estado, orden_pago_id, created_at, updated_at)` — desde las filas actuales de `compras`.
2. `INSERT INTO salesianos_fest_comprainscripcion (id, compra_id, inscripcion_id, tipo, cantidad, precio_unitario, total, created_at, updated_at)` — mapeo 1:1 en esta primera versión.
3. `DROP TABLE compras` — eliminación de la tabla antigua.
4. `ALTER TABLE pagos_ordenpago ADD COLUMN compra_id FK → commerce_compra` — actualización de la FK en `pagos`.

Como los datos son de prueba, no se requiere backwards-compatibility.

---

## 8. Estrategia de Seed y Tests

### 8.1 Seed

```python
# commerce/fixtures/seed_commerce.json
# Seed vacío — commerce.Compra no tiene datos base propios

# salesianos_fest/fixtures/seed_compras_fest.json
[
  # Crea Evento, Paquete, Persona
  # Crea Inscripcion
  # Crea commerce.Compra + CompraInscripcion (tipo=INICIAL, cantidad=10)
  # Crea OrdenPago (PENDIENTE)
]
```

### 8.2 Tests existentes a modificar

| Test | Cambio |
|------|--------|
| `test_compra.py` | Dividir: lógica genérica de compra va a `commerce/tests/`; composición FEST en `salesianos_fest/tests/` |
| `test_asignacion.py` | Actualizar fixtures para usar `commerce.Compra` + `CompraInscripcion` |

### 8.3 Tests nuevos

| Test | Ubicación | Qué prueba |
|------|-----------|------------|
| `test_comprainscripcion_one_inicial` | `salesianos_fest/tests/` | UniqueConstraint parcial impide dos INICIAL por Inscripcion |
| `test_compra_no_direct_access_from_pagos` | `pagos/tests/` | `pagos` no puede hacer FK a `salesianos_fest` |
| `test_ordenpago_descripcion_snapshot` | `pagos/tests/` | `descripcion` y `referencia_externa` se persisten en OrdenPago |
| `test_commerce_compra_is_generic` | `commerce/tests/` | `commerce.Compra` no tiene relaciones a módulos de negocio |

---

## 9. Lotes de Implementación Fásica

### Fase 1: Módulo `commerce`
1. Crear app `backend/modules/commerce/`
2. Definir `commerce/domain/models/compra.py` con campos genéricos
3. Definir `EstadoCompraChoices` en `commerce/domain/constants.py`
4. `commerce/domain/models/__init__.py`
5. Migración `0001_initial`
6. Tests unitarios de modelo (sin FK a negocio)

### Fase 2: Modificar `pagos`
1. Agregar campos `descripcion` y `referencia_externa` a `OrdenPago`
2. Cambiar FK `ordenpago.compra` de `salesianos_fest.Compra` a `commerce.Compra`
3. Tests de regresión en `pagos`

### Fase 3: Crear `CompraInscripcion` en `salesianos_fest`
1. Crear `salesianos_fest/domain/models/compra_inscripcion.py`
2. UniqueConstraint parcial `(inscripcion, tipo=INICIAL)` — una sola compra inicial
3. Flujo `CrearCompraFESTFlujo` que crea `commerce.Compra` + `CompraInscripcion` + `OrdenPago` atómicamente
4. Migración
5. Tests de composición

### Fase 4: Migrar datos y actualizar endpoints
1. Migración de datos (drop + reseed)
2. Actualizar `crear_compra_flujo.py` para usar nuevos modelos
3. Actualizar presenters y schemas
4. Actualizar controllers FEST
5. Tests end-to-end

### Fase 5: Validación
1. Ejecutar T01–T23 de la spec
2. Verificar que `pagos` no tiene regressions
3. Limpiar residuos de `salesianos_fest.Compra` antiguo
4. Persistir decisiones en Engram

---

## 10. Riesgos

| # | Riesgo | P | Impacto | Mitigación |
|---|--------|---|---------|------------|
| R1 | La FK de `OrdenPago` a `commerce.Compra` rompe referencias existentes | B | A | Drop + reseed — sin impacto |
| R2 | UniqueConstraint `(inscripcion, tipo=INICIAL)` rechaza datos existentes duplicados | M | M | Se aplica en bases de prueba limpias; validar en staging |
| R3 | El presenter FEST debe orquestar `commerce.Compra` + `CompraInscripcion` — más compleja la respuesta | M | B | El flujo ya era compuesto; el presenter solo agrega un join |
| R4 | Tests en `salesianos_fest` que usan `Compra` directa requieren rewrite completo de fixtures | A | M | Rewritear fixtures antes de la migración; no hay alternativa |
| R5 | `commerce.Compra.responsable` como FK a `Persona` acopla commerce a usuarios | B | M | Para un futuro store sin usuario autenticado, `responsable` puede ser nullable; el modelo no fuerza el acoplamiento |

---

## 11. Decisiones Explícitas Requeridas

1. **¿`commerce.Compra.responsable` es FK obligatoria o nullable?**  
   Para FEST siempre hay responsable autenticado. Para una tienda futura sin login puede ser nullable.  
   **Recomendación:** Nullable — `responsable` es información útil cuando existe, pero no es estructural para el agregado.

2. **¿La tienda futura requiere `AMPLIACION` o solo compras únicas?**  
   **Recomendación:** Diseñar `CompraTiendaItem` sin tipo INICIAL/AMPLIACION — la composición de tienda es por línea de producto, no por expansión de cantidad.

3. **¿Se elimina la columna `tipo` de `commerce.Compra`?**  
   La composición FEST lleva el `tipo`. `commerce.Compra` podría ser completamente agnóstico del tipo de compra.  
   **Recomendación:** Eliminar `tipo` de `commerce.Compra` — el tipo es preocupación del módulo de dominio, no del agregado genérico.

4. **¿`referencia_externa` en `OrdenPago` es un CharField libre o tiene un patrón?**
   **Recomendación:** CharField(100) libre — el módulo de negocio lo llena con el patrón que necesite ("FEST-INS-2026-001", "TDA-12345").

---

## 12. Criterios de Aceptación

- [ ] `commerce.Compra` no importa ningún modelo de `salesianos_fest` ni de ningún módulo de negocio
- [ ] `salesianos_fest.CompraInscripcion` tiene FK real (no string reference) a `commerce.Compra`
- [ ] No existe `entity_type` ni `entity_id` en ningún modelo
- [ ] No se usa `GenericForeignKey` en ningún modelo
- [ ] No se usa herencia de modelos Django para crear variantes de compra
- [ ] `OrdenPago` tiene `descripcion` y `referencia_externa` como snapshots de display/auditoría
- [ ] La cardinalidad `Compra → OrdenPago` es OneToOne verificada
- [ ] La cardinalidad `OrdenPago → TransaccionPago` es 1:N verificada
- [ ] Los tests T01–T23 pueden ejecutarse con los nuevos modelos
- [ ] `pagos` no ha recibido ninguna FK a módulos de negocio
