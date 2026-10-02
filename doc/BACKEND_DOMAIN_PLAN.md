# Plan de Dominio Backend — Salesianos FEST 2026

> **Versión:** 1.6 (Nota: flujo simplificado sin BORRADOR; pago diferido a módulo `pagos` futuro)  
> **Fecha:** 2026-09-19  
> **Proyecto:** `salesianos`  
> **Arquitectura:** Django modular con contrato `contract/django-app-architecture-contract.md`  
> **Objetivo:** Documentar el plan de modelos, reglas y arquitectura de los módulos `usuarios`, `inscripciones` y `pagos` (este último en fase posterior).

---

## 1. Objetivo y Alcance

Este documento establece el plan de dominio para el sistema de inscripciones del Salesianos FEST 2026. Cubre:

- **Módulo `usuarios`:** extiende el `Usuario` existente con la identidad `Persona` vinculada.
- **Módulo `inscripciones`:** registro de equipos, disciplinas, paquetes, participantes y delegados.
- **Módulo `pagos`:** órdenes de pago, transacciones e integración con Izipay (futuro).

No incluye el frontend, ni el mockup existente, ni la migración de datos legacy.

---

## 2. Arquitectura de Capas (Contrato Django CAM)

Cada módulo sigue la estructura del contrato `contract/django-app-architecture-contract.md`:

```
modules/<nombre_modulo>/
├── domain/
│   ├── models/          # Modelos Django (uno por archivo, agrupados por relación semántica)
│   ├── constants.py     # Choices (TextChoices)
│   ├── exceptions.py    # Excepciones de dominio
│   ├── schemas/         # DTOs internos Pydantic (*CreateData, *Result)
│   ├── services/core/   # Lógica sync reutilizable (SIN transaction.atomic propio)
│   ├── services/flujos/ # Flujos async (CON transaction.atomic donde corresponde)
│   ├── services/orchestrators/  # Fachadas async delgadas
│   └── selectors/       # Consultas complejas
├── presentation/
│   ├── schemas/         # Esquemas HTTP Ninja (*In, *Out)
│   ├── controllers/    # Controllers (delgados, solo delegan)
│   ├── presenters/     # Transformadores result → schema HTTP
│   └── routers.py
├── infrastructure/
│   ├── services.py     # Implementaciones de ports (API externa, cache)
│   └── selectors/      # Implementaciones concretas de selectors
├── admin.py
├── di.py               # Wiring injector
├── apps.py
└── tests/
```

**Modelo base:** `core.models.BaseModel` (UUID pk + created_at + updated_at).

**No se usa repository layer** para envolver el ORM — el ORM de Django es la capa de persistencia suficiente.

---

## 3. Reglas de Negocio Confirmadas

| # | Regla | Fuente |
|---|-------|--------|
| R1 | `Usuario` tiene relación `persona_fk` OneToOne requerida con `Persona`. | Decisión aprobada |
| R2 | `Persona` contiene: nombres, apellidos, tipo/número de documento, género, y datos opcionales de aseguradora/seguro. | Decisión aprobada |
| R3 | La aceptación de documentos legales se modela en `PersonaAceptacion` (tabla auditable), no como booleanos `c1/c2/c3`. | Decisión aprobada |
| R4 | `Disciplina.min_jugadores` y `Disciplina.max_jugadores` pueden ser nulos ambos. Null = sin límite en ese extremo. | **Interpretación arquitectónica** — no fue expresamente descrita con esas palabras por el usuario; se infiere del diseño de disciplina flexible por equipo. |
| R5 | La relación paquete-disciplina usa un modelo through explícito `PaqueteDisciplina`. | Decisión aprobada |
| R6 | `Inscripcion` NO tiene campo `codigo` generado por el sistema. | Decisión aprobada |
| R7 | `Inscripcion.cantidad_participantes` NO se almacena; se calcula via queryset/property/count sobre participantes. | Decisión aprobada |
| R8 | El `rol` del participante existe con valor por defecto `JUGADOR`. | Decisión aprobada |
| R9 | `InscripcionDelegado` permite que el delegado sea el responsable de la inscripción o un participante de cualquier equipo de esa inscripción. | Decisión aprobada |
| R10 | Una persona puede participar en varias disciplinas dentro de la misma inscripción. | Decisión aprobada |
| R11 | Una persona NO puede estar registrada dos veces en la misma disciplina y ámbito de evento, aunque sea en equipos distintos o inscripciones distintas. | Decisión aprobada |

---

## 4. Mapa de Módulos y Modelos

### 4.1 Módulo `usuarios` (existente, extiende)

**Extiende el modelo `Usuario` existente** añadiendo la relación `persona_fk`.

```
usuarios/
└── domain/models/
    ├── usuario.py          # Usuario (existente, extiende)
    └── persona.py          # NUEVO: Persona
```

#### `Persona`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado de BaseModel |
| `nombres` | CharField(255) | Requerido |
| `apellidos` | CharField(255) | Requerido |
| `tipo_documento` | CharField(3) | Choices: DNI, CE, PAS |
| `numero_documento` | CharField(20) | Único con tipo_documento |
| `genero` | CharField(1) | Choices: V, M |
| `telefono` | CharField(9) | Opcional, 9 dígitos |
| `whatsapp` | CharField(9) | Opcional, 9 dígitos |
| `contacto_emergencia_nombre` | CharField(120) | Opcional |
| `contacto_emergencia_telefono` | CharField(9) | Opcional |
| `aseguradora_nombre` | CharField(255) | Opcional |
| `aseguradora_numero_poliza` | CharField(50) | Opcional |
| `created_at` | DateTime | Heredado |
| `updated_at` | DateTime | Heredado |

**Constraint:** `UniqueConstraint(fields=['tipo_documento', 'numero_documento'], name='unique_tipo_numero_documento')`

---

### 4.2 Módulo `inscripciones` (nuevo)

```
inscripciones/
├── domain/
│   ├── models/
│   │   ├── disciplina.py       # Disciplina, Categoria
│   │   ├── paquete.py           # Paquete, PaqueteDisciplina
│   │   ├── evento.py           # Evento
│   │   ├── inscripcion.py       # Inscripcion, InscripcionDelegado, PersonaAceptacion
│   │   └── equipo.py            # EquipoInscrito, ParticipacionDisciplina, ParticipanteInscripcion
│   ├── constants.py             # Choices
│   ├── exceptions.py
│   ├── schemas/
│   ├── services/core/
│   ├── services/flujos/
│   └── selectors/
└── presentation/
    ├── schemas/
    ├── controllers/
    └── presenters/
```

#### `Disciplina`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `nombre` | CharField(100) | unique |
| `sigla` | CharField(20) | unique |
| `modalidad` | CharField(1) | Choices: M (masculino), F (femenino), X (mixto) |
| `min_jugadores` | PositiveInteger | Nullable — null = sin límite inferior |
| `max_jugadores` | PositiveInteger | Nullable — null = sin límite superior |
| `esta_activa` | Boolean | Default True |

**Nota:** Ambos campos (`min_jugadores`, `max_jugadores`) pueden ser nulos. Null = sin límite configurado en ese extremo. La validación de negocio ocurre en servicio (ver sección de Validaciones en dos niveles).

#### `Categoria`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `disciplina` | FK(Disciplina) | ON_DELETE PROTECT |
| `nombre` | CharField(50) | ej. "Junior", "Senior", "Master" |
| `anio_minimo` | PositiveInteger | Año de nacimiento mínimo |
| `anio_maximo` | PositiveInteger | Año de nacimiento máximo |
| `esta_activa` | Boolean | Default True |

#### `Paquete`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `nombre` | CharField(100) | unique |
| `descripcion` | TextField | Opcional |
| `cantidad_maxima_participantes` | PositiveInteger | Límite total de personas únicas en el paquete (caja/paquete completo) |
| `precio_regular` | DecimalField(10,2) | |
| `precio_promocional` | DecimalField(10,2) | Opcional |
| `valido_desde` | DateField | |
| `valido_hasta` | DateField | |
| `esta_activo` | Boolean | Default True |

**Nota:** `cantidad_maxima_participantes` representa la capacidad total del paquete, NO el límite parcial por disciplina. Es la cuenta de personas únicas (distintas) que pueden inscribirse en el paquete.

#### `PaqueteDisciplina` (through explícito)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `paquete` | FK(Paquete) | ON_DELETE CASCADE |
| `disciplina` | FK(Disciplina) | ON_DELETE CASCADE |

**Constraint:** `UniqueConstraint(fields=['paquete', 'disciplina'])`

#### `Evento`

Modelo para agrupar inscripciones y definir el alcance de la unicidad R11.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `nombre` | CharField(200) | ej. "Salesianos FEST 2026" |
| `fecha_inicio` | DateField | |
| `fecha_fin` | DateField | |
| `esta_activo` | Boolean | Default True |

#### `Inscripcion`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `evento` | FK(Evento) | ON_DELETE PROTECT |
| `responsable` | FK(Persona) | ON_DELETE PROTECT |
| `paquete` | FK(Paquete) | ON_DELETE PROTECT |
| `promocion` | CharField(10) | ej. "2002" |
| `estado` | CharField(20) | Choices EstadoInscripcion |
| `observacion` | TextField | Nullable — observación del Comité |

**NO tiene:** `codigo` (R6), `cantidad_participantes` (R7)

**Choices estado:** `RECIBIDA`, `EN_REVISION`, `OBSERVADA`, `VALIDADA`, `PAGO_PENDIENTE`, `PAGADA`, `CONFIRMADA`, `RECHAZADA`

#### `InscripcionDelegado`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `inscripcion` | FK(Inscripcion) | ON_DELETE CASCADE |
| `persona` | FK(Persona) | ON_DELETE PROTECT |

**Constraint:** `UniqueConstraint(fields=['inscripcion'], name='unique_delegado_por_inscripcion')` — un solo delegado por inscripción inicialmente.

**Nota de evolución:** Si en el futuro se aprueba que haya varios delegados, se elimina esta constraint via migración y se conserva la estructura FK/tabla idéntica.

**Validación en servicio:** `persona == inscripcion.responsable` OR `persona` es participante en algún equipo de esa inscripción.

#### `PersonaAceptacion` (auditable)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `persona` | FK(Persona) | ON_DELETE CASCADE |
| `tipo_aceptacion` | CharField(30) | ej. 'BASES', 'APTITUD_FISICA', 'IMAGEN' |
| `documento_version` | CharField(50) | ej. "BASES-SF26-2026-09-06" |
| `aceptado_en` | DateTimeField | |
| `ip_address` | GenericIPAddressField | Opcional |
| `user_agent` | CharField(500) | Opcional |

#### `EquipoInscrito`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `inscripcion` | FK(Inscripcion) | ON_DELETE CASCADE |
| `disciplina` | FK(Disciplina) | ON_DELETE PROTECT |
| `categoria` | FK(Categoria) | ON_DELETE PROTECT |
| `nombre` | CharField(120) | Nombre del equipo |

**Constraint:** `UniqueConstraint(fields=['inscripcion', 'disciplina'], name='uq_equipo_inscripcion_disciplina')` — **D7 CONFIRMADA**: un solo equipo por inscripción+disciplina, sin importar la categoría. La categoría es un atributo descriptivo del equipo, no un factor de unicidad.

**Significado de negocio:** Una `Inscripcion` puede tener varios `EquipoInscrito` (uno por disciplina distinta), pero NO puede tener dos equipos en la misma disciplina — aunque tengan categorías diferentes. Esto alinea con R10 (una persona puede jugar varias disciplinas) y R11 (cada persona aparece una sola vez por disciplina+evento). Si se necesita un equipo por categoría, la categoría se maneja como dato del equipo, no como llave de identificación.

---

## 4.3 Modelo de Participación: `ParticipacionDisciplina`

> **Problema原来的:** La regla R11 ("persona no puede estar dos veces en la misma disciplina y evento") era enforceable solo via query en servicio, lo cual es susceptible a race conditions bajo solicitudes concurrentes.
>
> **Solución:** Tabla intermedia `ParticipacionDisciplina` con campos directos `evento` y `disciplina` que permiten una `UniqueConstraint` a nivel de base de datos.

### `ParticipacionDisciplina`

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `evento` | FK(Evento) | ON_DELETE CASCADE |
| `disciplina` | FK(Disciplina) | ON_DELETE CASCADE |
| `persona` | FK(Persona) | ON_DELETE CASCADE |
| `equipo` | FK(EquipoInscrito) | ON_DELETE PROTECT |

**Constraints:**
- `UniqueConstraint(fields=['evento', 'disciplina', 'persona'], name='unique_persona_disciplina_evento')` — **protege R11 a nivel de BD**
- `UniqueConstraint(fields=['equipo', 'participacion'], name='unique_equipo_participacion')` — un equipo no tiene la misma participación dos veces

**¿Por qué campos directos en lugar de derivarlos?**  
La cadena original (`ParticipanteInscripcion` → `EquipoInscrito` → `Inscripcion` → `Evento` + `Disciplina`) requiere una constraint cross-table que Django no soporta de forma directa hasta Django 5.0+ con `UniqueConstraint` con `fields` a través de relaciones. Al materializar `evento` y `disciplina` como campos directos, la constraint `unique(evento, disciplina, persona)` se expresa sin subqueries y sin race conditions.

### `ParticipanteInscripcion` (rol por equipo)

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID | Heredado |
| `participacion` | FK(ParticipacionDisciplina) | ON_DELETE CASCADE |
| `equipo` | FK(EquipoInscrito) | ON_DELETE CASCADE |
| `rol` | CharField(20) | Choices: JUGADOR (default), CAPITAN, DELEGADO |
| `talle_camiseta` | CharField(5) | Choices: XS, S, M, L, XL, XXL, nullable |

**Sin constraint R11 propia** — la protección viene de `ParticipacionDisciplina`.

**Semántica:** `ParticipacionDisciplina` registra que una persona participa en una disciplina de un evento (único por BD). `ParticipanteInscripcion` registra en qué equipo y con qué rol. Cada `ParticipacionDisciplina` apuntará a un solo `ParticipanteInscripcion` activo en la práctica, ya que R11 lo impide.

---

## 4.4 Consistencia entre `ParticipacionDisciplina` y `EquipoInscrito`

**Problema potencial:** `ParticipacionDisciplina` tiene `evento` y `disciplina` como campos directos, pero también tiene `equipo`. Podría haber inconsistencia si `participacion.evento` ≠ `equipo.inscripcion.evento` o `participacion.disciplina` ≠ `equipo.disciplina`.

**Estrategia de consistencia:**

1. **Validación en servicio al crear.** En el flujo `_crear_inscripcion_flujo`, antes de grabar `ParticipacionDisciplina`, se verifica que `equipo.inscripcion.evento == evento` y `equipo.disciplina == disciplina`. Esta validación ocurre dentro del mismo `transaction.atomic`, por lo que es atómica.

2. **Campo `equipo` no modificable después de creación.** Una vez creado, no se permite cambiar `ParticipacionDisciplina.equipo`. Si el participante cambia de equipo, se elimina el `ParticipanteInscripcion` y se crea uno nuevo apuntando a otra `ParticipacionDisciplina` (en otro equipo), lo cual está prohibido por R11.

3. **Constraint de cobertura (opcional, PostgreSQL).** Se puede agregar una ` ExclusionConstraint` con `GIST` si se usa PostgreSQL, o una trigger-based check, para rechazar cualquier fila donde `participacion.evento != equipo.inscripcion.evento`. Para SQLite (desarrollo) esto no aplica.

4. **Lectura siempre via servicio.** Los servicios exponen consultas queunen la cadena completa para consumo, nunca acceden directamente a `ParticipacionDisciplina.evento` sin atravesé el `equipo`.

**Decisión de diseño:** No se implementa check constraint automático en la migración inicial. Se confía en la validación en servicio (punto 1) y en que el campo `equipo` no sea modificable. Si en el futuro se detecta inconsistencia via tests o auditoría, se agrega la constraint de DB.

---

## 4.5 Validación de Cupos: Dos Niveles Independientes

### Nivel 1 — Cupo por equipo/disciplina (`Disciplina.min_jugadores` / `max_jugadores`)

Cuando se agrega un participante a un equipo, el servicio valida:

- Si `Disciplina.min_jugadores` no es null: el equipo debe tener al menos ese número de participantes.
- Si `Disciplina.max_jugadores` no es null: el equipo no debe exceder ese número de participantes.

Null en cualquier extremo significa "sin límite configurado en ese extremo".

**No afecta a otras disciplinas ni a otras inscripciones.** Una misma `Persona` puede participar en múltiples disciplinas de la misma inscripción (R10), cada una con su propio conteo independiente.

### Nivel 2 — Capacidad total del paquete (`Paquete.cantidad_maxima_participantes`)

Al crear o modificar una inscripción, el servicio valida que el total de **personas únicas** (`DISTINCT Persona`) asociadas al paquete no exceda `Paquete.cantidad_maxima_participantes`.

**D6 CONFIRMADA — conteo DISTINCT:** `Paquete.cantidad_maxima_participantes` cuenta personas DISTINCT en toda la `Inscripcion`.

- Si el máximo del paquete es 15, puede haber como máximo **15 personas distintas**.
- Esas mismas 15 personas pueden distribuirse/reutilizarse en múltiples disciplinas sin consumir capacidad adicional del paquete.
- Una misma `Persona` que participa en 3 disciplinas distintas suma **1** para el total del paquete.
- Cada disciplina/equipo por separado debe respetar `Disciplina.min_jugadores` y `max_jugadores` cuando están configurados (Nivel 1).

**Validación en servicio (Nivel 2):**
```python
# Cuenta personas distintas en la inscripción
total_personas = (
    ParticipacionDisciplina.objects
    .filter(equipo__inscripcion=inscripcion)
    .values('persona')
    .distinct()
    .count()
)
if total_personas > paquete.cantidad_maxima_participantes:
    raise BusinessError("Se excede la capacidad máxima del paquete.")
```

---

## 5. Decisión de Diseño: `Evento` vs `EdicionEvento`

### Recomendación: Crear `Evento` simple

Para cumplir la regla R11 es necesario definir el **alcance del evento**. Sin `Evento`, no hay forma de distinguir si dos inscripciones pertenecen al mismo evento deportivo.

| Alternativa | Pros | Contras |
|-------------|------|---------|
| A. `Evento` simple | Claridad semántica, fácil de consultar | Una tabla adicional |
| B. `EdicionEvento` (evento + edición) | Permite versionar ediciones del mismo evento | Más complejidad, overkill para MVP |
| C. Sin modelo (año/constante) | Simple inicialmente | Acoplamiento implícito, difícil de extender |

**Recomendación: Alternativa A — `Evento` simple.**

Razones:
1. Agrupa inscripciones y proporciona el alcance para la constraint R11.
2. El mockup sugiere "Salesianos FEST 2026" como evento único — modelo simple es suficiente.
3. Si en el futuro hay que versionar (ej. "FEST 2027"), se crea otro `Evento`.

---

## 6. Flujos Clave

### 6.1 Registro de Usuario / Responsable

```
1. Visitante completa formulario en /register (frontend)
2. Controller: POST /auth/register
3. Orchestrator → Flujo:
   a. Crear Persona (datos civiles)
   b. Crear Usuario con persona_fk
   c. Crear PersonaAceptacion (bases aceptadas)
   d. transaction.atomic() envolviendo todo
4. Response: usuario creado + redirect a /inscripcion
```

### 6.2 Creación de Inscripción (Flujo simplificado — una sola submission)

> **Nota (2026-09-19):** Este flujo es **simplificado sin BORRADOR/pre-registro**. El frontend captura todos los datos (paquete seleccionado, equipos, participantes, delegado, aceptaciones) y envía un payload completo a `POST /inscripciones/`. El backend crea la `Inscripcion` en estado `RECIBIDA` en una sola transacción. El pago se difiere al módulo `pagos` futuro.

```
1. Responsable autenticado completa formulario/wizard (todos los datos en una pantalla o varios pasos)
2. Controller: POST /inscripciones/
3. Orchestrator → Flujo _crear_inscripcion:
   a. Validar que responsable no tenga inscripción activa en este evento (selector)
   b. Crear Inscripcion con estado inicial RECIBIDA
   c. Por cada disciplina seleccionada:
      - Crear EquipoInscrito
      - Por cada deportista:
        - Crear o relacionar Persona (por documento)
        - Crear ParticipacionDisciplina (evento + disciplina + persona + equipo)
          → La UniqueConstraint de BD rechaza duplicados (R11 protegido)
        - Crear ParticipanteInscripcion (participacion + equipo + rol + talle)
   d. Crear InscripcionDelegado (si no es el responsable)
   e. Por cada aceptación:
      - Crear PersonaAceptacion
   f. transaction.atomic() envolviendo todo
4. Response: Inscripcion con equipos y participantes
5. Pago: diferido — se maneja en módulo `pagos` futuro (no en MVP)
```

### 6.3 Validación R11 — protección por BD vs. servicio

**Capa 1 — UniqueConstraint de BD (siempre activa):**

```python
# En ParticipacionDisciplina:
UniqueConstraint(
    fields=['evento', 'disciplina', 'persona'],
    name='unique_persona_disciplina_evento'
)
```

Si dos solicitudes concurrentes intentan crear la misma `ParticipacionDisciplina`, la base de datos rechaza la segunda con `IntegrityError`. El flujo captura esta excepción y la transforma en `ConflictError` con mensaje legible.

**Capa 2 — Validación en servicio (fallback UX):**

Antes de intentar crear, se hace un `SELECT` para verificar si ya existe y lanzar `ConflictError` con mensaje de negocio antes de llegar a la excepción de BD.

```python
def _validar_r11(self, evento_id, disciplina_id, persona_id):
    if ParticipacionDisciplina.objects.filter(
        evento_id=evento_id,
        disciplina_id=disciplina_id,
        persona_id=persona_id,
    ).exists():
        raise ConflictError("La persona ya está registrada en esta disciplina en este evento.")
```

**Capa 3 — Validación de consistencia equipo/evento-disciplina:**

```python
def _validar_consistencia_equipo(self, participacion_data, equipo):
    if equipo.inscripcion.evento_id != participacion_data['evento_id']:
        raise BusinessError("El equipo no pertenece al evento de la participación.")
    if equipo.disciplina_id != participacion_data['disciplina_id']:
        raise BusinessError("El equipo no pertenece a la disciplina de la participación.")
```

### 6.4 Pago (futuro, módulo `pagos`)

```
1. Comité valida inscripción (cambia estado a VALIDADA)
2. Responsable consulta estado → ve PAGO_PENDIENTE
3. Flujo futuro (Izipay):
   a. Crear OrdenPago (monto, inscripción, estado='PENDIENTE')
   b. Redirigir a Izipay
   c. Izipay webhook → actualizar estado de TransaccionPago
   d. Si exitoso → actualizar OrdenPago a PAGADA → actualizar Inscripcion a PAGADA
```

---

## 7. Decisiones: Estado Final y Clasificación

### 7.1 Decisiones de Negocio Explicitamente Confirmadas por el Usuario

| # | Decisión | Detalle |
|---|----------|---------|
| D1 | Un `InscripcionDelegado` por inscripción inicialmente | FK + `UniqueConstraint(fields=['inscripcion'])`. Si en el futuro se permiten varios, se elimina la constraint via migración. |
| D6 | `Paquete.cantidad_maxima_participantes` cuenta personas DISTINCT | Una misma persona en varias disciplinas suma 1. Las 15 personas pueden estar en múltiples disciplinas sin costo adicional. |
| D7 | Un `EquipoInscrito` por `Inscripcion` + `Disciplina` | `UniqueConstraint(fields=['inscripcion', 'disciplina'])`. No se permiten dos equipos en la misma disciplina aunque tengan categorías distintas. |

### 7.2 Defaults Arquitectónicos / Recomendaciones Técnicas (no contradichas por el usuario)

Estas son decisiones de diseño que el documento recomienda por coherencia técnica. No fueron explícitamente discutidas, pero no contradicen ninguna regla confirmada:

| # | Default | Recomendación |
|---|---------|---------------|
| D2 | `max_jugadores` / `min_jugadores` null = sin límite en ese extremo | El servicio valida según los valores configurados en la disciplina. |
| D3 | Categoría manual en wizard con validación de rango | El usuario elige la categoría; el servicio valida que el año de nacimiento esté en el rango de la categoría. |
| D4 | Precio único por paquete | El mockup muestra un monto fijo; es el modelo más simple. |
| D5 | Sin `ExclusionConstraint` de BD en MVP | La validación en servicio + campo no modificable es suficiente. Se puede agregar post-MVP si se usa PostgreSQL. |

### 7.3 Decisiones Deferibles (pagos o post-MVP)

| # | Decisión | Por qué deferir |
|---|----------|----------------|
| DF-A | `ExclusionConstraint` de BD para consistencia equipo↔participacion | Requiere PostgreSQL; la validación en servicio es suficiente para el MVP. |
| DF-B | Múltiples delegados por inscripción | La estructura FK lo permite; la constraint es removible via migración cuando se necesite. |
| DF-C | Integración Izipay / módulo `pagos` | Completamente separable del modelo de inscripción. |
| DF-D | Auditoría de cambios de estado de `Inscripcion` | Tabla de auditoría; no bloquea creación ni transición de estados. |

### 7.4 Decisiones que No Aplican al Primer Apply

- **`Categoria` behavior (D3):** La categoría NO necesita validarse para el primer apply de modelos. El modelo `Categoria` existe con sus campos (nombre, anio_minimo, anio_maximo). La lógica de validación automática vs. manual se define cuando se implemente el flujo de wizard, no es blocker para crear el modelo.

> **Conclusión:** El modelo core de `usuarios` y `inscripciones` está **suficientemente definido** para proceder a `sdd-apply`. Las decisiones de negocio explícitas están confirmadas (D1, D6, D7). Los defaults técnicos (D2-D5) son coherentes y no fueron contradichos. Las decisiones deferibles son extensiones, no precondiciones.

---

## 8. Plan de Ejecución por Fases (SDD Apply)

### Fase 1: `usuarios` — Extender con `Persona`

**Archivos a crear/modificar:**
- `backend/modules/usuarios/domain/models/persona.py` — nuevo
- `backend/modules/usuarios/domain/models/__init__.py` — re-exportar Persona
- `backend/modules/usuarios/domain/constants.py` — Choices de documento y género
- `backend/modules/usuarios/domain/schemas/` — PersonaCreateData, PersonaUpdateData
- `backend/modules/usuarios/domain/services/core/persona_service.py` — sync CRUD
- `backend/modules/usuarios/presentation/schemas/` — HTTP schemas
- `backend/modules/usuarios/presentation/controllers/` — endpoints si corresponde
- `backend/modules/usuarios/admin.py` — registrar Persona

**Dependencias:** ninguna (módulo existente)

### Fase 2: `inscripciones` — Modelos base

**Archivos a crear:**
- `backend/modules/inscripciones/apps.py`
- `backend/modules/inscripciones/domain/models/disciplina.py`
- `backend/modules/inscripciones/domain/models/categoria.py`
- `backend/modules/inscripciones/domain/models/paquete.py`
- `backend/modules/inscripciones/domain/models/evento.py`
- `backend/modules/inscripciones/domain/models/inscripcion.py`
- `backend/modules/inscripciones/domain/models/equipo.py` — incluye `ParticipacionDisciplina`
- `backend/modules/inscripciones/domain/constants.py`
- `backend/modules/inscripciones/domain/exceptions.py`
- `backend/modules/inscripciones/di.py`
- Migraciones iniciales

**Dependencias:** Fase 1 completa (`Persona` disponible)

### Fase 3: `inscripciones` — Servicios y Lógica de Negocio

**Servicios core sync:**
- `DisciplinaService`, `CategoriaService`, `PaqueteService`, `EventoService`
- `InscripcionService` — crear, actualizar estado
- `EquipoService` — crear equipo
- `ParticipacionService` — crear participación con validación R11 (capa 1 BD + capa 2 servicio) y consistencia equipo
- `ParticipanteService` — crear/actualizar rol y talle

**Flujos async:**
- `_crear_inscripcion_flujo` — creación completa con transaction.atomic
- `_agregar_participante_flujo` — agregar persona a equipo con protección R11
- `_cambiar_estado_inscripcion_flujo` — cambio de estado por Comité
- `_asignar_delegado_flujo` — asignar/reemplazar delegado

**Dependencias:** Fase 2 completa

### Fase 4: `inscripciones` — Presentación (API)

**Schemas HTTP:** DisciplinaIn/Out, CategoriaIn/Out, PaqueteIn/Out, InscripcionIn/Out, EquipoIn/Out, ParticipacionIn/Out, ParticipanteIn/Out, DelegadoIn/Out

**Controllers:** CRUD para catálogos; creación y listado de inscripciones; cambio de estado por Comité.

**Dependencias:** Fase 3 completa

### Fase 5: `pagos` — Modelo e Integración Izipay (futuro)

Modelos: `OrdenPago`, `TransaccionPago`, `ComprobantePagoManual`. Esta fase queda postergada.

---

## 9. Constraints y Validaciones Clave

| Constraint | Tipo | Dónde |
|------------|------|-------|
| `unique(tipo_documento, numero_documento)` en Persona | DB | Modelo |
| `unique(paquete, disciplina)` en PaqueteDisciplina | DB | Modelo |
| `unique(inscripcion, disciplina)` en EquipoInscrito | DB | **D7** — un equipo por inscripción+disciplina (sin importar categoría) |
| `unique(evento, disciplina, persona)` en ParticipacionDisciplina | DB | **R11 protegida por BD sin race conditions** |
| `unique(inscripcion)` en InscripcionDelegado | DB | Modelo — un delegado por inscripción (removible via migración) |
| Delegate debe ser responsable o participante | Servicio | Validación en flujo |
| Null en min/max jugadores = sin límite en ese extremo | Servicio | Validación al crear equipo |
| Consistencia equipo ↔ participacion (evento y disciplina) | Servicio | Validación en ParticipacionService |
| Cupo total paquete ≤ `Paquete.cantidad_maxima_participantes` (personas distintas) | Servicio | Validación en flujo de inscripción — **D6 confirmada**: conteo DISTINCT de personas |

---

## 10. Mapeo de Módulos Existentes a Nuevos

| Módulo Django | Label | Contiene |
|---------------|-------|----------|
| `modules.usuarios` | `usuarios` | Usuario + Persona (extendido) |
| `modules.inscripciones` | `inscripciones` | Disciplina, Categoria, Paquete, Evento, Inscripcion, Equipo, ParticipacionDisciplina, Participante, Delegado, Aceptacion |
| `modules.pagos` | `pagos` | OrdenPago, TransaccionPago, ComprobanteManual (futuro) |

**Registro en `INSTALLED_APPS`:** Agregar `'modules.inscripciones'` y `'modules.pagos'` en `backend/config/settings/base.py`.

**Registro DI:** Agregar en `NINJA_EXTRA.INJECTOR_MODULES`.

---

## 11. Nomenclatura Seguida

| Concepto | Nombre en código | Notas |
|----------|-----------------|-------|
| Persona natural (datos civiles) | `Persona` | |
| Usuario del sistema | `Usuario` | |
| Deportivo | `Disciplina` | |
| Rama etaria | `Categoria` | ej. Junior, Senior |
| Producto vendido | `Paquete` | |
| Evento deportivo | `Evento` | ej. "Salesianos FEST 2026" |
| Solicitud de inscripción | `Inscripcion` | |
| Equipo dentro de una inscripción | `EquipoInscrito` | |
| Participación en disciplina+evento | `ParticipacionDisciplina` | **Tabla de protección R11** |
| Deportista en equipo | `ParticipanteInscripcion` | |
| Representante legal de inscripción | `InscripcionDelegado` | |
| Aceptaciones auditable | `PersonaAceptacion` | |

---

## 12. Resumen de Confirmaciones de Usuario vs. Defaults Técnicos

### Decisiones explícitamente confirmadas por el usuario

| # | Decisión | Estado |
|---|----------|--------|
| D1 | Un `InscripcionDelegado` por inscripción (FK + constraint única) | ✅ Confirmada |
| D6 | `Paquete.cantidad_maxima_participantes` cuenta DISTINCT Persona | ✅ Confirmada |
| D7 | Un `EquipoInscrito` por `Inscripcion` + `Disciplina` | ✅ Confirmada |
| — | `PersonaAceptacion` auditable (no booleanos c1/c2/c3) | ✅ Confirmada |
| — | `PaqueteDisciplina` como through explícito | ✅ Confirmada |
| — | Cambios generales al modelo de paquetes aceptados | ✅ Confirmados |

### Defaults arquitectónicos (no contradichos)

| # | Default | Estado |
|---|---------|--------|
| D2 | `min/max_jugadores` null = sin límite en ese extremo | ✅default vigentes |
| D3 | Categoría manual en wizard con validación de rango | ✅default vigentes |
| D4 | Precio único por paquete | ✅default vigentes |
| D5 | Sin `ExclusionConstraint` en MVP | ✅default vigentes |

---

## 13. Correcciones respecto a versión 1.0

| # | Problema | Solución |
|---|----------|---------|
| C1 | R11 era validada solo en servicio — race condition bajo concurrencia | Nueva tabla `ParticipacionDisciplina` con `UniqueConstraint(evento, disciplina, persona)` a nivel de BD |
| C2 | `ParticipanteInscripcion` derivaba disciplina/evento por cadena transitiva | `ParticipacionDisciplina` materializa los campos directos; consistency validada en servicio al crear |
| C3 | La documentación de constraints no mencionaba la protección R11 en BD | Sección 9 actualizada; pseudocódigo de validación de 3 capas en sección 6.3 |
| C4 | Flujo de creación no reflejaba el modelo de participación | Sección 6.2 actualizada con creación de `ParticipacionDisciplina` antes de `ParticipanteInscripcion` |

## 14. Cambios en versión 1.2

| # | Cambio | Detalle |
|---|--------|---------|
| V2-1 | `InscripcionDelegado` ahora usa FK normal + `UniqueConstraint(fields=['inscripcion'])` | Permite evolución a múltiples delegados via migración (eliminar constraint) |
| V2-2 | `Disciplina.min_jugadores` y `max_jugadores` son ambos nullable explícitamente | Documentado en modelo y en R4 |
| V2-3 | `Paquete.capacidad` renombrado a `Paquete.cantidad_maxima_participantes` | Refleja语义 de cupo total de personas, no de equipos |
| V2-4 | Nueva sección 4.5 de validación en dos niveles | Nivel 1: cupo por equipo/disciplina; Nivel 2: cupo total de paquete |
| V2-5 | Decisión abierta D6 agregada | Pregunta sobre conteo de persona multi-disciplina para capacidad de paquete |
| V2-6 | Sección 12 actualizada con confirmación D6 | Incluida como decisión crítica requerida antes de apply |

## 15. Cambios en versión 1.4

| # | Cambio | Detalle |
|---|--------|---------|
| V4-1 | **D7 CONFIRMADA — constraint en `EquipoInscrito`** | `UniqueConstraint(fields=['inscripcion', 'disciplina'], name='uq_equipo_inscripcion_disciplina')`. Una `Inscripcion` puede tener un `EquipoInscrito` por disciplina, no por categoría. |
| V4-2 | Significado de negocio de D7 documentado | Explicación: la categoría es descriptiva del equipo, no factor de identificación.alinea con R10 y R11. |
| V4-3 | Sección 7 reescrita como tabla de estado | Todas las decisiones D1-D7 marcadas como CONFIRMADAS. |
| V4-4 | Nueva subsección 7.2 de blockers | Clasificación explícita: **sin blockers** para apply de `usuarios`/`inscripciones`. |
| V4-5 | Nueva subsección 7.3 de decisiones deferibles | DF-A a DF-D: postergadas a pagos o post-MVP. |
| V4-6 | Sección 9 (Constraints) actualizada con D7 | Referencia a `unique(inscripcion, disciplina)` en EquipoInscrito. |
| V4-7 | **Modelo listo para sdd-apply** | Las decisiones de dominio que afectan los modelos core están cerradas. |

## 16. Decisión D7 — Detalle Completo

### Problema original

La constraint original `(inscripcion, disciplina, categoria)` en `EquipoInscrito` permitía crear MÚLTIPLES equipos en la misma inscripción y disciplina si tenían categorías diferentes. Esto contradecía la regla de negocio confirmada por el usuario.

### Decisión D7

`UniqueConstraint(fields=['inscripcion', 'disciplina'], name='uq_equipo_inscripcion_disciplina')` — una `Inscripcion` puede tener **un solo** `EquipoInscrito` por `Disciplina`, sin importar la categoría.

### Significado de negocio

- Una inscripción puede inscribirse en varias disciplinas → varios `EquipoInscrito` (uno por disciplina).
- Dentro de la misma disciplina, NO puede haber dos equipos aunque tengan categorías diferentes.
- La `Categoria` es un atributo descriptivo del equipo (ej. "Junior", "Senior"), no una dimensión de identificación.
- Si en el futuro se necesita representar "equipo categoría Junior + equipo categoría Senior en la misma disciplina", eso sería una segunda `Inscripcion` (diferente paquete o contexto comercial).

### Implicación en `ParticipacionDisciplina`

Con un solo equipo por inscripción+disciplina, la cadena `ParticipacionDisciplina.equipo.inscripcion.evento` es determinista para una disciplina dada. La validación de consistencia equipo↔participacion sigue siendo necesaria para protección defensiva, pero el caso de conflicto múltiple equipo por disciplina ya no puede ocurrir a nivel de datos.

---

## 17. Cambios en versión 1.5

| # | Cambio | Detalle |
|---|--------|---------|
| V5-1 | R4 nuance: null semantics en min/max_jugadores | Aclarado: es interpretación arquitectónica, no wording explícito del usuario. |
| V5-2 | Sección 7 reescrita completamente | Distingue: decisiones explícitas de usuario (D1/D6/D7) vs. defaults técnicos (D2-D5) vs. deferibles (DF-A a DF-D). |
| V5-3 | Sección 9 corregida | Nota "requiere confirmación D6" eliminada — D6 ya está confirmada. |
| V5-4 | Sección 12 reescrita | Ya no framed as "confirmaciones pendientes"; distingue confirmadas vs. defaults vigentes. |
| V5-5 | Subsección 7.4 agregada | `Categoria` behavior (D3) explícitamente deferido; no es blocker para primer apply. |
| V5-6 | Engram actualizado | Artifact `sdd/salesianos-backend-domain-plan/explore` corregido para reflejar atribución correcta. |

## 18. Cambios en versión 1.6

| # | Cambio | Detalle |
|---|--------|---------|
| V6-1 | Flujo simplificado documentado | Sección 6.2 ahora clarifica: una sola submission, estado inicial `RECIBIDA`, sin BORRADOR/pre-registro. |
| V6-2 | Pago diferido explícito | Sección 6.2 y 6.4 indican que el pago se maneja en módulo `pagos` futuro, no en el MVP actual. |
| V6-3 | Paquete sin complejidad extra de pricing | `Paquete` usa `precio_regular` (único) — no hay `precio_preventa`, `fecha_fin_preventa` ni versioning de precios. |

---

*Documento generado como resultado de SDD explore phase.*
