# PLAN: Cotización y Compra — UX de Inscripción FEST 2026

> **Proyecto:** Salesianos FEST  
> **Artifact:** `sdd/salesianos-fest-purchase-quotation-contract/explore`  
> **Fecha:** 2026-10-18  
> **Modo:** Exploración read-only + plan de implementación  
> **Idioma:** Español (neutro/profesional)  

---

## RESUMEN EJECUTIVO

| Área | Estado | Severidad |
|------|--------|----------|
| Mínimo de compra con origen backend (`FIJO_PAQUETE` vs `SEGUN_DISCIPLINA`) | 🟡 PARCIAL — `modo_disciplinas`没错 pero la distinción comercial no está explícita en el contrato API | HIGH |
| Presenter de paquete/cotización expone mínimos y reglas | ❌ NO EXISTE — no hay endpoint de cotización previo al compromiso | CRITICAL |
| UI de inscripción con tarjeta de cotización y controles +/- | ❌ NO EXISTE — el wizard no tiene campo cantidad editable | CRITICAL |
| Mutación final revalida precio/mínimo servidor | ✅ YA EXISTE — `CrearCompraFlujo` valida `cantidad >= minimo_compra_inicial` | — |
| Diseño para ofertas de equipo e independiente | 🟡 PARCIAL — el modelo soporta ambos pero la UX no los diferencia claramente | MEDIUM |

---

## 1. MODELO DE DATOS: ESTADO ACTUAL VS OBJETIVO

### 1.1 Modelo Actual (Explícito en Código)

#### Backend — Paquete (Fuente: `paquete.py`)

```python
class Paquete(BaseModel):
    evento: FK(Evento)
    nombre: str
    tipo: PACK | DISCIPLINA
    modo_disciplinas: FIJO | ELEGIBLE        # CANONICAL — no inferir
    cantidad_disciplinas: int                 # slots de disciplina (1, 2, 3)
    minimo_compra_inicial: int               # mínimo comercial en personas
    activo: bool
```

#### Backend — Compra (Fuente: `compra.py`)

```python
class Compra(BaseModel):
    inscripcion: FK(Inscripcion)
    orden_pago: OneToOne(OrdenPago)
    tipo: INICIAL | AMPLIACION
    cantidad: int                             # cupos comprados
    precio_unitario: Decimal                  # snapshot congelado
    total: Decimal                            # snapshot = cantidad * precio_unitario
    estado: PENDIENTE | PAGADA | CANCELADA
```

#### Backend — Disciplina (Fuente: `disciplina.py`)

```python
class Disciplina(BaseModel):
    sigla: str (única)
    nombre: str
    modalidad: M | F | X
    min_jugadores: int                        # mínimo deportivo por equipo (5-10)
    max_jugadores: int                        # máximo deportivo por equipo
```

### 1.2 Catálogo de Datos Sembrados (Fuente: `seed_catalogo_fest.py`)

| Paquete | Tipo | `modo_disciplinas` | `cantidad_disciplinas` | `minimo_compra_inicial` | Disciplinas Linkadas | Precio Preventa | Precio Regular |
|---------|------|-------------------|------------------------|------------------------|---------------------|-----------------|---------------|
| Reencuentro + Fiesta | PACK | **ELEGIBLE** | 1 | **10** | F7F, VOL, BAS | S/40 | S/50 |
| Pichanga + Fiesta | PACK | **FIJO** | 1 | **10** | F7M | S/45 | S/55 |
| Dúo + Fiesta Box | PACK | **ELEGIBLE** | 2 | **15** | VOL, BAS | S/60 | S/70 |
| Trío + Fiesta Box | PACK | **ELEGIBLE** | 3 | **20** | F7M, VOL, BAS | S/60 | S/70 |
| Fútbol 7 Masculino | DISCIPLINA | **FIJO** | 1 | **7** | F7M | S/40 | S/50 |
| Fútbol 7 Femenino | DISCIPLINA | **FIJO** | 1 | **7** | F7F | S/40 | S/50 |
| Vóley Mixto | DISCIPLINA | **FIJO** | 1 | **6** | VOL | S/40 | S/50 |
| Básquet Masculino | DISCIPLINA | **FIJO** | 1 | **5** | BAS | S/40 | S/50 |

### 1.3 Modelo Objetivo — Explicitación de Mínimo

**Problema identificado:** El campo `minimo_compra_inicial` actualmente mezcla dos conceptos:
1. **Mínimo comercial** (FIJO_PAQUETE): la cantidad mínima de cupos que se deben comprar por paquete — viene del catálogo (`paquete.minimo_compra_inicial`)
2. **Mínimo deportivo** (SEGUN_DISCIPLINA): la cantidad mínima de jugadores por equipo según la disciplina — viene de `disciplina.min_jugadores`

**这两种 origins no están diferenciados en el API contrato.**

#### Cambio propuesto en `PaqueteListOut` / `PaqueteDetailOut`:

```python
class PaqueteListOut(BaseSchema):
    # ... campos existentes ...
    
    # NUEVOS campos explícitos para origen del mínimo
    minimo_origen: Literal["FIJO_PAQUETE", "SEGUN_DISCIPLINA"]  # CANONICAL
    minimo_cantidad: int  # Valor numérico del mínimo
    # Campo anterior minimo_compra_inicial se mantiene por compatibilidad 
    # pero su semántica ahora es explícita via minimo_origen
```

**Regla comercial confirmada por especificación y catálogo oficial:**
- Todo paquete sembrado expone su mínimo comercial explícito desde `Paquete.minimo_compra_inicial`.
- Las ofertas por disciplina tienen un mínimo comercial que coincide con `Disciplina.min_jugadores` (Fútbol 7, Vóley 6, Básquet 5), pero la cotización sigue leyendo el valor del paquete.
- Reencuentro, Pichanga, Dúo y Trío tienen mínimos comerciales totales de 10, 10, 15 y 20 respectivamente, sin importar cuántas disciplinas se elijan.
- `Disciplina.min_jugadores` sirve para reglas deportivas de roster, no para recalcular ni sumar el mínimo comercial de la cotización.

---

## 2. CONTRATO API RECOMENDADO

### 2.1 Rutas API Existentes vs Nuevas

| Ruta | Método | Props | Estado | Notas |
|------|--------|-------|--------|-------|
| `/api/catalogo/paquetes/` | GET | — | ✅ Existe | Lista paquetes con `modo_disciplinas`, `minimo_compra_inicial` |
| `/api/catalogo/paquetes/{id}/` | GET | — | ✅ Existe | Detalle con precios, beneficios |
| `POST /api/inscripciones/completa/` | POST | `cantidad: int` | ✅ Existe | Creación atómica inscripcion + compra + equipos |
| `POST /api/compras/` | POST | `inscripcion_id, tipo, cantidad` | ✅ Existe | Crear compra standalone |
| `**POST /api/cotizaciones/**` | POST | `paquete_id, cantidad` | ❌ NUEVO | Cotizar sin crear |
| `**GET /api/cotizaciones/{cotizacion_id}/**` | GET | — | ❌ NUEVO | Revalidar cotización |

### 2.2 Schema Propuesto: CotizacionRequest

```python
class CotizacionRequest(BaseSchema):
    paquete_id: str
    cantidad: int = Field(..., ge=1, description="Cupos a cotizar")
    disciplina_id: Optional[str] = Field(
        None, 
        description="Para paquetes ELEGIBLE: disciplina seleccionada (req. si modo=ELEGIBLE)"
    )
```

### 2.3 Schema Propuesto: CotizacionResponse

```python
class CotizacionResponse(BaseSchema):
    cotizacion_id: str          # UUID para referencia
    paquete_id: str
    paquete_nombre: str
    modo_disciplinas: str       # FIJO | ELEGIBLE
    minimo_origen: str          # FIJO_PAQUETE | SEGUN_DISCIPLINA
    minimo_cantidad: int        # Valor mínimo requerido
    cantidad_cotizada: int       # Cantidad solicitada
    cantidad_disciplinas: int    # Slots de disciplina del paquete
    precio_unitario: float       # Precio vigente (desde PaquetePrecio activo)
    precio_regular: float        # Precio regular (referencia)
    precio_preventa: Optional[float]
    total: float                # cantidad_cotizada * precio_unitario
    validez_hasta: datetime     # Timestamp de expiración de cotización
    version: int                # Contador de versión para detección de cambio
    estado: Literal["ACTIVA", "EXPIRADA", "REEMPLAZADA"]
```

### 2.4 Presenter JSON — Ejemplo de Respuesta

```json
{
  "success": true,
  "data": {
    "cotizacion_id": "550e8400-e29b-41d4-a716-446655440000",
    "paquete_id": "123e4567-e89b-12d3-a456-426614174000",
    "paquete_nombre": "Reencuentro + Fiesta",
    "modo_disciplinas": "ELEGIBLE",
    "minimo_origen": "FIJO_PAQUETE",
    "minimo_cantidad": 10,
    "cantidad_cotizada": 12,
    "cantidad_disciplinas": 1,
    "precio_unitario": 40.00,
    "precio_regular": 50.00,
    "precio_preventa": 40.00,
    "total": 480.00,
    "validez_hasta": "2026-10-19T23:59:59Z",
    "version": 1,
    "estado": "ACTIVA"
  },
  "message": "Cotización generada correctamente."
}
```

### 2.5 Tablas Escritas por la Cotización

La cotización **NO escribe en la base de datos** — es un cálculo stateless derivado del catálogo vigente. La única entidad que persiste es la `Compra` (con snapshot de precio).

```
Tablas leídas (cotización stateless):
  - Paquete (minimo_compra_inicial, modo_disciplinas, cantidad_disciplinas)
  - PaquetePrecio (precio_unitario vigente por etapa)
  - Disciplina (min_jugadores para SEGUN_DISCIPLINA)

Tablas escritas (solo al confirmar compra):
  - Compra (snapshot precio_unitario, total, cantidad, estado=PENDIENTE)
  - OrdenPago (monto_total, estado=PENDIENTE)
```

---

## 3. CICLO DE VIDA DE LA COTIZACIÓN

### 3.1 Estados de la Cotización

```
┌─────────────┐
│   ACTIVA    │ ← Cotización recién generada (validez 24h)
└──────┬──────┘
       │ (expiración o nueva cotización)
       ▼
┌─────────────┐
│  EXPIRADA   │ ← Pasó validez_hasta sin confirmar
└──────┬──────┘
       │ (nueva cotización misma cantidad)
       ▼
┌─────────────┐
│ REEMPLAZADA │ ← Reemplazada por versión más nueva
└─────────────┘
```

### 3.2 Cache de Cotización en Frontend (Form State)

```
FormState (Zustand / React Hook Form):
{
  paquete_id: string,
  cantidad: number,              // Editable por usuario
  cotizacion: CotizacionResponse | null,
  cotizacion_fetched_at: Date | null,
  is_cotizacion_valid: boolean
}
```

**Reglas de cache:**
- Cuando `cantidad` cambia → invalidar `cotizacion` (marcar `is_cotizacion_valid: false`)
- Cuando usuario abandona el campo cantidad por >500ms → hacer debounced call a `POST /api/cotizaciones/`
- Si la cotización está expirada (`validez_hasta < now`) → mostrar error "La cotización expiró. Genera una nueva."
- Si la cotización está reemplazada (nueva versión disponible) → mostrar warning "El precio cambió. Revisa la nueva cotización."

### 3.3 Confirmación Final — Server Revalidation

El flujo de confirmación (`POST /api/inscripciones/completa/` o `POST /api/compras/`) **SIEMPRE revalida**:

1. `cantidad >= minimo_compra_inicial` del paquete vigente
2. `precio_unitario` vigente no cambió desde la cotización (mediante `version` o re-fetch)
3. Si cambió → `409 Conflict: PRECIO_CAMBIO` con la nueva cotización como payload

---

## 4. INTERACCIÓN FIJO/ELEGIBLE

### 4.1 Paquetes FIJO

- `modo_disciplinas = FIJO`: las disciplinas están predefinidas en `PaqueteDisciplina`
- El mínimo `minimo_cantidad` viene directamente de `paquete.minimo_compra_inicial`
- No se requiere `disciplina_id` en la cotización
- Ejemplo: "Pichanga + Fiesta" → FIJO_PAQUETE, min=10, disciplinas=[F7M]

### 4.2 Paquetes ELEGIBLE

- `modo_disciplinas = ELEGIBLE`: el usuario selecciona de las disciplinas linkadas
- El mínimo `minimo_cantidad` viene del mínimo comercial explícito del paquete; elegir disciplinas no lo modifica.
- Las disciplinas seleccionadas se validan para crear equipos, mientras el mínimo deportivo se valida sobre el roster cuando corresponda.
- Ejemplo: "Dúo + Fiesta Box" → ELEGIBLE, disciplinas=[VOL, BAS], mínimo comercial total=15.

### 4.3 Lógica de Cotización

```python
def cotizar_paquete(paquete_id: str, cantidad: int) -> Cotizacion:
    paquete = Paquete.objects.get(id=paquete_id)
    minimo = paquete.minimo_compra_inicial
    if cantidad < minimo:
        raise CantidadInsuficienteError(minimo=minimo, received=cantidad)
    return Cotizacion(cantidad=cantidad, precio_unitario=precio_vigente(paquete), minimo=minimo)
```

---

## 5. ESTADOS UX, ERRORES Y LOADING

### 5.1 Estados UI — Tarjeta de Cotización

```
┌─────────────────────────────────────────────────────────────┐
│  📦 Reencuentro + Fiesta                    [ELEGIBLE]      │
│  ─────────────────────────────────────────────────────────  │
│  Precio por persona: S/40.00                               │
│                                                             │
│  Cantidad de cupos:                                        │
│  ┌───┐    ┌─────────┐    ┌───┐                          │
│  │ - │    │   12    │    │ + │                          │
│  └───┘    └─────────┘    └───┘                          │
│  Mínimo: 10 personas · Máximo: —                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 💡 "La cotización es válida por 24 horas"           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Subtotal cotizado: S/480.00                              │
│  ─────────────────────────────────────────────────────────  │
│  [Cotizar de nuevo]  [Continuar con esta cotización →]   │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Estados de Error

| Condición | UI | Mensaje |
|-----------|----|---------|
| `cantidad < minimo_cantidad` | Input en rojo, botón deshabilitado | `La cantidad mínima es {minimo_cantidad} para este paquete` |
| Cotización expirada | Banner warning amarillo | `La cotización expiró. Genera una nueva.` |
| Precio cambió desde cotización | Banner warning amarillo + mostrar nueva | `El precio cambió de S/X a S/Y. Revisa la nueva cotización.` |
| Error de red al cotizar | Toast error | `No se pudo cotizar. Intenta de nuevo.` |
| Paquete no encontrado | 404 page | — |
| Error de servidor | Toast error genérico | `Ocurrió un error inesperado.` |

### 5.3 Estados de Loading

| Acción | UI |
|--------|-----|
| Cotización en curso | Spinner en botón "Cotizar" + input deshabilitado |
| Cambio de cantidad (debounce 500ms) | Spinner inline junto al total |
| Confirmando inscripción | Full-screen loader + "Procesando tu inscripción..." |

### 5.4 Accesibilidad

- Input cantidad: `type="number"`, `min={minimo_cantidad}`, `aria-label="Cantidad de cupos"`, `aria-describedby="minimo-ayuda"`
- Botones +/-: `aria-label="Incrementar cantidad"`, `aria-label="Decrementar cantidad"`
- Error: `role="alert"` para errores, `aria-live="polite"` para warnings de precio
- Cotización expirada: `role="warning"` con `aria-label="Cotización expirada"`
- Contraste mínimo 4.5:1 para todo texto crítico (precio, mínimo)

---

## 6. COMPORTAMIENTO EN CONFIRMACIÓN FINAL

### 6.1 Flujo de Confirmación

```
1. Usuario completa wizard → hace clic en "Confirmar inscripción"
2. Si no hay cotización válida → trigger cotizacion automática
3. Mostrar pantalla de confirmación con:
   - Paquete seleccionado
   - Cantidad cotizada
   - Precio unitario vigente
   - Total
   - "Esta cotización es válida hasta {validez_hasta}"
   - "Al confirmar, el precio queda congelado"
4. Usuario hace clic en "Confirmar y proceder al pago"
5. POST /api/inscripciones/completa/
   - Backend revalida cantidad >= minimo
   - Backend revalida precio_unitario vigente
   - Si cambió → 409 Conflict con nueva cotización
   - Si ok → crear Compra + OrdenPago + Equipos (atómico)
6. Redirigir a IzipayModal con orden_pago_id
```

### 6.2 Revalidación Server-Side en Mutación

```python
# En CrearInscripcionCompletaFlujo o CrearCompraFlujo
def _crear_compra_sync(self, data):
    with transaction.atomic():
        # 1. Obtener precio vigente actual
        precio_actual, _ = self.compra_core.obtener_precio_vigente(paquete_id)
        
        # 2. Si el precio cambió desde la cotización (comparar con precio_unitario de cotización)
        if precio_actual != data.precio_unitario_cotizado:
            raise ConflictError(
                code="PRECIO_CAMBIO",
                message=f"El precio cambió de S/{data.precio_unitario_cotizado} a S/{precio_actual}",
                new_precio=precio_actual,
                new_total=data.cantidad * precio_actual
            )
        
        # 3. Validar cantidad mínima
        if data.cantidad < paquete.minimo_compra_inicial:
            raise CantidadInsuficienteError(...)
```

---

## 7. CONCURRENCIA Y SNAPSHOT DE PRECIO

### 7.1 Estrategia de Concurrencia

- **Lectura sucia aceptable**: el precio puede cambiar entre la cotización y la confirmación
- **Detección de conflicto**: se compara `precio_unitario` de la cotización vs el precio vigente al momento de crear la `Compra`
- **Resolución**: si cambió → 409 Conflict con nueva cotización → usuario decide si acepta el nuevo precio o cancela

### 7.2 Snapshot en Compra

La `Compra` ya almacena:
- `precio_unitario`: snapshot del precio vigente al momento de crear la compra
- `total`: snapshot = `cantidad * precio_unitario`

Esto ya está implementado y es correcto.

### 7.3 Validez de Cotización

- Timestamp `validez_hasta` = `now() + 24 horas`
- No se requiere persistencia en BD (stateless computation)
- El frontend es responsable de verificar expiración antes de mostrar el botón de confirmación

---

## 8. LOTES DE IMPLEMENTACIÓN

### 8.1 Lote 1 — Backend: Endpoint de Cotización (CRITICAL)

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `presentation/schemas/cotizacion_schemas.py` | NUEVO — `CotizacionRequest`, `CotizacionResponse` |
| `domain/services/flujos/cotizacion_flujo.py` | NUEVO — lógica de cálculo de mínimo según FIJO/ELEGIBLE |
| `presentation/controllers/cotizacion_controller.py` | NUEVO — `POST /api/cotizaciones/`, `GET /api/cotizaciones/{id}/` |
| `domain/constants.py` | NUEVO — `OrigenMinimoChoices` (FIJO_PAQUETE, SEGUN_DISCIPLINA) |
| `presentation/schemas/catalogo_schemas.py` | Agregar `minimo_origen` a `PaqueteListOut` y `PaqueteDetailOut` |
| `presentation/presenters/catalogo_presenter.py` | Mapear `minimo_origen` desde `Paquete` |
| `config/api.py` | Registrar `CotizacionController` |

**API Contracts:**
```python
# POST /api/cotizaciones/
class CotizacionRequest(BaseSchema):
    paquete_id: str
    cantidad: int = Field(..., ge=1)
    disciplina_id: Optional[str] = None  # Requerido si modo=ELEGIBLE

class CotizacionResponse(BaseSchema):
    cotizacion_id: str
    paquete_id: str
    paquete_nombre: str
    modo_disciplinas: str
    minimo_origen: str
    minimo_cantidad: int
    cantidad_cotizada: int
    cantidad_disciplinas: int
    precio_unitario: float
    precio_regular: float
    precio_preventa: Optional[float]
    total: float
    validez_hasta: datetime
    version: int
    estado: str
```

### 8.2 Lote 2 — Frontend: Tarjeta de Cotización con Controles +/-

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `features/inscripciones/schemas/cotizacion.schema.ts` | NUEVO — Zod schemas para CotizacionRequest/Response |
| `features/inscripciones/services/cotizacion.service.ts` | NUEVO — API calls a `/api/cotizaciones/` |
| `features/inscripciones/components/CotizacionCard.tsx` | NUEVO — Tarjeta de cotización con +/- cantidad |
| `features/inscripciones/hooks/useCotizacion.ts` | NUEVO — hook con debounce y cache de cotización |
| `features/inscripciones/components/InscripcionWizard.tsx` | Integrar CotizacionCard en Step 1, después de SmartPaqueteCardsField |
| `features/inscripciones/components/ConfirmacionStep.tsx` | NUEVO — Pantalla de confirmación final antes de submit |
| `features/inscripciones/hooks/useCreateInscripcionCompleta.ts` | Agregar cotización al payload (opcional, para debugging) |

**Dependencias:**
- Requiere Lote 1 (endpoint de cotización)

### 8.3 Lote 3 — Frontend: Validación y Revalidation en Submit

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `features/inscripciones/views/InscripcionClientShell.tsx` | Agregar paso de confirmación antes de submit |
| `features/inscripciones/hooks/useConfirmarInscripcion.ts` | NUEVO — manejar 409 Conflict con nueva cotización |
| `features/inscripciones/components/PrecioCambiadoModal.tsx` | NUEVO — modal cuando precio cambió entre cotización y confirmación |

### 8.4 Lote 4 — Frontend: Detalle de Inscripción con Compras

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `features/inscripciones/views/InscripcionDetailView.tsx` | Mostrar `CompraDetailCard` con cantidad, precio, total, estado |
| `features/inscripciones/components/CompraDetailCard.tsx` | NUEVO — tarjeta con datos de la compra congelada |

---

## 9. IMPACTO DE MIGRACIÓN

### 9.1 Migración de Datos

**NO se requiere migración de datos** — los cambios son en API contrato y UI, no en esquema de BD.

- `Paquete.minimo_compra_inicial` → se mantiene igual, solo se le da semántica explícita con `minimo_origen`
- `Compra.precio_unitario`, `Compra.total`, `Compra.cantidad` → sin cambios
- Nuevos campos en `PaqueteListOut`/`PaqueteDetailOut` → opcionales, backward compatible

### 9.2 Compatibilidad hacia Atrás

- Endpoint `POST /api/inscripciones/completa/` existente → sin cambios en firma
- `InscripcionCompletaOut` → sin cambios
- Frontend existente → sigue funcionando, pero no tiene la funcionalidad de cotización

### 9.3 Breaking Changes

| Cambio | Tipo | Mitigación |
|--------|------|------------|
| Nuevo campo `minimo_origen` en `PaqueteListOut`/`PaqueteDetailOut` | Aditivo, no breaking | Frontend puede忽略 si no existe |
| Nuevo endpoint `/api/cotizaciones/` | Aditivo | Solo afecta si se usa la nueva UI |
| Nuevo `409 Conflict: PRECIO_CAMBIO` en mutaciones | Nuevo error code | Frontend debe manejar este código |

---

## 10. MATRIZ DE PRUEBAS DE ACEPTACIÓN

### 10.1 Pruebas Backend

| ID | Descripción | Endpoint | Input | Output Esperado |
|----|-------------|----------|-------|----------------|
| T-B01 | Cotizar paquete FIJO | POST /api/cotizaciones/ | paquete_id=Pichanga, cantidad=10 | `minimo_origen=FIJO_PAQUETE`, `total=450` |
| T-B02 | Cotizar paquete ELEGIBLE sin disciplina | POST /api/cotizaciones/ | paquete_id=Reencuentro, cantidad=10 | `400 Bad Request` (disciplina_id requerido) |
| T-B03 | Cotizar paquete ELEGIBLE con disciplina | POST /api/cotizaciones/ | paquete_id=Reencuentro, cantidad=10, disciplina_id=VOL | `minimo_origen=SEGUN_DISCIPLINA`, `total=400` |
| T-B04 | Cotizar cantidad menor al mínimo | POST /api/cotizaciones/ | paquete_id=Pichanga, cantidad=5 | `400 Bad Request` (cantidad < minimo) |
| T-B05 | Cotización con precio expirado (verificar server time) | — | — | El servidor no persiste cotización, es stateless |
| T-B06 | Crear inscripción completa con precio válido | POST /api/inscripciones/completa/ | cantidad=12, precio_unitario=40 | `201 Created`, Compra con `total=480` |
| T-B07 | Crear inscripción con precio cambiado | POST /api/inscripciones/completa/ | cantidad=12, precio_unitario=39 (outdated) | `409 Conflict: PRECIO_CAMBIO` |

### 10.2 Pruebas Frontend

| ID | Descripción | Acción | Resultado Esperado |
|----|-------------|--------|-------------------|
| T-F01 | Selección de paquete muestra mínimo | Click en "Pichanga + Fiesta" | Tarjeta muestra "Mínimo: 10 personas" |
| T-F02 | Input cantidad permite valores >= mínimo | Ingresar 12 | Botón "Cotizar" habilitado |
| T-F03 | Input cantidad rechaza valores < mínimo | Ingresar 5 | Mensaje error, botón deshabilitado |
| T-F04 | Cotización muestra total actualizado | Ingresar 15, esperar 500ms | Muestra "S/675.00" |
| T-F05 | Cotización expirada muestra warning | Esperar 24h o manipular reloj | Banner "Cotización expiró" |
| T-F06 | Confirmación muestra datos de cotización | Click "Continuar" | Muestra: paquete, cantidad, total, preço unitario |
| T-F07 | Confirmación con precio cambiado muestra modal | Simular cambio de precio en backend | Modal "El precio cambió" con nueva cotización |
| T-F08 | Acceso con teclado en input cantidad | Tab + arrows | Incrementa/decrementa cantidad |
| T-F09 | Lector de pantalla anuncia precio y mínimo | Focus en CotizacionCard | Lee: "Precio por persona S/40, mínimo 10 personas, total S/480" |

---

## 11. REGLA CONFIRMADA: MÍNIMO COMERCIAL vs MÍNIMO DEPORTIVO

### 11.1 El Problema

El seed actual muestra:
- Paquetes FIJO (Pichanga, disciplinas individuales): `minimo_compra_inicial = 5-10` (personas)
- Paquetes ELEGIBLE (Reencuentro, Dúo, Trío): `minimo_compra_inicial = 10-20` (personas)

La Disciplina tiene `min_jugadores = 5-10` (jugadores por equipo).

`minimo_compra_inicial` es la cantidad comercial total de cupos que se compra para la inscripción. No es un mínimo por equipo ni una suma calculada desde las disciplinas.

### 11.2 Evidencia del Código Actual

En `CrearInscripcionCompletaFlujo._crear_atomico`:
```python
if data.cantidad < paquete.minimo_compra_inicial:
    raise CantidadInsuficienteError(...)
```

Esto valida `cantidad` contra `minimo_compra_inicial` directamente — no hay distinción por disciplina.

En el frontend, `InscripcionWizard.onSubmit`:
```typescript
const cantidad = selectedPaquete.cantidad_minima_compra ?? 1;
```

El frontend debe mostrar ese mínimo comercial como valor inicial de la cotización, sin reemplazarlo por mínimos deportivos.

### 11.3 Ejemplos Oficiales

- Dúo + Fiesta Box: 15 cupos comerciales totales, con Vóley y Básquet como disciplinas requeridas.
- Trío + Fiesta Box: 20 cupos comerciales totales, con Fútbol 7 Masculino, Vóley y Básquet como disciplinas requeridas.
- Fútbol por disciplina: mínimo comercial 7, igual al mínimo deportivo de Fútbol 7.
- Vóley por disciplina: mínimo comercial 6, igual al mínimo deportivo de Vóley.
- Básquet por disciplina: mínimo comercial 5, igual al mínimo deportivo de Básquet.

---

## 12. ARTIFACTOS LEÍDOS

| Artifact | Ruta | Relevancia |
|---------|------|------------|
| Contract API Wrapper/Presenter | `contract/api-wrapper-presenter-contract.md` | Patrones de arquitectura presenters |
| Seed Catalog | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` | Valores oficiales de mínimo, precios |
| CatalogoPresenter | `backend/modules/salesianos_fest/presentation/presenters/catalogo_presenter.py` | Mapeo actual de presenter |
| Catalogo Schemas | `backend/modules/salesianos_fest/presentation/schemas/catalogo_schemas.py` | Contratos API actuales |
| CompraController | `backend/modules/salesianos_fest/presentation/controllers/compra_controller.py` | Endpoint de compra existente |
| CompraOrchestrator | `backend/modules/salesianos_fest/domain/services/orchestrators/compra_orchestrator.py` | Lógica de creación de compra |
| CrearCompraFlujo | `backend/modules/salesianos_fest/domain/services/flujos/crear_compra_flujo.py` | Validación de mínimo existente |
| CompraService | `backend/modules/salesianos_fest/domain/services/core/compra_service.py` | Snapshot de precio |
| Compra Model | `backend/modules/salesianos_fest/domain/models/compra.py` | Estructura de Compra |
| InscripcionController | `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` | Endpoint creación atómica |
| CrearInscripcionCompletaFlujo | `backend/modules/salesianos_fest/domain/services/flujos/crear_inscripcion_completa_flujo.py` | Flujo atómico actual |
| Paquete Model | `backend/modules/salesianos_fest/domain/models/paquete.py` | Modelo de paquete |
| Paquete Schemas | `backend/modules/salesianos_fest/presentation/schemas/paquete.schema.ts` | Frontend Zod schemas |
| SmartPaqueteCardsField | `frontend/src/features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx` | UI de selección actual |
| InscripcionWizard | `frontend/src/features/inscripciones/components/InscripcionWizard.tsx` | Flujo de wizard actual |
| useCreateInscripcionCompleta | `frontend/src/features/inscripciones/hooks/useCreateInscripcionCompleta.ts` | Hook de creación actual |
| Informe Anterior | `doc_dev/INFORME_INSCRIPCION_EQUIPOS_COMPRA_MINIMA_UX.md` | Gaps previamente identificados |
| Plan Rediseño | `doc_dev/INFORME_SDD_EXPLORACION_REDISENO_SALESIANOS_FEST.md` | Arquitectura general del sistema |

---

*Este plan fue generado mediante SDD Explore read-only. No modifica código fuente. Todos los hallazgos están respaldados por evidencia de archivos reales y código de seed.*
