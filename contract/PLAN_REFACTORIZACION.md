# Plan de Refactorización Arquitectónica (Guía Estricta de Código)

Este documento sirve como la **única fuente de verdad** para la arquitectura backend. Define explícitamente qué puede hacer y qué no puede hacer cada capa del sistema, con ejemplos de código reales.

---

## 1. Reglas Absolutas y Anti-Patrones

### A. Los Controladores son "Sagrados" (Cero Lógica)
El controlador solo hace 3 cosas: Parsear la entrada, llamar al Orquestador, y retornar el éxito formateado por un Presenter.
*   **PROHIBIDO:** Usar `if`, `for`, o variables de estado.
*   **PROHIBIDO:** Tocar el ORM (`Model.objects.all()`).
*   **PROHIBIDO:** Retornar errores manuales (`return error_response(...)`).

#### ❌ EL ANTI-PATRÓN (Lo que NUNCA debe existir)
```python
@route.get("/{bungalow_id}/imagenes", response={200: ApiResponse[list[BungalowImagenOut]]})
async def listar_imagenes(self, bungalow_id: str, request):
    # ❌ 1. ORM directo en el controlador
    bungalow = await sync_to_async(self._service.get_by_id)(bungalow_id)
    
    # ❌ 2. Lógica de negocio (IF)
    if not bungalow:
        # ❌ 3. Manejo manual de errores
        return error_response(code="BUNGALOW_NOT_FOUND", status=404)
        
    # ❌ 4. Más ORM directo en el controlador
    imagenes = await sync_to_async(lambda: list(bungalow.imagenes.all()))()
    return success_response(...)
```

#### ✅ LA FORMA CORRECTA
```python
# modulos/alojamiento/presentation/controllers/bungalow_controller.py
from modulos.alojamiento.domain.services.orchestrators.bungalow_orchestrator import BungalowOrchestrator

@route.get("/{bungalow_id}/imagenes", response={200: ApiResponse[list[BungalowImagenOut]]})
async def listar_imagenes(self, bungalow_id: str, request):
    # ✅ 1. Solo delegación pura. Cero ifs, cero error_responses manuales.
    imagenes = await self.bungalow_orchestrator.listar_imagenes_proceso(bungalow_id)
    
    # ✅ 2. Formateo y retorno de éxito exclusivo.
    imagenes_out = [BungalowPresenter._map_imagen(i) for i in imagenes]
    return success_response(imagenes_out)
```

---

### B. El Manejo de Excepciones Globales
Si el controlador no puede retornar errores, ¿quién lo hace? **El Orquestador o el Flujo/Core mediante `raise`.**
Tu archivo `backend/core/exceptions.py` captura `HttpError` automáticamente.

#### ✅ EN EL ORQUESTADOR O CORE:
```python
from ninja.errors import HttpError

class BungalowOrchestrator:
    async def listar_imagenes_proceso(self, bungalow_id: str):
        bungalow = await sync_to_async(self.core.get_by_id)(bungalow_id)
        
        # ✅ Aquí va la validación. Se LANZA el error, no se retorna.
        if not bungalow:
            raise HttpError(404, f"Bungalow '{bungalow_id}' no encontrado")
            
        return await sync_to_async(self.core.get_imagenes)(bungalow)
```

---

### C. Tipado Estricto de Schemas (`BaseSchema`)
Todo esquema, ya sea de entrada (`In`) o de respuesta (`Out`), debe heredar obligatoriamente de `BaseSchema`.
*   **Propósito:** Evitar guardar/retornar `null` y `""` de forma inconsistente en las mismas columnas.

#### ✅ CORRECTO
```python
from core.types import BaseSchema

class FamiliarIn(BaseSchema): # ✅ Hereda de tu clase estandarizada
    dni: str
    nombres: str
```

---

### D. Cero Returns Gigantes (Asignación en Orquestadores)
En los Orquestadores, cuando llamas a un flujo, **no** puedes hacer un return directo masivo.

#### ✅ CORRECTO
```python
async def vincular_familiar_proceso(self, auth_id, payload):
    flujo_seguro = sync_to_async(self.flujo.ejecutar_vinculacion_familiar, thread_sensitive=True)
    
    # ✅ Se asigna a una variable para claridad y debug
    response = await flujo_seguro(auth_id, payload)
    
    return response
```

---

### E. Imports Absolutos vs Imports Frágiles
Nunca usar `...` para escalar en carpetas. Es frágil y rompe herramientas de refactorización.

#### ✅ CORRECTO
```python
from modulos.identidad.domain.services.orchestrators.contacto_orchestrator import ContactoOrchestrator
from modulos.identidad.domain.schemas.persona_schemas import PersonaCreateData
```

---

## 2. Los 3 Patrones Únicos de Controladores (Regla de Firmas)

La firma de un controlador **solo** puede aceptar `self`, `request`, el `payload` (o `data`/`files`), y parámetros de ruta/query. Cualquier otra variable suelta en la firma es un error arquitectónico. Solo existen 3 formas de recibir datos:

### Patrón 1: Dual (JSON o FormData)
Se usa cuando el endpoint soporta tanto JSON puro como FormData (cuando las imágenes son opcionales o vienen en lote mixto).
```python
@route.patch("/{bungalow_id}/imagenes", response={200: ApiResponse[BungalowEnrichedOut]})
async def batch_imagenes_patch(self, bungalow_id: str, request):
    # Parseo interno manejado por tu utilidad especial
    payload = parse_request_payload(request, BungalowImagenBatchIn)
    # ... delegación al orquestador
```

### Patrón 2: FormData Estricto (Archivos obligatorios)
Se usa cuando el endpoint SIEMPRE va a recibir archivos (ej. foto_frontal).
```python
@route.post("/familiar", response={200: ApiResponse[ContactoOut]})
async def crear_familiar(self, request, data: Form[DataForm], files: File[list[UploadedFile]]):
    # Parseo manual usando parse_form_json
    payload = parse_form_json(data.data, files, FamiliarIn)
    
    # Es totalmente VÁLIDO mapear el payload a DTOs de dominio aquí antes del orquestador
    data_persona = PersonaCreateData(dni=payload.dni, nombres=payload.nombres)
    data_contacto = ContactoCreateData(tipo_vinculo=payload.tipo_vinculo)
    
    result = await self.contacto_orchestrator.crear_familiar_proceso(request.auth.id, data_persona, data_contacto)
    return success_response(ContactoPresenter.present(result))
```

### Patrón 3: JSON Estricto (API REST Clásica)
Se usa para endpoints puramente de texto/JSON (sin archivos involucrados).
```python
@route.post("/vincular-familiar", response={200: ApiResponse[ContactoOut]})
async def vincular_familiar(self, request, payload: VincularFamiliarIn):
    # Parseo automático de Pydantic por Ninja a través del parámetro tipado `payload`
    data_contacto = ContactoCreateData(tipo_vinculo=payload.tipo_vinculo, es_familiar=True)
    
    result = await self.contacto_orchestrator.vinvular_familiar_proceso(request.auth.id, payload.dni, data_contacto)
    return success_response(ContactoPresenter.present(result))
```

---

## 3. Presenters, Helpers y Results (Reglas Complementarias)

### A. Regla del Presenter
El Presenter tiene una sola responsabilidad: **Mapear datos crudos (Modelos o Results) hacia `Schemas Out`**.
*   Solo debe tener `@staticmethod` o `@classmethod`.
*   **PROHIBIDO:** Llamar a la base de datos (nada de `objects.get()`).
*   **Permitido:** Lógica mínima de formateo (ej. concatenar nombres, transformar fechas, resolver booleanos `is_active = estado == 'A'`).

### B. Regla de Helpers
Los Helpers son funciones de utilidad pura que no pertenecen al negocio directamente (ej. generar un hash, verificar un código).
*   **Regla:** Deben nombrarse empezando con un guion bajo `_` para denotar que son utilerías internas (ej. `_generar_token()`, `_calcular_edad()`).

### C. Schemas API vs Results Internos
Existe una diferencia vital entre la carpeta `schemas/` y `results/`:
1.  **`domain/schemas/`:** Son los contratos oficiales de tu API. Lo que entra (`In`) y lo que sale (`Out`). **Heredan de `BaseSchema`.**
2.  **`domain/results/`:** Son DTOs internos (Data Transfer Objects). Se usan cuando el Orquestador necesita retornar información compleja al Controlador que no es simplemente un modelo de Django (ej. `MeResult` agrupa datos de Persona, Configuración y Perfiles en un solo objeto). **Heredan de `BaseModel` puro de Pydantic.** El Presenter toma estos `Results` y los convierte en `Schemas Out`.

---

## 4. Mapa Exacto de las 4 Capas (Ejemplo: Identidad)

1. **Controller (`presentation/controllers/auth_controller.py`)**
   - Importa el Orquestador absoluto.
   - Aplica 1 de los 3 patrones de Parseo.
   - Retorna `success_response`.
2. **Orchestrator (`domain/services/orchestrators/auth_orchestrator.py`)**
   - Contiene validaciones complejas.
   - Usa `sync_to_async` y asigna a variables.
   - Lanza `HttpError` si algo es inválido.
3. **Flujo (`domain/services/flujos/auth_flujo.py`)**
   - Agrupa múltiples interacciones de Core.
   - Único lugar donde existe el decorador `@transaction.atomic`.
4. **Core (`domain/services/core/persona_core.py`)**
   - Transaccionalidad pura del ORM de Django (`get`, `create`, `filter`).
   - Cero lógica de negocio condicional.

---

## 5. Historial de Implementaciones遵守 los Patrones

### ✅ Endpoint Batch Delegados — Liquidaciones
- **Endpoint:** `PATCH /liquidaciones/{liquidacion_id}/delegados`
- **Patrón aplicado:** Controlador thin → Orchestrator (validaciones) → Flujo (`transaction.atomic` + `related_batch`) → Core ORM puro
- **Estado:** ✅ Implementado y verificado (197 tests passed, 0 skipped)
- **Fecha:** 2026-07-03

(End of file - total 207 lines)
