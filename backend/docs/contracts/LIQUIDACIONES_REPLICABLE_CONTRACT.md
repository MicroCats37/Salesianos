# Contrato Replicable — Módulo Liquidaciones

> **Versión**: 1.0 (definitiva, post-swap semántico)
> **Fecha**: 2026-08-08
> **Estado**: Fuente de verdad arquitectónica
> **Audiencia**: Desarrolladores que implementan nuevos tipos de liquidación (Edificaciones, Mecánica de Suelos, Impacto Vial, Taludes, Reintegro)

---

## 0. Propósito

Este documento es la **fuente de verdad arquitectónica** para crear nuevos tipos de liquidación en el módulo `liquidaciones`. Define el contrato de 4 capas, los wrappers de entrada/salida, las reglas semánticas y el patrón de polimorfismo que permite extender el sistema sin modificar código base.

**Aplicabilidad**: Cualquier nuevo tipo de liquidación que siga uno de los tres motores de cálculo:
- **M2** (área × costo_por_m²): HU, Mecánica de Suelos, Impacto Vial, Taludes
- **Visitas** (cantidad × UIT%): Inspección de Obra
- **Porcentaje** (valor_proyecto × %): Edificaciones

---

## 1. Regla Semántica de Wrappers (DEFINITIVA)

Esta es la regla más importante. Si no se entiende esto, todo lo demás falla.

| Wrapper | Significado | Contenido (Output) |
|---------|-------------|---------------------|
| `liquidacion_general` | Cabecera común | Datos administrativos: municipalidad, usuario_creador, expediente, proyecto, totales, FK IGV/UIT |
| `liquidacion_especifica` | **Identidad del trámite** | Solo `id` (UUID) + `numero` (autoincremental de `AutoNumeroModel`) |
| `liquidacion_tipo` | **Motor de cálculo** | Datos computacionales: `area_m2`, `costo_por_m2`, `cantidad_visitas`, `porcentaje_uit`, etc. + FK a la tarifa aplicada |

### 1.1. Equivalencia conceptual

```
liquidacion_especifica = "¿CUÁL es este trámite?"     → Identidad (id + numero)
liquidacion_tipo        = "¿CÓMO se calculó?"          → Cálculo (datos + matemática)
liquidacion_general     = "¿QUIÉN, DÓNDE, CUÁNTO?"    → Cabecera administrativa
```

### 1.2. Por qué importa

Antes (incorrecto, swapped):
- `liquidacion_tipo` → `{ id, numero }` ← MAL, debería ser cálculo
- `liquidacion_especifica` → `{ area_m2, costo_por_m2 }` ← MAL, debería ser identidad

Después (correcto, definitivo):
- `liquidacion_especifica` → `{ id, numero }` ← Identidad
- `liquidacion_tipo` → `{ area_m2, costo_por_m2, derecho_minimo, ... }` ← Cálculo

---

## 2. Wrappers de Input (2 obligatorios)

Todo endpoint de creación recibe EXACTAMENTE 2 wrappers:

```python
class LiquidacionTipoInput(BaseSchema):  # Nombre genérico, varía por tipo
    liquidacion_general: LiquidacionGeneralRevisionIn     # Siempre presente
    liquidacion_especifica: LiquidacionTipoDatosIn        # datos + tarifa (NO identidad)
```

### 2.1. `liquidacion_general` — Cabecera Input

```python
class LiquidacionGeneralRevisionIn(BaseSchema):
    municipalidad_id: uuid.UUID          # FK plana
    expediente: str
    observacion: Optional[str]
    proyecto: ProyectoCotizarSchema      # Proyecto INLINE (no FK)
```

### 2.2. `liquidacion_especifica` — Datos de Cálculo (nombre confuso, contiene cálculo)

**Importante**: aunque se llame `liquidacion_especifica` en el input, contiene los datos del motor de cálculo. La "identidad" solo aparece en el output.

**Para M2**:
```python
class LiquidacionPorMetroCuadradoIn(BaseSchema):
    datos: LiquidacionPorMetroCuadradoDatosIn       # area_solicitada
    tarifa: LiquidacionPorMetroCuadradoTarifaIn     # tarifa_m2_id (FK plana)
```

**Para Visitas**:
```python
class LiquidacionPorCategoriaVisitasIn(BaseSchema):
    datos: LiquidacionPorCategoriaVisitasDatosIn    # cantidad_visitas, categoria
    tarifa: LiquidacionPorCategoriaVisitasTarifaIn  # tarifa_visitas_id (FK plana)
```

### 2.3. Campos PROHIBIDOS en el JSON de Input

- `usuario_creador` (viene del JWT, no del body)
- `retencion` (default `false`, no se envía)
- `estado` (default automático, no se envía)
- `tipo_calculo` (NO EXISTE en el modelo)
- `concepto` (NO EXISTE en el modelo)

### 2.4. IDs seleccionables van planos con sufijo `_id`

```json
{
  "liquidacion_general": {
    "municipalidad_id": "uuid-here",
    "distrito_id": "uuid-here",
    "proyecto": { ... inline ... }
  },
  "liquidacion_especifica": {
    "datos": { ... },
    "tarifa": { "tarifa_m2_id": "uuid-here" }
  }
}
```

---

## 3. Wrappers de Output (3 obligatorios)

Todo endpoint de creación retorna EXACTAMENTE 3 wrappers:

```python
class LiquidacionTipoOutput(BaseSchema):
    liquidacion_general: LiquidacionGeneralOutput           # Siempre presente
    liquidacion_especifica: LiquidacionTipoOutput            # Identidad: id + numero
    liquidacion_tipo: LiquidacionTipoDatosOut                # Cálculo (varía por tipo)
```

### 3.1. `liquidacion_general` — Cabecera Output

```python
class LiquidacionGeneralOutput(BaseSchema):
    id: uuid.UUID
    municipalidad_id: uuid.UUID          # FK plana
    usuario_creador: UsuarioCreadorOutput  # ANIDADO: solo { id }
    fecha_registro: str
    expediente: str
    observacion: Optional[str]
    numero_revision: int
    sub_total: float                     # ⚠️ CON guión bajo (NO "subtotal")
    total: float
    igv_id: Optional[uuid.UUID]          # FK plana (NO igv_snapshot)
    uit_id: Optional[uuid.UUID]          # FK plana (NO uit_snapshot)
    proyecto: ProyectoOutput
```

### 3.2. `liquidacion_especifica` — Identidad (SOLO 2 campos)

```python
class LiquidacionTipoOutput(BaseSchema):  # Output de identidad
    id: uuid.UUID   # PK de la tabla específica (ej: LiquidacionHabilitacionUrbana.id)
    numero: int     # Auto-correlativo (de AutoNumeroModel)
```

### 3.3. `liquidacion_tipo` — Datos del Motor de Cálculo

**Para M2** (HU, Mecánica Suelos, Impacto Vial, Taludes):
```python
class LiquidacionPorMetroCuadradoDatosOut(BaseSchema):
    id: uuid.UUID
    area_m2: float
    costo_por_m2: float
    derecho_minimo: float
    derecho_maximo: float
    tarifa_aplicada_id: uuid.UUID        # FK a TarifaPorMetroCuadrado
    derecho_aplicado_id: uuid.UUID       # FK a DerechoPorMetroCuadrado
```

**Para Visitas** (Inspección de Obra):
```python
class LiquidacionPorCategoriaVisitasDatosOut(BaseSchema):
    id: uuid.UUID
    cantidad_visitas: int
    porcentaje_uit: float
    categoria: str
    tarifa_aplicada_id: uuid.UUID        # FK a TarifaPorCategoriaVisitas
```

**Importante**: Visitas NO tiene `derecho_minimo` / `derecho_maximo` (esos campos solo aplican a M2).

### 3.4. Campos PROHIBIDOS en el JSON de Output

- `igv_snapshot` / `uit_snapshot` (solo se exponen como FK plana: `igv_id`, `uit_id`)
- `tipo_calculo` (NO EXISTE)
- `concepto` (NO EXISTE)
- `subtotal` sin guión bajo (correcto: `sub_total`)

---

## 4. Contrato de 4 Capas

Cada endpoint sigue EXACTAMENTE esta cadena:

```
HTTP Request
    ↓
[1] Controller (Presentation)     ← sync def, sin if/for/ORM
    ↓
[2] Orchestrator (Domain)        ← sync def, valida con HttpError, sin ORM
    ↓
[3] Flujo (Domain)               ← sync def + @transaction.atomic, sin validación
    ↓
[4] Core (Infrastructure)        ← sync def, ORM puro, sin HttpError, sin lógica
    ↓
ORM models / DB
```

### 4.1. Controller — `presentation/controllers/liquidacion_especifico/`

**Responsabilidades (únicas)**:
- Recibir HTTP request
- Extraer `usuario_id` del JWT
- Llamar al Orchestrator
- Mapear Result → Schema via Presenter
- Retornar respuesta

**PROHIBIDO en Controller**:
- `if`, `for`, `try/except` (excepto decoradores del framework)
- Acceso directo a ORM (`.objects.get()`, `.filter()`, etc.)
- Validaciones de negocio
- Cálculos matemáticos

```python
@api_controller("/liquidaciones/habilitacion-urbana")
class LiquidacionHabilitacionUrbanaController:
    @route.post("/nueva-liquidacion/primera-revision")
    def crear_primera_revision(self, request, payload: LiquidacionHabilitacionUrbanaInput):
        usuario_id = request.user.id
        domain_result = self.orchestrator.crear_primera_revision_proceso(
            usuario_id=usuario_id, payload_in=payload
        )
        result = self.presenter.present_primera_revision(domain_result)
        return success_response(result)
```

### 4.2. Orchestrator — `domain/services/orchestrators/liquidacion_especifico/`

**Responsabilidades (únicas)**:
- Validar inputs del Presentation Schema (HttpError 400)
- Mapear Presentation Schema → Domain DTO
- Aplicar reglas de clamping (ej: M2 min/max)
- Llamar al Flujo
- NO hace ORM directo

**PROHIBIDO en Orchestrator**:
- `@transaction.atomic` (solo en Flujo)
- Acceso directo a ORM (excepto lecturas de IGV/UIT/Tarifa para validación)
- Cálculos matemáticos complejos

```python
class LiquidacionHabilitacionUrbanaOrchestrator:
    def crear_primera_revision_proceso(self, usuario_id, payload_in):
        # Validación
        if payload_in.liquidacion_especifica.datos.area_solicitada <= 0:
            raise HttpError(400, "area_solicitada debe ser mayor a 0")
        # Mapeo a DTO
        domain_data = HabilitacionUrbanaPrimeraRevisionData(...)
        # Delegación
        return self.flujo.ejecutar_primera_revision(usuario_id, domain_data)
```

### 4.3. Flujo — `domain/services/flujos/liquidacion_especifico/`

**Responsabilidades (ÚNICO lugar con `@transaction.atomic`)**:
- Coordinar creación de todos los registros DB en orden:
  1. Entidad (upsert por documento)
  2. Proyecto
  3. Tarifa (lookup para FK snapshot)
  4. `LiquidacionGeneral` (con totales)
  5. `LiquidacionTipo` (M2 o Visitas, con valores snapshot)
  6. `LiquidacionEspecifica` (HU, IO, etc., identidad)
- Mapear ORM objects → Domain Result (Pydantic puro)

**PROHIBIDO en Flujo**:
- Validación (confía en Orchestrator)
- Cálculos matemáticos (delega al Core)

```python
class LiquidacionHabilitacionUrbanaFlujo:
    @transaction.atomic()
    def _ejecutar_primera_revision_sync(self, usuario_id, data):
        entidad = self.general_core.create_entidad(...)
        proyecto = self.general_core.create_proyecto(...)
        cotizacion = self.m2_core.calcular_cotizacion_m2(...)
        liquidacion_general = self.general_core.create_liquidacion_general(...)
        liquidacion_m2 = self.m2_core.create_liquidacion_por_metro_cuadrado(...)
        liquidacion_especifica = LiquidacionHabilitacionUrbana.objects.create(
            liquidacion=liquidacion_general
        )
        return HabilitacionUrbanaPrimeraRevisionResult(...)
```

### 4.4. Core — `domain/services/core/`

**Responsabilidades (puro ORM + matemática)**:
- Queries ORM puras (`.objects.get()`, `.filter()`, `.create()`)
- Cálculos aritméticos simples (sin reglas de negocio)
- Creación de registros

**PROHIBIDO en Core**:
- `HttpError` (no sabe de HTTP)
- `@transaction.atomic` (lo maneja el Flujo)
- Lógica de validación o reglas de negocio
- Importación de schemas de Presentation

```python
class LiquidacionPorMetroCuadradoCoreService:
    def calcular_cotizacion_m2(self, tipo_liquidacion, area_solicitada, tarifa_m2_id):
        tarifa = TarifaPorMetroCuadradoModel.objects.get(id=tarifa_m2_id)
        monto_bruto = area_solicitada * tarifa.costo_por_m2
        # Aplica clamping derecho_minimo/maximo si es necesario
        return CotizacionM2Result(...)
```

### 4.5. Presenter — `presentation/presenters/liquidacion_especifico/`

**Responsabilidades (mapeo puro)**:
- Convertir Domain Result → Presentation Schema
- `@staticmethod` obligatorio (sin estado)

**PROHIBIDO en Presenter**:
- Lógica de negocio
- Acceso a ORM
- `@staticmethod` es la única forma permitida

```python
class LiquidacionHabilitacionUrbanaPresenter:
    @staticmethod
    def present_primera_revision(domain_result):
        return LiquidacionHabilitacionUrbanaOutput(
            liquidacion_general=...,
            liquidacion_especifica=...,  # identidad (id + numero)
            liquidacion_tipo=...         # cálculo
        )
```

---

## 5. Regla de Snapshot (Inmutabilidad)

Cuando se crea una liquidación, se guarda:

1. **FK a la tarifa** (referencia, para integridad referencial)
2. **Valores numéricos snapshot** (lo que realmente se usó en el cálculo)

### 5.1. Ejemplo M2 (`LiquidacionPorMetroCuadrado`)

```python
class LiquidacionPorMetroCuadrado(BaseModel):
    liquidacion = ForeignKey(LiquidacionGeneral)
    # FK snapshot (referencia)
    tarifa_aplicada = ForeignKey("TarifaPorMetroCuadrado", on_delete=PROTECT)
    derecho_aplicado = ForeignKey("DerechoPorMetroCuadrado", on_delete=PROTECT)
    # Valores snapshot (inmutables)
    area_m2 = DecimalField(...)
    costo_por_m2 = DecimalField(...)    # ← copiado de la tarifa al momento de crear
    derecho_minimo = DecimalField(...)  # ← copiado del derecho al momento de crear
    derecho_maximo = DecimalField(...)
```

**Por qué**: Cambios futuros en la tarifa NO alteran liquidaciones pasadas (auditabilidad + inmutabilidad).

---

## 6. Patrón de Polimorfismo (Extensibilidad)

### 6.1. Regla de Oro: **CREAR, no modificar**

Para agregar un nuevo tipo de liquidación, crear archivos en carpetas NUEVAS. **NUNCA modificar** los archivos existentes de HU/IO.

### 6.2. Archivos a CREAR por cada nuevo tipo

```
backend/modules/liquidaciones/
├── domain/
│   ├── models/liquidacion/liquidacion_especifico/
│   │   └── liquidacion_<tipo>.py                    # Modelo identidad (hereda AutoNumeroModel)
│   ├── schemas/liquidacion_especifico/
│   │   └── <tipo>_primera_revision_data.py          # DTO de dominio
│   ├── results/liquidacion_especifico/
│   │   └── <tipo>_primera_revision_result.py        # Result de dominio
│   └── services/
│       ├── flujos/liquidacion_especifico/
│       │   └── liquidacion_<tipo>_flujo.py          # Flujo @transaction.atomic
│       └── orchestrators/liquidacion_especifico/
│           └── liquidacion_<tipo>_orchestrator.py   # Validación
├── presentation/
│   ├── schemas/liquidacion_especifico/
│   │   └── liquidacion_<tipo>_schemas.py            # Schemas Input/Output
│   ├── presenters/liquidacion_especifico/
│   │   └── liquidacion_<tipo>_presenter.py          # Presenter @staticmethod
│   └── controllers/liquidacion_especifico/
│       └── liquidacion_<tipo>_controller.py         # HTTP entry point
```

### 6.3. Archivos a REUTILIZAR (NUNCA modificar)

- `domain/services/core/liquidacion_general/*` (Entidad, Proyecto, LiquidacionGeneral)
- `domain/services/core/liquidacion_tipo/*` (M2, Visitas, Porcentaje core services)
- `presentation/schemas/liquidacion_general/*`
- `presentation/schemas/liquidacion_tipo/*` (M2, Visitas, Porcentaje schemas)
- `core_application/models.py` (VigenciaModel, AutoNumeroModel)

### 6.4. Ejemplo: Agregar Mecánica de Suelos (idéntico a HU)

Mecánica de Suelos usa el mismo motor M2 que HU. Solo cambia el `TipoLiquidacion` y la tabla de identidad:

1. Crear `domain/models/liquidacion/liquidacion_especifico/liquidacion_mecanica_suelos.py`:
   ```python
   class LiquidacionMecanicaSuelos(BaseModel, AutoNumeroModel):
       liquidacion = OneToOneField(LiquidacionGeneral, on_delete=CASCADE)
       # numero viene de AutoNumeroModel
   ```

2. Crear los 7 archivos restantes (schema, DTO, Result, flujo, orchestrator, presenter, controller) copiando la estructura de HU y reemplazando:
   - `HabilitacionUrbana` → `MecanicaSuelos`
   - `HABILITACION_URBANA` → `MECANICA_SUELOS` (en `TipoLiquidacion` enum)

3. Registrar el modelo en `liquidaciones/models/liquidacion_especifico/__init__.py`.

4. Generar migración: `uv run python manage.py makemigrations --settings=config.settings.development`.

5. **Listo**. El endpoint queda disponible sin tocar HU.

---

## 7. Configuración de Tests

### 7.1. Stack de Testing

- **Framework**: pytest + pytest-django
- **Cliente HTTP**: `ninja.testing.TestClient` (NO `AsyncClient`)
- **JWT**: `ninja_jwt.tokens.AccessToken.for_user(user)`
- **DB**: `@pytest.mark.django_db` (sin `transaction=True`)

### 7.2. Configuración JWT en `config/settings/test.py`

```python
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

### 7.3. Patrón de Test (referencia)

Copiar patrón de `C:\Users\Usuario\Desktop\my-apps\centro-de-esparcimiento\ninja\tests\conftest.py`.

```python
import pytest
from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken

@pytest.mark.django_db
def test_crear_primera_revision_hu():
    user = UserFactory()
    token = AccessToken.for_user(user)
    client = TestClient(liquidacion_api)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/liquidaciones/habilitacion-urbana/nueva-liquidacion/primera-revision",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200
```

---

## 8. Endpoints Actuales (Referencia)

| Tipo | Endpoint |
|------|----------|
| HU | `POST /api/liquidaciones/habilitacion-urbana/nueva-liquidacion/primera-revision` |
| HU | `POST /api/liquidaciones/habilitacion-urbana/cotizar` |
| HU | `GET /api/liquidaciones/habilitacion-urbana/tarifas/vigentes` |
| IO | `POST /api/liquidaciones/inspeccion-obra/crear-primera-revision` |

---

## 9. Convenciones de Imports

**SIEMPRE absolutos**:
```python
from modules.liquidaciones.domain.services.core.liquidacion_general import LiquidacionGeneralCoreService
from modules.liquidaciones.presentation.schemas.liquidacion_especifico.liquidacion_habilitacion_urbana_schemas import LiquidacionHabilitacionUrbanaInput
```

**NUNCA relativos con puntos**:
```python
# ❌ PROHIBIDO
from ..core import LiquidacionGeneralCoreService
from ...schemas import LiquidacionHabilitacionUrbanaInput
```

---

## 10. Reglas Críticas (Anti-Patterns)

| ❌ NO hacer | ✅ Hacer correctamente |
|-------------|----------------------|
| Poner `if`/`for` en Controller | Controller solo delega |
| Usar `async def` en Controller/Orchestrator | `sync def` en todas las capas |
| Poner `@transaction.atomic` en Controller/Orchestrator/Core | Solo en Flujo |
| Lanzar `HttpError` desde Core | Core solo retorna Result, Orchestrator lanza HttpError |
| Acceder a ORM directo en Orchestrator (excepto lecturas simples) | Orchestrator valida y mapea, Core hace ORM |
| Hacer cálculos en Orchestrator/Flujo | Core hace la matemática |
| Usar `import` relativo con `..` | Siempre absoluto con `from modules.xxx...` |
| Devolver `dict` desde Presenter | Devolver Schema tipado |
| Usar `uuid.uuid4()` en Presenter para IDs | Usar el ID real del Result |
| Llamar `liquidacion.save()` sin asignar FKs IGV/UIT primero | Asignar FKs antes del save |

---

## 11. Próximos Tipos a Implementar

| Tipo | Motor | Estado |
|------|-------|--------|
| Habilitación Urbana (HU) | M2 | ✅ Implementado |
| Inspección de Obra (IO) | Visitas | ✅ Implementado |
| Mecánica de Suelos | M2 | 🔲 Pendiente (copiar HU, cambiar TipoLiquidacion) |
| Edificaciones (PO) | Porcentaje | 🔲 Pendiente |
| Impacto Vial | M2 | 🔲 Pendiente |
| Taludes | M2 | 🔲 Pendiente |
| Reintegro | TBD | 🔲 Pendiente |

---

## 12. Glosario

| Término | Definición |
|---------|-----------|
| **AutoNumeroModel** | Abstract model en `core_application.models` que autoincrementa `numero` en `save()` |
| **VigenciaModel** | Abstract model con `periodo_inicio`/`periodo_fin` y manager `.vigentes()` |
| **Snapshot** | Copia inmutable del valor de la tarifa al momento de crear la liquidación |
| **Clamping** | Forzar un valor numérico a un rango [min, max] (ej: derecho_minimo, derecho_maximo) |
| **Wrapper** | Schema Pydantic que agrupa un conjunto de campos relacionados |
| **FK plana** | Campo `xxx_id: uuid.UUID` directamente en el schema (no anidado) |
| **FK anidada** | Campo `xxx: { id: uuid.UUID }` cuando solo se necesita la referencia |
