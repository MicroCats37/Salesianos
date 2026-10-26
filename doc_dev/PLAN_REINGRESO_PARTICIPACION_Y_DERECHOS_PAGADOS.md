# Exploration: Participación — Reingreso y Derechos Pagados

> **Proyecto:** `Salesianos`
> **Fecha:** 2026-10-19
> **Tipo:** Architecture Exploration
> **Artifact:** `sdd/participacion-reingreso-y-derechos-pagados/explore`
> **Modo:** Exploration — no implementation

---

## 1. Escenario Reportado

El usuario reporta:
1. Una persona tiene una participación retirada (estado=`R`) en una disciplina/evento/equipo
2. Se le agrega de nuevo y el sistema crea otra fila activa (estado=`A`)
3. La verificación R11 solo comprueba participación activa, permitiendo el duplicado histórico
4. El conteo del roster en el presenter usa filas activas mientras el array de participantes incluye filas retiradas, causando conteos visuales inconsistentes

---

## 2. Estado Actual del Sistema

### 2.1 Verificación R11 en `ParticipacionCoreService.crear()`

**Archivo:** `backend/modules/salesianos_fest/domain/services/core/participacion_service.py:40-48`

```python
# R11 check: any active participacion for same (evento, disciplina, persona)?
existing = Participacion.objects.filter(
    evento_id=evento_id,
    disciplina_id=disciplina_id,
    persona_id=persona_id,
    estado="A",  # <-- SOLO activos
).exists()
if existing:
    raise R11ViolationError()
```

**Veredicto:** R11 verifica solo `estado="A"`. Si existe una participación retirada (`R`), no la encuentra. Esto es **correcto** según la especificación FEST.

### 2.2 Spec FEST — Regla R11

**Fuente:** `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md:34`

> "No puede jugar dos veces en la **misma disciplina del mismo evento**, aunque sea en inscripciones diferentes (regla R11)."

**Fuente:** `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md:391-392`

> "**Unicidad:** `(evento, disciplina, persona)` WHERE `estado=A` — partial unique constraint (R11)"
> "**R11:** Una persona no puede participar activamente en la misma disciplina del mismo evento a través de dos inscripciones distintas."

### 2.3 Flujo de Reingreso Después de Retiro

**Archivo:** `backend/modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py:86-93`

```python
# Create or get existing InscripcionPersona
ip, created = InscripcionPersona.objects.get_or_create(
    inscripcion_id=data.inscripcion_id,
    persona_id=str(persona.id),
    defaults={"estado": "A"},
)
if not created and ip.estado == "R":
    ip.estado = "A"  # Reactiva InscripcionPersona
    ip.save()
```

El `InscripcionPersona` se reactiva (cambia `R` → `A`). Pero la participación se crea via `ParticipacionCoreService.crear()` que crea una **nueva fila** de `Participacion` con `estado="A"`.

**Archivo:** `backend/modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py:106-116`

```python
# R11 check is done by ParticipacionCoreService.crear()
participacion_core = ParticipacionCoreService()
participacion_data = ParticipacionCreateData(
    inscripcion_persona_id=str(ip.id),
    equipo_id=str(data.equipo_id),
    ...
)
participacion = participacion_core.crear(participacion_data)  # Nueva fila
```

### 2.4 Conteo de Roster en el Presenter

**Archivo:** `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py:74-79`

```python
# Count ACTIVA participaciones only. The DB stores estado as a
# single-char code ("A" = Activa, "R" = Retirada) per the
# `EstadoParticipacionChoices` — NOT the verbose "ACTIVA" string.
# Using the wrong literal here silently returns 0 for every team.
activas = [p for p in eq.participaciones if p.estado == "A"]
jugadores_registrados = len(activas)
```

**Archivo:** `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py:108-134`

```python
participantes: [
    ParticipacionOut(
        ...
        estado=p.estado,  # Incluye "A" y "R"
        ...
    )
    for p in eq.participaciones  # <-- TODOS, no filtra por estado
],
```

**Conclusión:** `jugadores_registrados` cuenta solo `estado="A"`, pero `participantes[]` incluye TODAS las participaciones (activas y retiradas).

### 2.5 Selector que Carga Participaciones

**Archivo:** `backend/modules/salesianos_fest/domain/selectors/participacion_selector.py:42-70`

```python
@staticmethod
def get_by_equipo(equipo_id: str) -> list[ParticipacionResult]:
    """Return all participaciones for an equipo."""
    qs = Participacion.objects.select_related(...).filter(
        equipo_id=equipo_id
    ).order_by("created_at")
    # No filtra por estado — devuelve TODOS
```

---

## 3. Análisis del Escenario Reportado

### 3.1 "¿El sistema permite duplicados históricos?"

**Respuesta:** Sí, y es **correcto**. R11 solo impide que una persona tenga DOS participaciones ACTIVAS en la misma disciplina/evento. Una participación retirada (`R`) + una nueva activa (`A`) es el comportamiento esperado.

**Fuentes que lo confirman:**
- FEST Spec T10: "Juan se retira de inscripción A pero permanece en B" → puede reingresar a otra inscripción
- FEST Spec T13: "Juan retira a un jugador pero este aún juega otra disciplina en la misma inscripción" → no libera el cupo inmediatamente
- F5 (Spec líneas 174-181): "Si ya no juega en ninguna disciplina de esa inscripción: cambiar asignación activa a LIBERADA"

### 3.2 "¿La verificación R11 está incompleta?"

**Respuesta:** No. R11 está implementada correctamente. Solo verifica activos (`estado="A"`) porque la restricción de BD es un **partial unique constraint** `(evento, disciplina, persona) WHERE estado=A`.

### 3.3 "¿El conteo del presenter es inconsistente?"

**Respuesta:** Parcialmente sí — existe una **inconsistencia visual**. El `participantes[]` que se envía al frontend incluye filas retiradas, pero `jugadores_registrados` las ignora. Esto puede confundir en el frontend si el UI muestra ambos sin distinción.

Sin embargo, **mostrar histórico de participantes retiradas es intencional** — permite al admin ver quién fue parte del equipo aunque ya no esté.

### 3.4 "¿Qué hay del flujo Mover?"

**Archivo:** `backend/modules/salesianos_fest/domain/services/orchestrators/participacion_orchestrator.py:60-86`

```python
def _mover_atomico(self, participacion_id: str, equipo_destino_id: str):
    with transaction.atomic():
        p = self._participacion_core.obtener_por_id(participacion_id)
        eq_destino = Equipo.objects.get(id=equipo_destino_id)
        p.equipo = eq_destino  # Solo cambia equipo
        p.save()               # No crea fila nueva
```

Mover NO crea nueva participación — solo actualiza `equipo_id` de la fila existente. R11 no se dispara porque no hay `crear()`. Esto significa que una persona PUEDE moverse entre equipos de la misma disciplina dentro de la misma inscripción sin verificar R11.

**¿Es esto un bug?** Técnicamente no viola R11 (no hay doble participación activa), pero el flujo no verifica explícitamente. Si el drag-drop del frontend permite mover y luego el backend lo procesa sin R11, el usuario no recibe feedback de que eso no está permitido si ya existiera otra participación activa.

---

## 4. Distinción de Conceptos

### 4.1 Historia de Participación vs. Reingreso

| Concepto | Estado | Descripción |
|---|---|---|
| Historia de participación | `A` + `R` | Todas las filas de `Participacion` para auditoría |
| Participación activa | `A` | Fila(s) que cuenta(n) para R11 y roster |
| Reingreso | Nueva fila `A` tras `R` | Correcto — no viola R11 |

**Regla:** R11 protege participaciones ACTIVAS simultáneas. Una persona puede tener múltiples filas `R` (retirada) y como máximo UNA `A` por disciplina/evento.

### 4.2 Derechos Pagados (`AsignacionCupo`) vs. Participación

| Aspecto | `AsignacionCupo` | `Participacion` |
|---|---|---|
| Qué representa | Cupo comercial pagado asignado a persona | Participación deportiva en equipo/disciplina |
| Estados | `ACTIVA` / `LIBERADA` / `REVOCADA` | `A` (Activa) / `R` (Retirada) |
| Creación | Al confirmar pago (F2) | Al agregar persona a equipo |
| Liberación | Al retirar persona si no juega más en ninguna disciplina (F5) | Al retirer participación |
| Relación | Vinculada a `Compra` | Vinculada a `Equipo` |

**Fuente:** `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md:118`

> "**AsignacionCupo:** Se crea al confirmarse compra para personas registradas y cubiertas..."

### 4.3 Compra/Pago y Acreditación

```
Compra (PENDIENTE/PAGADA/CANCELADA)
  └── CompraInscripcion (vincula compra genérica a Inscripcion FEST)
        └── AsignacionCupo (ACTIVA cuando hay cupo disponible, LIBERADA al retirar)
              └── AcreditacionEvento (acceso efectivo al evento)
```

**Fuente:** `backend/modules/salesianos_fest/domain/services/flujos/liberar_cupo_flujo.py:86-126`

Cuando se libera un cupo:
1. `Participacion.estado = "R"` para todas las participaciones de esa persona en la inscripción
2. `AsignacionCupo.estado = "LIBERADA"` (si no hay otras participaciones activas)
3. `AcreditacionEvento` se recalcula considerando OTRAS inscripciones con origen pagado

---

## 5. Análisis de Opciones

### Opción A — Reactivación (Mantener Actual)

**Descripción:** Cuando una persona retirada vuelve a participar, se CREA una nueva fila `Participacion` con `estado="A"`. La fila `R` permanece como auditoría.

**Pros:**
- Historial completo — no se pierde cuándo salió y cuándo volvió
- R11 se cumple trivialmente (una sola `A` a la vez)
- alineado con FEST spec F5

**Contras:**
- Una persona puede tener MUCHAS filas `R` si entra y sale múltiples veces
- `participantes[]` del presenter incluye histórico,可能导致 UI confuso
- No hay forma de saber "la última participación activa" sin filtrar

**Complejidad:** N/A (es el comportamiento actual y es correcto)

### Opción B — Bloqueo de Reingreso

**Descripción:** No permitir crear nueva participación si ya existe una fila `R` para mismo (evento, disciplina, persona). Requerir que un admin reabra la participación original.

**Pros:**
- Mantiene la participación original como única fila
- Menos filas en la tabla

**Contras:**
- Pierde historial de ida y vuelta
- No permite escenarios legítimos de "entró, salió, volvió" (T10)
- Requiere flujo de "reactivar" adicional

**Complejidad:** Alta — requiere nuevo flujo, UI de reactivación, y no está en la spec

### Opción C — Ocultar Filas Retiradas del Participantes[]

**Descripción:** En el presenter, filtrar `participantes[]` para excluir `estado="R"` del array enviado al frontend, pero mantener `jugadores_registrados` como está.

**Pros:**
- Elimina la inconsistencia visual
- Roster count sigue siendo correcto (solo activos)
- Cambio pequeño en el presenter

**Contras:**
- Admin pierde visibilidad del histórico de participantes retiradas
- Si necesita ver quién fue retire, debe consultar otra vista

**Complejidad:** Baja — cambio en una línea del presenter

### Opción D — Separar Histórico de Activos (Mejor)

**Descripción:** Mantener dos arrays en `EquipoDetalleOut`:
- `participantes: ParticipanteOut[]` — solo `estado="A"`
- `historico: ParticipanteOut[]` — solo `estado="R"`

**Pros:**
- Consistencia: `participantes` = activos = conteo
- Admin puede ver histórico en campo separado
- Alineado con principios de separación de concerns

**Contras:**
- Breaking change en el schema de API
- Requiere cambios en frontend para mostrar `historico[]`

**Complejidad:** Media — schema, presenter, y frontend

---

## 6. Recomendación

### 6.1 Respuesta a las Preguntas del Usuario

| Pregunta | Respuesta |
|---|---|
| ¿El reingreso es correcto? | **Sí** — el sistema permite crear nueva fila `A` tras `R`. Es el comportamiento correcto según FEST spec F5 y T10. |
| ¿Cuándo es válida una nueva fila? | Cuando NO existe otra fila `A` para ese (evento, disciplina, persona). La presencia de `R` no blocking. |
| ¿Mismo equipo vs. mudar equipo difiere? | **No para R11.** Mover entre equipos de la misma disciplina NO crea nueva fila (actualiza `equipo_id`). R11 no se re-verifica en el move. Mismo equipo vs. diferente equipo no cambia R11. |
| ¿Cómo preservar historial sin duplicar? | Creando NUEVA fila `A` cuando no hay `A` existente. La `R` permanece como auditoría. |

### 6.2 Verificación del Escenario

El escenario reportado **NO es un bug** — es el comportamiento correcto:

1. Persona tiene participación `R` → histórico preservado ✅
2. Se agrega de nuevo → nueva fila `A` creada ✅
3. R11 solo verifica `A` → no bloquea porque `R` no cuenta ✅
4. Ahora tiene DOS filas: una `R` y una `A` → correcto ✅

### 6.3 Inconsistencia Visual del Presenter

**Sí existe**, pero es de UI, no de lógica de negocio:

- `jugadores_registrados` = cuenta solo `A` ✅
- `participantes[]` = incluye `A` y `R` ⚠️

**Recomendación:** Implementar **Opción D** — separar `participantes` (activos) de `historico` (retirados).

---

## 7. Casos de Borde

### 7.1 Mismo Equipo — Reingreso

1. Persona tiene `Participacion(equipo=X, disciplina=Futbol, estado=R)`
2. Se agrega de nuevo a equipo X (misma disciplina)
3. Se crea nueva `Participacion(equipo=X, disciplina=Futbol, estado=A)`
4. Ahora hay DOS filas: `R` y `A`
5. **R11 no bloquea** porque solo verifica `A`

**¿Debería bloquear?** Técnicamente R11 permite reingreso. Si el requerimiento es "una persona no puede entrar dos veces al mismo equipo aunque sea en momentos distintos", eso requiere lógica adicional.

### 7.2 Mismo Evento, Diferente Disciplina

1. Persona tiene `Participacion(disciplina=Futbol, estado=A)`
2. Se intenta agregar a `disciplina=Voley` del mismo evento
3. **R11 no bloquea** — diferente disciplina

**Correcto** según spec: R11 es por disciplina.

### 7.3 Mismo Evento, Diferente Inscripción

1. Persona tiene `Participacion(inscripcion=A, disciplina=Futbol, estado=A)`
2. Se intenta agregar a `inscripcion=B` del mismo evento, misma disciplina
3. **R11 BLOQUEA** — existe `A` para (evento, disciplina, persona)

**Correcto** según spec R11.

### 7.4 Cupo Pagado vs. No Pagado

1. Persona tiene `AsignacionCupo(estado=ACTIVA)` pagada
2. Se retira del equipo — `Participacion.estado=R` y `AsignacionCupo.estado=LIBERADA`
3. Cupo queda **LIBERADO** pero no destruido — disponible para reasignación
4. Se asigna a otra persona → nueva `AsignacionCupo(estado=ACTIVA)`

**Correcto** según F5: "El cupo liberado está disponible para reasignación."

### 7.5 Mismo Equipo — Mover Participación

1. Persona tiene `Participacion(equipo=A, disciplina=Futbol, estado=A)`
2. Se usa drag-drop para mover a equipo B (misma disciplina)
3. `_mover_atomico()` solo cambia `equipo_id` — no crea fila nueva
4. **No se verifica R11** porque no se llama `crear()`

**Observación:** Si la lógica de negocio requiere que mover entre equipos de la misma disciplina NO esté permitido (aunque no viole R11), habría que agregar esa validación explícitamente.

---

## 8. Matriz de Pruebas Sugeridas

| ID | Escenario | Resultado Esperado | Área |
|---|---|---|---|
| T-R01 | Agregar persona con participación `R` a SAME equipo/discIPLINA → nueva `A` creada | ✅ Permitido — R11 no blocks | ParticipacionCoreService |
| T-R02 | Agregar persona con participación `R` a DIFFERENT disciplina → nueva `A` creada | ✅ Permitido | ParticipacionCoreService |
| T-R03 | Agregar persona con participación `A` (misma disciplina) → error R11 | ✅ Bloqueado | ParticipacionCoreService |
| T-R04 | Mover participación entre equipos de misma disciplina → no se verifica R11 | ⚠️ Actual: permite sin verificar | ParticipacionOrchestrator |
| T-R05 | Verificar `participantes[]` incluye `R` pero `jugadores_registrados` no | ⚠️ Inconsistencia visual | InscripcionPresenter |
| T-R06 | Retirar persona → `AsignacionCupo` pasa a `LIBERADA` | ✅ Correcto | LiberarCupoFlujo |
| T-R07 | Reasignar cupo liberado a otra persona | ✅ Nueva `AsignacionCupo` creada | AsignacionOrchestrator |
| T-R08 | Admin bloquea fiesta → no se borra tras reingreso | ✅ Override preservado | AcreditacionCoreService |

---

## 9. Afectados

| Archivo | Por Qué |
|---|---|
| `backend/modules/salesianos_fest/domain/services/core/participacion_service.py` | R11 solo verifica `A` — correcto |
| `backend/modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py` | Crea nueva fila `A` tras `R` — correcto |
| `backend/modules/salesianos_fest/domain/services/orchestrators/participacion_orchestrator.py` | Mover no verifica R11 — podría necesitar validación adicional |
| `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py` | `participantes[]` incluye `R`, `jugadores_registrados` solo `A` — inconsistencia visual |
| `frontend/src/features/inscripciones/services/inscripcion.service.ts` | Tipo `EquipoDetalleOut` incluye `participantes[]` con ambos estados |

---

## 10. Riesgos

1. **Inconsistencia visual en frontend:** El array `participantes[]` incluye estados `A` y `R`, pero el conteo `jugadores_registrados` solo considera `A`. Puede confundir a admins.

2. **Mover entre equipos no verifica R11:** El flujo `_mover_atomico` no llama a `crear()`, por lo tanto R11 no se re-verifica. Si hay lógica de negocio que bloquee mover entre equipos de misma disciplina, no está implementada.

3. **Schema breaking change:** Si se implementa la Opción D (separar `historico`), requiere cambio en el schema de API y适配 frontend.

---

## 11. Próximo Paso Recomendado

**Sí, está listo para propuesta.** El siguiente paso es crear el artifact `proposal` con:

1. **Opción recomendada:** Opción D — separar `participantes` (activos) de `historico` (retirados)
2. **Cambio menor adicional:** Considerar agregar validación R11 en `_mover_atomico` para prevenir moves no deseados entre equipos de misma disciplina
3. **No requiere cambio en R11** — está correctamente implementado
4. **No requiere cambio en reingreso** — es el comportamiento correcto según spec

---

## 12. Referencias

- Spec FEST: `doc_dev/ESPECIFICACION_AGENT_IA_SALESIANOS_FEST_V1.md`
- Tablas y lógica: `doc_dev/DOCUMENTACION_LOGICA_Y_TABLAS_SALESIANOS_FEST.md`
- R11 constraint: `backend/modules/salesianos_fest/domain/models/participacion.py`
- R11 service: `backend/modules/salesianos_fest/domain/services/core/participacion_service.py:40-48`
- Presenter roster: `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py:74-79`
- Mover flow: `backend/modules/salesianos_fest/domain/services/orchestrators/participacion_orchestrator.py:60-86`
- Agregar persona: `backend/modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py`
- Liberar cupo: `backend/modules/salesianos_fest/domain/services/flujos/liberar_cupo_flujo.py`
- FEST spec T10, T13: Escenario de retiro y reingreso
