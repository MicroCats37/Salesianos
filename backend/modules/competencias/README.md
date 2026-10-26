# Módulo `competencias` — Cuadros eliminatorios

Módulo Django que administra los **cuadros eliminatorios de una jornada**:
una competencia agrupa `Evento + Disciplina + Categoria`, los equipos se
incorporan con **orden manual**, el cuadro se **escribe a mano** (nadie lo
genera) y los resultados se propagan al siguiente encuentro **confirmando**
una propuesta.

> Documento operativo del módulo: uso, despliegue por fases, rollback y gate
> de verificación. El contrato de arquitectura vive en `contract/`; este
> archivo no lo reemplaza.

---

## 1. Alcance (y lo que queda fuera)

| Dentro | Fuera (por diseño) |
|---|---|
| Competencias de una jornada (`Evento + Disciplina + Categoria + nombre`) | `Sede` / `Cancha` — el módulo **no** las conoce |
| Equipos, rondas, encuentros, horarios, resultados y correcciones | Round-robin, tablas de posiciones, claves de API |
| Auditoría completa (`django-simple-history`) con actor y motivo | Validación de género / roster (es una invariante de `modules.salesianos_fest`) |

Reglas que **no** son negociables:

- El sistema **nunca** inventa un participante, una ronda ni un bye.
- El bye lo decide **el administrador**: un encuentro con exactamente un
  participante, sin horario, sin marcador, `FINALIZADO`, con ese participante
  como ganador.
- El **ganador es autoritativo**: el marcador es informativo y nunca lo
  determina ni lo contradice.
- Toda mutación protegida exige **motivo auditado** (5..500 caracteres) y
  `expected_version` (bloqueo optimista).

---

## 2. Superficies HTTP

Prefijo de la API: `/api`. Los controllers son **async**; el cliente de
pruebas es `ninja_extra.testing.TestAsyncClient`.

### 2.1 Administrativa — con escrituras (`RequireAdmin`)

Prefijo: `/api/administracion/competencias`.

| Operación | Método | Ruta |
|---|---|---|
| Listar | `GET` | `/` |
| Crear | `POST` | `/` |
| Agenda de un día | `GET` | `/agenda` |
| Detalle | `GET` | `/{competencia_id}` |
| Actualizar | `PATCH` | `/{competencia_id}` |
| Estado | `PATCH` | `/{competencia_id}/estado` |
| Eliminar (borrador sin uso) | `DELETE` | `/{competencia_id}` |
| Cuadro | `GET` | `/{competencia_id}/cuadro` |
| Equipos | `GET` / `POST` | `/{competencia_id}/equipos` |
| Participación de un equipo | `PATCH` | `/{competencia_id}/equipos/{competencia_equipo_id}` |
| Rondas | `GET` / `POST` | `/{competencia_id}/rondas` |
| Ronda | `PATCH` | `/{competencia_id}/rondas/{ronda_id}` |
| Invalidar ronda | `PATCH` | `/{competencia_id}/rondas/{ronda_id}/estado` |
| Encuentros | `GET` / `POST` | `/{competencia_id}/encuentros` |

Prefijo: `/api/administracion/competencias/encuentros`.

| Operación | Método | Ruta |
|---|---|---|
| Mover participantes | `PATCH` | `/{encuentro_id}/participantes` |
| Programar | `PATCH` | `/{encuentro_id}/programacion` |
| Estado | `PATCH` | `/{encuentro_id}/estado` |
| Bye manual | `POST` | `/{encuentro_id}/bye` |
| Enlazar con el siguiente | `POST` | `/{encuentro_id}/enlace` |
| Quitar el enlace | `POST` | `/{encuentro_id}/desenlace` |
| Resultado | `POST` | `/{encuentro_id}/resultado` |
| Propuesta de avance | `POST` | `/{encuentro_id}/avance/preview` |
| Confirmar avance | `POST` | `/{encuentro_id}/avance/confirm` |
| Impacto de la corrección | `POST` | `/{encuentro_id}/correccion/preview` |
| Confirmar corrección | `POST` | `/{encuentro_id}/correccion/confirm` |
| Eliminar (borrador sin uso) | `DELETE` | `/{encuentro_id}` |

### 2.2 Pública — solo lectura

Prefijo: `/api/competencias`. **No expone ninguna escritura.**

| Operación | Método | Ruta |
|---|---|---|
| Listar | `GET` | `/` |
| Encuentros | `GET` | `/encuentros` |
| Detalle | `GET` | `/{competencia_id}` |
| Cuadro | `GET` | `/{competencia_id}/cuadro` |

El alcance lo resuelve **el servidor** (ediciones activas). Un recurso fuera
del alcance se responde con `404 COMPETENCIA_NOT_FOUND`: la superficie nunca
confirma la existencia de algo que el lector no puede ver.

### 2.3 Frontend

| Ruta | Contenido |
|---|---|
| `/administracion/competencias` | Listado con filtros en la URL |
| `/administracion/competencias/[id]` | Detalle + editores |
| `/administracion/competencias/cuadro` | Cuadro por rondas (responsive) |
| `/administracion/competencias/agenda` | Agenda de **un** día |

La lógica vive en `frontend/src/features/admin/competencias/`
(schemas Zod ↔ backend, services, hooks TanStack Query, editores y diálogos).

---

## 3. Uso operativo

1. **Crear la competencia** — `POST /administracion/competencias` con
   `evento_id`, `disciplina_id`, `categoria_id`, `nombre` y `fecha`. La
   identidad (`evento + disciplina + categoria + nombre`, sin distinguir
   mayúsculas) es única y la fecha debe caer dentro del evento.
2. **Incorporar los equipos** — `POST /{id}/equipos` con `equipo_id` y
   `orden`. El orden es **manual**: el sistema no siembra nada. Un equipo
   inactivo, de otro evento, de otra disciplina o de otra categoría se
   rechaza con `409 EQUIPO_NO_ELEGIBLE`.
3. **Crear las rondas** — `POST /{id}/rondas` con `etiqueta` y `orden`
   (ambos únicos dentro de la competencia).
4. **Crear los encuentros** — `POST /{id}/encuentros` con `ronda_id`,
   `orden` y los participantes **opcionales**: un cuadro vacío o parcial es
   un cuadro válido.
5. **Asignar los byes a mano** — `POST /encuentros/{id}/bye` sobre el
   encuentro que tiene un solo participante.
6. **Programar** — `PATCH /encuentros/{id}/programacion` con un intervalo
   positivo **dentro del día de la competencia**. Dos encuentros que se
   tocan no se solapan (`[inicio, fin)`); el mismo equipo no puede jugar dos
   veces a la vez, ni siquiera en otra competencia del evento.
7. **Enlazar con la siguiente ronda** — `POST /encuentros/{id}/enlace` con
   el encuentro destino y el slot (`PARTICIPANTE_1` / `PARTICIPANTE_2`). El
   enlace siempre apunta **hacia adelante**.
8. **Registrar el resultado** — `POST /encuentros/{id}/resultado`. El
   ganador debe ocupar uno de los slots (`422 INVALID_WINNER` si no).
9. **Propagar el ganador** — `POST /encuentros/{id}/avance/preview` (no
   escribe) y luego `POST /encuentros/{id}/avance/confirm`. La propagación
   coloca al ganador **una sola vez** y deja registro (`ganador_propagado`).
10. **Corregir un resultado** — `POST /encuentros/{id}/correccion/preview`
    para ver el impacto y `POST /encuentros/{id}/correccion/confirm` para
    aplicarla. Si un descendiente ya **comenzó**, **finalizó** o fue
    **cancelado**, la corrección **no** cambia nada sin `override=true` **y**
    `acepta_impacto=true` **y** un motivo: nunca hay cascada silenciosa.

### 3.1 Concurrencia e idempotencia

- Dos administradores que editan la **misma** versión: sólo se aplica la
  primera; la segunda recibe `409 RESOURCE_CHANGED` **sin efectos parciales**.
- Un comando repetido **con la misma intención** es idempotente: responde
  `200` y no escribe (ni sube la versión).
- Las mutaciones protegidas sin `expected_version` válido fallan antes de
  escribir.

### 3.2 Eliminación y cancelación

| Situación | Resultado |
|---|---|
| Borrador sin participantes, sin horario, sin enlaces ni historial posterior | Se **borra** físicamente (`204`) |
| Cualquier recurso en uso | `409 DELETE_NOT_ALLOWED`: se **cancela** o se **invalida** y se conserva la historia |

---

## 4. Catálogo público de errores

Los mensajes públicos salen **sólo** de `backend/core/exceptions.py`; nunca
exponen UUIDs, ids internos, constraints SQL ni texto crudo de excepción.

| Estado | Códigos |
|---|---|
| `404` | `COMPETENCIA_NOT_FOUND`, `RONDA_NOT_FOUND`, `ENCUENTRO_NOT_FOUND`, `COMPETENCIA_EQUIPO_NOT_FOUND` |
| `409` | `COMPETENCIA_DUPLICADA`, `EQUIPO_NO_ELEGIBLE`, `EQUIPO_SOLAPADO`, `SLOT_OCUPADO`, `DESTINO_BLOQUEADO`, `INVALID_STATE_TRANSITION`, `DELETE_NOT_ALLOWED`, `RESOURCE_CHANGED` |
| `422` | `INVALID_SCHEDULE`, `INVALID_WINNER`, `INVALID_LINK`, `REASON_REQUIRED` |
| `401` / `403` | `AUTHENTICATION_REQUIRED` / `ACTION_NOT_ALLOWED` (superficie administrativa) |

---

## 5. Despliegue por fases

La migración inicial (`competencias.0001_initial`) crea **cuatro tablas
vivas** (`competencias`, `competencia_equipos`, `rondas`, `encuentros`) y
**cuatro históricas**, sin *backfill*. Las fases se activan **en este
orden**; no se adelanta ninguna:

| Fase | Qué se activa | Cómo se activa | Señal de que está bien |
|---|---|---|---|
| **0. Esquema** | Las tablas y el historial | `manage.py migrate` | `migrate` sin errores; `makemigrations --check` sin drift |
| **1. Rutas ocultas** | Los endpoints, sin navegación | Desplegar el código; **no** agrega la entrada al menú | `/api/docs` lista los endpoints; nadie los conoce todavía |
| **2. Administración planificada** | El menú `/administracion/competencias` y la creación de competencias y cuadros | Agregar la entrada de navegación | El administrador crea una competencia de prueba con equipos y rondas |
| **3. Resultados y avance** | Resultado, avance y corrección | Habilitar los editores de la fase 3 | Un cuadro completo se propaga de punta a punta |
| **4. Lectura pública** | `GET /api/competencias*` | Publicar la superficie pública | Un lector anónimo ve el cuadro de la edición activa |

En la fase 1 el módulo se despliega **sin** que nadie pueda escribir desde la
interfaz: las escrituras existen en la API pero no hay pantalla que las
invoque.

---

## 6. Rollback

El rollback tiene **dos** destinos según el uso que tuvo el módulo.

### 6.1 Antes de usar el módulo (fases 0–1)

Se **revierte la migración**:

```bash
docker exec -it salesianos_backend uv run python manage.py migrate competencias zero
```

No hay datos que preservar: nadie escribió nada.

### 6.2 Después de usar el módulo (fases 2–4)

**No se borra nada.** El rollback operativo es:

- [ ] **Deshabilitar las escrituras**: retirar los controllers del registro de
      la API (`backend/config/api.py`) o poner la superficie administrativa en
      solo lectura. Los datos quedan legibles.
- [ ] **Retirar la navegación** de `/administracion/competencias` y de los
      accesos de la interfaz que la enlacen.
- [ ] **Cancelar** las competencias en uso (`PATCH /{id}/estado` con
      `CANCELADA`): es terminal y auditable, y deja el historial intacto.
- [ ] **Mantener las tablas en solo lectura**: la superficie pública de
      lectura (`GET /api/competencias*`) puede seguir activa si conviene, o
      se apaga también; en ningún caso se borran las tablas ni el historial.
- [ ] **No** ejecutar `migrate competencias zero` con datos: la API responde
      `409 DELETE_NOT_ALLOWED` ante el borrado físico de un recurso en uso, y
      esa protección es la garantía de que la historia no se pierde.

Ningún dato histórico se elimina en un rollback: las tablas
`competencias_historical*` conservan el antes y el después de cada cambio
(actor, motivo y fecha).

---

## 7. Verificación

```bash
# Backend — suite del módulo (unit-free: sólo integration + e2e)
cd backend && python -m pytest modules/competencias/tests -q

# Backend — sólo la suite E2E (flujo HTTP completo)
cd backend && python -m pytest modules/competencias/tests/e2e -q

# Backend — chequeos de Django
cd backend && python manage.py check
cd backend && python manage.py makemigrations --check --dry-run

# Frontend — pruebas, tipos, lint del alcance y build
cd frontend && npx vitest run src/features/admin/competencias
cd frontend && npx tsc --noEmit
cd frontend && npx biome check src/features/admin/competencias
cd frontend && npm run build
```

### 7.1 Gate externo: PostgreSQL

La suite corre en **SQLite** (en memoria). La portabilidad del esquema a
PostgreSQL está cubierta **sin servidor**: `tests/integration/
test_migraciones_portabilidad.py` renderiza el DDL de la migración inicial con
el *schema editor* de PostgreSQL en modo `collect_sql` (sin abrir socket) y lo
compara con el de SQLite.

**La verificación contra un PostgreSQL real es un gate de release externo y
no se puede dar por cumplida con la suite local.** Antes de producción:

- [ ] Levantar PostgreSQL 16 (`docker compose up -d db`) y apuntar las
      variables `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT`.
- [ ] `manage.py migrate` sobre esa base (crea las 4 tablas vivas y las 4
      históricas).
- [ ] `manage.py makemigrations --check --dry-run` → sin drift.
- [ ] `python -m pytest modules/competencias/tests -q` contra PostgreSQL
      (con `USE_SQLITE` **desactivado**).
- [ ] `manage.py check` y la prueba de portabilidad del DDL en verde.

Sin ese gate, el despliegue en producción **no** está aprobado.

---

## 8. Archivos

| Ruta | Contenido |
|---|---|
| `domain/models/` | `Competencia`, `CompetenciaEquipo`, `Ronda`, `Encuentro` (+ historial) |
| `domain/services/core/` | Reglas de negocio (síncronas, sin `transaction.atomic`) |
| `domain/services/flujos/` | Flujos async: son los que abren la transacción y los bloqueos |
| `domain/services/orchestrators/` | Fachadas async delgadas (una por endpoint) |
| `domain/selectors/` | Consultas de lectura (competencias, encuentros, alcance) |
| `presentation/schemas/` | Schemas HTTP (`BaseSchema`, compuestos por bloques) |
| `presentation/presenters/` | Transformadores puros resultado → schema |
| `presentation/controllers/` | Controllers async: sin `if`, sin ORM, sin errores manuales |
| `migrations/0001_initial.py` | Esquema inicial (4 tablas + 4 históricas) |
| `tests/integration/` | Reglas, flujos, API y portabilidad |
| `tests/e2e/` | Flujo HTTP completo: cuadros de 3/5/6/7/8, byes, concurrencia, autorización y rollback |
