# Contrato Específico — Liquidaciones Edificaciones (PorcentajeObra)

> **Versión**: 1.0 (inicial)
> **Fecha**: 2026-08-08
> **Estado**: Documentación de implementación
> **Audiencia**: Desarrolladores que implementan el motor PorcentajeObra para Edificaciones
> **Proyecto**: comision-asuntos-municipales
> **Rama**: betha

---

## 0. Propósito

Este documento complementa el contrato replicable (`LIQUIDACIONES_REPLICABLE_CONTRACT.md`) con las reglas específicas del motor **PorcentajeObra** usado en Edificaciones. Mientras el contrato replicable define los patrones genéricos de 4 capas, wrappers y polimorfismo, este documento describe las particularidades matemáticas, modelos de datos y reglas de negocio exclusivas del cálculo por porcentaje.

El motor PorcentajeObra se diferencia de los motores M2 y Visitas en que:
- **No usa área ni visitas**: usa `valor_declarado × sum(porcentaje_tarifas)`
- **Aglomera múltiples tarifas**: el usuario selecciona N tarifas simultáneamente (Civil, Sanitaria, Eléctrica)
- **Clamping agregado**: la regla de negocio aplica al total calculado, no a cada detalle individual

---

## 1. Reglas Semánticas Confirmadas

**`porcentaje_liquidacion`** = SUMA de todos los porcentajes de las tarifas aplicadas.
- Ejemplo: 3 tarifas a 0.0015 cada una → `porcentaje_liquidacion = 0.0045` (0.45%)

**Cada `Detalle.subtotal`** = `valor_declarado × tarifa.porcentaje_liquidacion`

**`LiquidacionGeneral.sub_total`** = SUMA de todos los `Detalle.subtotal`

**`LiquidacionGeneral.total`** = `sub_total + IGV`

---

## 2. Reglas Semánticas — `tipo_tramite` (Future-State)

**`tipo_tramite` es OPCIONAL y se deja NULL por ahora.**

El modelo `LiquidacionPorcentajeObra.tipo_tramite` existe y acepta valores del enum `TipoTramiteEdificaciones` (OBRA_NUEVA, AMPLIACION, REMODELACION, etc.), pero:

- Por ahora NO se envía en el input
- Por ahora NO se persiste (queda NULL)
- Por ahora NO se valida en el output

**Cuándo se activará** (futuro): cuando el frontend necesite distinguir entre tipos de trámite para reglas de negocio específicas. La implementación futura:

```python
# En Orchestrator:
if payload.tipo_tramite:
    liquidacion_porcentaje.tipo_tramite = payload.tipo_tramite
else:
    liquidacion_porcentaje.tipo_tramite = None  # explícitamente NULL

# En Presenter:
class LiquidacionPorcentajeObraDatosOut(BaseSchema):
    tipo_tramite: Optional[str]  # None permitido
```

**Migración futura requerida**: si se agregan validaciones tipo "primera revisión solo permite tipo_tramite=OBRA_NUEVA", se necesitará un constraint en DB.

---

## 3. Wrappers de Input (2 wrappers, 2 modos)

Todo endpoint de creación recibe exactamente 2 wrappers. Existen dos modos de especificar las tarifas:

### Modo A: Auto-fill (práctico para primera revisión)

```json
{
  "liquidacion_general": {
    "municipalidad_id": "uuid",
    "expediente": "string",
    "observacion": "string or null",
    "proyecto": {
      "denominacion": "string",
      "nombre_propietario": "string",
      "direccion": "string",
      "distrito_id": "uuid",
      "entidad": {
        "tipo_documento": "RUC|DNI",
        "numero_documento": "string",
        "razon_social": "string"
      }
    }
  },
  "liquidacion_especifica": {
    "datos": {
      "valor_declarado": 100000.00
    },
    "tarifas": []
  }
}
```

Backend auto-rellena con todas las `TarifaPorcentajeObra` vigentes para `TipoLiquidacion.EDIFICACION`.

### Modo B: Explícito (futuro, mixto, custom)

```json
{
  "liquidacion_general": {
    "municipalidad_id": "uuid",
    "expediente": "string",
    "observacion": "string or null",
    "proyecto": {
      "denominacion": "string",
      "nombre_propietario": "string",
      "direccion": "string",
      "distrito_id": "uuid",
      "entidad": {
        "tipo_documento": "RUC|DNI",
        "numero_documento": "string",
        "razon_social": "string"
      }
    }
  },
  "liquidacion_especifica": {
    "datos": {
      "valor_declarado": 100000.00
    },
    "tarifas": [
      { "tarifa_porcentaje_obra_id": "uuid-tarifa-1ra-civil" },
      { "tarifa_porcentaje_obra_id": "uuid-tarifa-1ra-sanitaria" },
      { "tarifa_porcentaje_obra_id": "uuid-tarifa-1ra-electrica" }
    ]
  }
}
```

Frontend selecciona explícitamente. Backend valida que cada una esté vigente y sea de EDIFICACION.

**Importante**: NO se envía `tipo_tramite` (queda NULL).
**Importante**: NO se envía `especialidad_id` (la tarifa ya tiene FK a Especialidad).
**Importante**: NO se envía `usuario_creador`, `retencion`, `estado` (del JWT/default).

---

## 4. Wrappers de Output (3 wrappers)

```json
{
  "liquidacion_general": {
    "id": "uuid",
    "municipalidad_id": "uuid",
    "usuario_creador": { "id": "uuid" },
    "fecha_registro": "iso-datetime",
    "expediente": "string",
    "observacion": "string or null",
    "numero_revision": 1,
    "sub_total": 450.00,
    "total": 531.00,
    "igv_id": "uuid",
    "uit_id": "uuid",
    "proyecto": { ... }
  },
  "liquidacion_especifica": {
    "id": "uuid",
    "numero": 1
  },
  "liquidacion_tipo": {
    "id": "uuid",
    "valor_declarado": 100000.00,
    "porcentaje_liquidacion": 0.0045,
    "tipo_tramite": null,
    "derecho_minimo": 129.80,
    "derecho_maximo": null,
    "porcentaje_minimo_uit": 0.02,
    "derecho_aplicado_id": "uuid-derecho",
    "detalles": [
      {
        "id": "uuid",
        "especialidad_id": "uuid",
        "tarifa_aplicada_id": "uuid",
        "porcentaje_aplicado": 0.0015,
        "subtotal": 150.00,
        "igv": 27.00,
        "uit": 110.00,
        "total": 177.00
      }
    ]
  }
}
```

---

## 5. Lógica de Cálculo

### 5.0 Resolución Híbrida de Tarifas

```python
# En el Orchestrator, ANTES de calcular:
def resolver_tarifas(payload_tarifas):
    if not payload_tarifas:  # Array vacío → auto-fill
        return TarifaPorcentajeObra.objects.filter(
            tarifa_base__tipo_liquidacion=TipoLiquidacion.EDIFICACION,
            tarifa_base__vigentes=True,
        )
    else:  # Explícito → validar
        tarifas = []
        for t in payload_tarifas:
            tarifa = TarifaPorcentajeObra.objects.get(id=t.tarifa_porcentaje_obra_id)
            if not tarifa.tarifa_base.vigentes:
                raise HttpError(400, f"Tarifa {tarifa.id} no está vigente")
            if tarifa.tarifa_base.tipo_liquidacion != TipoLiquidacion.EDIFICACION:
                raise HttpError(400, f"Tarifa {tarifa.id} no es de edificaciones")
            tarifas.append(tarifa)
        return tarifas
```

**Razón**: el modo auto-fill simplifica el caso común (primera revisión = todas las tarifas). El modo explícito permite casos futuros (mixto, custom).

### 5.1 Por Detalle

Para cada tarifa en `tarifas[]`:

```python
detalle.subtotal = valor_declarado × tarifa.porcentaje_liquidacion
detalle.igv = detalle.subtotal × igv_vigente.valor  # ej: 0.18
detalle.uit = valor_declarado × porcentaje_minimo_uit  # ej: 0.0011 (informativo)
detalle.total = detalle.subtotal + detalle.igv
```

### 5.2 Agregado

```python
porcentaje_liquidacion = sum(tarifa.porcentaje_liquidacion for tarifa in tarifas)
total_subtotal_calculado = sum(detalle.subtotal for detalle in detalles)
```

### 5.3 Clamping (en Orchestrator)

```python
# Clamping aplicado POR DETALLE
for detalle in detalles:
    minimo_subtotal = uit_vigente.valor * derecho.porcentaje_minimo_uit
    detalle.subtotal = max(
        valor_declarado * tarifa.porcentaje_liquidacion,
        minimo_subtotal
    )
    detalle.igv = detalle.subtotal × igv_vigente.valor
    detalle.total = detalle.subtotal + detalle.igv

# Sumas agregadas
total_subtotal_calculado = sum(detalle.subtotal for detalle in detalles)
total_calculado = sum(detalle.total for detalle in detalles)
```

**Razón**: la regla de negocio dice "el cobro por cada especialidad no puede ser menor al mínimo legal (X% UIT)". El clamping se aplica a cada detalle individualmente y luego se suman para el total.

### Ejemplo Visual de Clamping (Mínimo Dinámico por Detalle)

**Variables del Sistema:**
- UIT Vigente = S/. 5,500
- IGV = 18% (0.18)
- `porcentaje_minimo_uit` = 0.02 (2%)

**Cálculo del Mínimo:**
- Subtotal Mínimo = `5,500 × 0.02` = **S/. 110.00**
- Total Mínimo (con IGV) = `110.00 × 1.18` = **S/. 129.80**

**Escenario A: El cálculo es MENOR al mínimo (Se aplica Clamping)**
- `valor_declarado` = S/. 10,000
- `tarifa.porcentaje` = 0.0015 (0.15%)

1. Subtotal crudo: `10,000 × 0.0015` = **S/. 15.00**
2. Clamping: `max(15.00, 110.00)` = **S/. 110.00** 🛑 *(¡Subió al mínimo!)*
3. IGV: `110.00 × 0.18` = S/. 19.80
4. Total del detalle: `110.00 + 19.80` = **S/. 129.80**

**Escenario B: El cálculo es MAYOR al mínimo (NO se aplica Clamping)**
- `valor_declarado` = S/. 100,000
- `tarifa.porcentaje` = 0.0015 (0.15%)

1. Subtotal crudo: `100,000 × 0.0015` = **S/. 150.00**
2. Clamping: `max(150.00, 110.00)` = **S/. 150.00** ✅ *(Se respeta el monto mayor)*
3. IGV: `150.00 × 0.18` = S/. 27.00
4. Total del detalle: `150.00 + 27.00` = **S/. 177.00**

---

## 6. Reglas de Negocio (Porcentajes)

| Escenario | % | Base | Mínimo |
|-----------|---|------|--------|
| Primera Rev / Demolición / Reintegro | 0.15% | Valor FUE | S/ 129.80 (2% UIT + IGV) |
| Ampliación / Remodelación | 0.15% | Valor FUE | S/ 129.80 |
| Especialidad / 3ra+ Rev | 0.05% | Valor Inicial | S/ 129.80 |
| Modificación Licencia / Variación | 0.05% | Valor Inicial | S/ 129.80 |

El usuario selecciona el `TarifaPorcentajeObra` apropiado (que ya tiene el % incluido).

---

## 7. Modelo de Datos (4 tablas)

```
LiquidacionGeneral (cabecera común)
   └─→ LiquidacionEdificacion (identidad: id + numero, AutoNumeroModel)
        └─→ LiquidacionPorcentajeObra (motor: valor_declarado, %)
             ├─→ derecho_aplicado (FK → DerechoPorcentajeObra)
             └─→ tarifas_aplicadas (M2M → TarifaPorcentajeObra, through Detalle)
                  └─→ LiquidacionPorcentajeObraDetalle (1-N por especialidad)
                       ├─→ tarifa_aplicada (FK → TarifaPorcentajeObra)
                       ├─→ especialidad (FK → Especialidad)
                       └─→ subtotal, igv, uit, total
```

### Tablas Involucradas

| Modelo | Hereda de | Propósito |
|--------|-----------|-----------|
| `LiquidacionGeneral` | TimestampModel | Cabecera común: municipalidad, expediente, proyecto, totales |
| `LiquidacionEdificacion` | AutoNumeroModel | Identidad del trámite Edificación (id + numero) |
| `LiquidacionPorcentajeObra` | BaseModel | Motor: valor_declarado, porcentaje_liquidacion, derecho_minimo/max |
| `LiquidacionPorcentajeObraDetalle` | BaseModel | Detalle por especialidad: subtotal, igv, uit, total |

---

## 8. Multiplicidad

| Relación | Cardinalidad |
|----------|--------------|
| LiquidacionGeneral → LiquidacionEdificacion | 1:1 |
| LiquidacionEdificacion → LiquidacionPorcentajeObra | 1:1 |
| LiquidacionPorcentajeObra → Detalles | 1:N |
| Detalle → TarifaPorcentajeObra | N:1 |
| Detalle → Especialidad | N:1 |
| LiquidacionPorcentajeObra → DerechoPorcentajeObra | N:1 |

**Nota sobre `tarifas[]` en input**:
- Es una lista (puede estar vacía)
- Si está vacía → auto-fill con todas las vigentes
- Si tiene elementos → validación explícita

**Multiplicidad de salida**:
- `detalles[]` siempre tiene al menos 1 elemento (las especialidades procesadas)
- En el modo auto-fill para primera revisión, típicamente 3 detalles (Civil, Sanitaria, Eléctrica)

---

## 9. Ejemplos de Cálculo

### Ejemplo 1: Caso normal (sin clamping)

- valor_declarado: 100,000
- 3 tarifas a 0.0015 (Civil, Sanitaria, Eléctrica)
- IGV: 18%
- UIT: 5,500

```python
Civil:    subtotal=150.00, igv=27.00, total=177.00
Sanitaria: subtotal=150.00, igv=27.00, total=177.00
Electrica: subtotal=150.00, igv=27.00, total=177.00

porcentaje_liquidacion = 0.0045
LiquidacionGeneral.sub_total = 450.00
LiquidacionGeneral.total = 531.00
```

### Ejemplo 2: Clamping mínimo aplicado (POR DETALLE)

- valor_declarado: 10,000 (bajo)
- 3 tarifas a 0.0015
- UIT vigente: 5,500
- porcentaje_minimo_uit: 0.02 (2%)
- IGV: 18%

```python
# Cada tarifa calcula: valor_declarado × porcentaje = 10,000 × 0.0015 = 15
# Mínimo por detalle: uit_vigente × porcentaje_minimo_uit = 5,500 × 0.02 = 110
# Como 15 < 110, se aplica clamping POR CADA DETALLE

Civil:    subtotal=max(15, 110)=110, igv=19.80, total=129.80
Sanitaria: subtotal=max(15, 110)=110, igv=19.80, total=129.80
Electrica: subtotal=max(15, 110)=110, igv=19.80, total=129.80

LiquidacionGeneral.sub_total = 330.00
LiquidacionGeneral.total = 389.40
```

---

## 10. Contrato de 4 Capas (Aplicación Específica)

El patrón de 4 capas del contrato replicable se aplica idénticamente a Edificaciones:

- **Controller**: `liquidacion_edificaciones_controller.py` — thin,/delega
- **Orchestrator**: `liquidacion_edificaciones_orchestrator.py` — valida, aplica clamping
- **Flujo**: `liquidacion_edificaciones_flujo.py` — `@transaction.atomic`, coordina
- **Core**: `liquidacion_porcentaje_obra_core_service.py` — ORM puro + aritmética

### Responsabilidades Específicas por Capa

| Capa | Responsabilidad en PorcentajeObra |
|------|----------------------------------|
| Controller | Recibe `LiquidacionEdificacionesInput`, delega a Orchestrator, formatea con Presenter |
| Orchestrator | Valida `valor_declarado > 0`, aplica clamping, mapea a DTO |
| Flujo | Coordina: upsert Entidad → upsert Proyecto → lookup Tarifas → create LiquidacionGeneral → create LiquidacionEdificacion → create LiquidacionPorcentajeObra → create Detalles |
| Core | math pura: `valor × porcentaje`, `subtotal × igv`, clamping factor |

---

## 11. Endpoints

```
GET  /api/liquidaciones/edificaciones/tarifas/vigentes
POST /api/liquidaciones/edificaciones/cotizar
POST /api/liquidaciones/edificaciones/nueva-liquidacion/primera-revision
```

### GET /api/liquidaciones/edificaciones/tarifas/vigentes

Retorna las tarifas de porcentaje de obra vigentes para el tipo de cálculo seleccionado.

**Response**:
```json
{
  "tarifas": [
    {
      "id": "uuid",
      "nombre": "Civil",
      "porcentaje_liquidacion": 0.0015,
      "especialidad": { "id": "uuid", "nombre": "Civil" }
    },
    {
      "id": "uuid",
      "nombre": "Sanitaria",
      "porcentaje_liquidacion": 0.0015,
      "especialidad": { "id": "uuid", "nombre": "Sanitaria" }
    },
    {
      "id": "uuid",
      "nombre": "Eléctrica",
      "porcentaje_liquidacion": 0.0015,
      "especialidad": { "id": "uuid", "nombre": "Eléctrica" }
    }
  ]
}
```

### POST /api/liquidaciones/edificaciones/cotizar

Simula el cálculo sin persistir. Aplica clamping.

**Request**: Mismo formato que `nueva-liquidacion` pero sin `liquidacion_general.expediente`.

### POST /api/liquidaciones/edificaciones/nueva-liquidacion/primera-revision

Crea la liquidación persistida.

---

## 12. Archivos a Crear (Plan de Implementación)

| # | Path | Propósito | Clases/Métodos Clave |
|---|------|-----------|----------------------|
| 1 | `modules/liquidaciones/domain/models/liquidacion/liquidacion_especifico/liquidacion_edificacion.py` | Modelo identidad Edificación | `LiquidacionEdificacion` (AutoNumeroModel) |
| 2 | `modules/liquidaciones/domain/models/liquidacion/liquidacion_porcentaje/liquidacion_porcentaje_obra.py` | Modelo motor | `LiquidacionPorcentajeObra`, `LiquidacionPorcentajeObraDetalle` |
| 3 | `modules/liquidaciones/domain/services/core/liquidacion_porcentaje/liquidacion_porcentaje_obra_core_service.py` | Lógica matemática pura | `resolver_tarifas(tarifas_ids)`, `calcular_cotizacion_po()`, `create_liquidacion_porcentaje_obra()` |
| 4 | `modules/liquidaciones/domain/services/flujos/liquidacion_edificaciones_flujo.py` | Flujo transaccional | `_ejecutar_primera_revision_sync()` con `@transaction.atomic` |
| 5 | `modules/liquidaciones/domain/services/orchestrators/liquidacion_edificaciones_orchestrator.py` | Validación y clamping | `crear_primera_revision_proceso()` |
| 6 | `modules/liquidaciones/domain/schemas/liquidacion_edificaciones_data.py` | DTOs de dominio | `EdificacionesPrimeraRevisionData` |
| 7 | `modules/liquidaciones/domain/results/liquidacion_edificaciones_result.py` | Results de dominio | `EdificacionesPrimeraRevisionResult` |
| 8 | `modules/liquidaciones/presentation/schemas/liquidacion_edificaciones_schemas.py` | Schemas Input/Output | `LiquidacionEdificacionesInput`, `LiquidacionEdificacionesOutput` |
| 9 | `modules/liquidaciones/presentation/presenters/liquidacion_edificaciones_presenter.py` | Mapeo Result → Schema | `present_primera_revision()` |
| 10 | `modules/liquidaciones/presentation/controllers/liquidacion_edificaciones_controller.py` | Entry point HTTP | `crear_primera_revision()` |
| 11 | `modules/liquidaciones/presentation/controllers/liquidacion_edificaciones_tarifas_controller.py` | Tarifas vigentes | `listar_tarifas_vigentes()` |

**Nota sobre el Core service**:
```python
# En liquidacion_porcentaje_obra_core_service.py:
"""
Core service for PorcentajeObra calculations.

Key methods:
- resolver_tarifas(tarifas_ids: list) -> list[TarifaPorcentajeObra]
  Hybrid resolution: empty list → auto-fill, non-empty → validate each.
- calcular_cotizacion_po(valor_declarado, tarifas_ids) -> CotizacionPOResult
- create_liquidacion_porcentaje_obra(...) -> LiquidacionPorcentajeObra
- create_liquidacion_porcentaje_obra_detalle(...) -> LiquidacionPorcentajeObraDetalle
- get_derecho_porcentaje_vigente() -> DerechoPorcentajeObra
- get_tarifas_porcentaje_vigentes() -> list[TarifaPorcentajeObra]

FUTURE: when tipo_tramite is activated, add:
- validar_tipo_tramite_permitido(tipo_tramite, accion) -> bool
"""
```

---

## 13. Orden de Implementación

### Phase 1: Domain Layer (DTOs, Results, Core Service)

1. `liquidacion_porcentaje_obra.py` (modelos)
2. `liquidacion_edificacion.py` (modelo identidad)
3. `liquidacion_porcentaje_obra_core_service.py`
4. `liquidacion_edificaciones_data.py` (DTOs)
5. `liquidacion_edificaciones_result.py` (Results)

### Phase 2: Business Logic (Flujo, Orchestrator)

6. `liquidacion_edificaciones_orchestrator.py`
7. `liquidacion_edificaciones_flujo.py`

### Phase 3: API Layer (Schemas, Presenter, Controller)

8. `liquidacion_edificaciones_schemas.py`
9. `liquidacion_edificaciones_presenter.py`
10. `liquidacion_edificaciones_controller.py`
11. `liquidacion_edificaciones_tarifas_controller.py`

### Phase 4: Tests + DI bindings

12. Tests unitarios por capa
13. Tests de integración del endpoint
14. Registrar modelos en `__init__.py`
15. Configurar URLs en el router

---

## 14. Tests Requeridos

### Tests de Core Service

| Test | Descripción |
|------|-------------|
| `test_calcular_cotizacion_porcentaje_sin_clamping` | valor_declarado=100000, 3 tarifas×0.0015 → sub_total=450 |
| `test_calcular_cotizacion_porcentaje_con_clamping_minimo` | valor_declarado=10000 → total<129.80, verificar factor aplicado |
| `test_calcular_cotizacion_porcentaje_sin_tarifas` | Debe lanzar HttpError 400 |
| `test_valor_declarado_cero` | Debe lanzar HttpError 400 |
| `test_valor_declarado_negativo` | Debe lanzar HttpError 400 |

### Tests de Orchestrator

| Test | Descripción |
|------|-------------|
| `test_clamping_minimo_distribuye_proporcionalmente` | Verificar que el factor se aplica a cada detalle |
| `test_clamping_maximo_distribuye_proporcionalmente` | Mismo para max |
| `test_clamping_no_aplicado_caso_normal` | Factor = 1.0 cuando no se necesita clamping |

### Tests de Flujo (Integración DB)

| Test | Descripción |
|------|-------------|
| `test_crear_primera_revision_edificacion` | Creación completa, verificar totales |
| `test_crear_segunda_revision_edificacion` | Incrementa `numero` a 2 |
| `test_upsert_entidad_por_documento` | Mismo RUC → no duplica Entidad |

### Tests de Controller/Endpoint

| Test | Descripción |
|------|-------------|
| `test_post_primera_revision_201` | Endpoint retorna 200, wrappers correctos |
| `test_get_tarifas_vigentes_200` | Lista tarifas con especialidad |
| `test_post_cotizar_sin_persistir` | Solo retorna cálculo, no crea registros |

### Tests de Hybrid Mode (Tarifas)

| Test | Setup | Action | Assertions |
|------|-------|--------|------------|
| Auto-fill mode (empty array) | 3 vigentes tarifas created | POST con `tarifas: []` | All 3 detalles created, response OK |
| Explicit mode (3 tarifas) | 3 vigentes tarifas created | POST con 3 tarifa_ids | All 3 detalles created, response OK |
| Invalid tarifa_id | 3 vigentes + 1 expired | POST con expired tarifa_id | 400 error "Tarifa no vigente" |
| Tarifa of wrong type (HU instead of EDIFICACION) | HU tarifa created | POST con HU tarifa_id | 400 error "Tarifa no es de edificaciones" |

---

## 15. Gaps Pre-existentes

### Gap 1: `ReglaTarifaEdificacion` referenciado pero no existe

El seed script de tasas referencia `ReglaTarifaEdificacion` en la configuración de `TarifaPorcentajeObra`, pero el modelo no existe en el codebase actual. **Acción requerida**: Crear el modelo o ajustar el seed.

### Gap 2: Seed script asigna campos no existentes en `TarifaPorcentajeObra`

El seed establece `fields['tarifa_porcentaje_obra']['derecho_minimo']` y `fields['tarifa_porcentaje_obra']['derecho_maximo']` en el seed, pero estos campos podrían no existir en el modelo actual. **Acción requerida**: Verificar modelo `TarifaPorcentajeObra` y ajustar seed o modelo.

### Gap 3: Endpoint `GET tarifas-vigentes` no existe

El endpoint `GET /api/liquidaciones/edificaciones/tarifas/vigentes` es necesario para que el frontend pueda mostrar las tarifas disponibles al usuario antes de cotizar. **Acción requerida**: Implementar en `liquidacion_edificaciones_tarifas_controller.py`.

---

## 16. Preguntas Abiertas

### P1: ¿Cómo se determina `derecho_minimo` y `derecho_maximo`?

¿Viene de la tarifa seleccionada, del `DerechoPorcentajeObra`, o es un valor fijo en `LiquidacionPorcentajeObra`?

**Hipótesis actual**: `derecho_minimo` y `derecho_maximo` se copian del `DerechoPorcentajeObra` asociado a la primera tarifa seleccionada (o al tipo de trámite).

### P2: ¿El `porcentaje_minimo_uit` es fijo o viene de la tarifa?

El ejemplo usa 0.02 (2% UIT). ¿Es un valor fijo del sistema o depende de la tarifa/escenario?

### P3: ¿Se permite mezclar tarifas de diferentes escenarios?

~~¿El usuario puede mezclar tarifas de "Primera Rev" con tarifas de "Especialidad"?~~ → **RESUELTO with hybrid mode**: El modo auto-fill usa todas las vigentes; el modo explícito permite selección. La mezcla depende de las reglas de negocio futuras.

### P4: ¿Qué pasa cuando `tipo_tramite` deje de ser NULL?

~~¿Se usará para filtrar qué tarifas son válidas?~~ → **DOCUMENTADO**: `tipo_tramite` es future-state. Por ahora es NULL. Cuando se active, se agregará validación en Orchestrator y Presenter.

### P5: ¿El clamping aplica solo al sub_total o al total (incluyendo IGV)?

~~La regla dice "el cobro total no puede ser menor al derecho mínimo".~~ → **CONFIRMADO**: Clamping aplica al TOTAL (sub_total + IGV), con distribución proporcional por detalle. El clamping se hace sobre el total calculado (sub_total × (1 + igv)).

### P6: Whether to validate frontend can send empty array (mode auto-fill) AND non-empty array (mode explicit) in same endpoint

El endpoint acepta ambos modos en el mismo endpoint. ¿Se debe validar que no se mezclen modos?

---

## 17. Relación con Contrato Replicable

Este documento es un **anexo específico** al contrato replicable. Las siguientes secciones del contrato replicable aplican sin modificación:

| Sección del Contrato Replicable | Aplicabilidad |
|--------------------------------|---------------|
| Sección 1: Regla Semántica de Wrappers | ✅ Aplica (3 wrappers: general, especifico=identidad, tipo=cálculo) |
| Sección 2: Wrappers de Input (2 obligatorios) | ✅ Aplica con las particularidades de Sección 2 de este doc |
| Sección 3: Wrappers de Output (3 obligatorios) | ✅ Aplica con `detalles[]` en `liquidacion_tipo` |
| Sección 4: Contrato de 4 Capas | ✅ Aplica idénticamente |
| Sección 5: Regla de Snapshot | ✅ Aplica (porcentaje, valor_declarado son snapshots) |
| Sección 6: Patrón de Polimorfismo | ✅ Aplica (crear, no modificar) |
| Sección 7: Configuración de Tests | ✅ Aplica |
| Sección 9: Convenciones de Imports | ✅ Aplica (absolutos siempre) |
| Sección 10: Reglas Críticas | ✅ Aplica |

---

## Anexo: Convenciones de Imports

**Imports absolutos** (obligatorio):

```python
from modules.liquidaciones.domain.models.liquidacion.liquidacion_especifico.liquidacion_edificacion import LiquidacionEdificacion
from modules.liquidaciones.domain.models.liquidacion.liquidacion_porcentaje.liquidacion_porcentaje_obra import LiquidacionPorcentajeObra, LiquidacionPorcentajeObraDetalle
from modules.liquidaciones.domain.services.core.liquidacion_general import LiquidacionGeneralCoreService
from modules.liquidaciones.domain.services.core.liquidacion_porcentaje.liquidacion_porcentaje_obra_core_service import LiquidacionPorcentajeObraCoreService
from modules.liquidaciones.presentation.schemas.liquidacion_edificaciones_schemas import LiquidacionEdificacionesInput, LiquidacionEdificacionesOutput
```

**NUNCA relativos con puntos**:
```python
# ❌ PROHIBIDO
from ..models import LiquidacionEdificacion
from ...core import LiquidacionPorcentajeObraCoreService
```
