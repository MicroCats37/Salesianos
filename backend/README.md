# Backend - Salesianos FEST 2026

Este es el backend del proyecto, construido con **Django**, **Django Ninja Extra** y empaquetado con **uv**.

El proyecto completo corre con Docker Compose (`salesianos_backend`).

## Inicialización y Seeds (Datos base)

Para inicializar el sistema desde cero (por ejemplo, después de montar la base de datos por primera vez), es necesario cargar los datos base (seeds).

Todos los comandos se ejecutan **dentro del contenedor** usando `docker exec`.

### 1. Crear el Administrador

Crea el usuario superadmin (`username: admin`, `password: admin`, vinculado a un DNI de sistema `00000000`).

```bash
docker exec -it salesianos_backend uv run python manage.py create_admin
```

> **Nota:** Si la contraseña fue cambiada y querés resetearla al valor por defecto, podés usar el flag `--force`:
> `docker exec -it salesianos_backend uv run python manage.py create_admin --force`

### 2. Cargar Promociones y Paquetes (Precios)

Este comando carga automáticamente toda la estructura base para que las inscripciones funcionen:
- **Promociones** (Años de egreso: 1970 a 2026).
- **Disciplinas** y **Categorías** (Fulbito, Vóley, Básquet, Súper Máster, etc.).
- **Paquetes y Precios** (Deportistas, Delegados, con sus respectivos precios regulares y promocionales).
- **El Evento Principal** ("Salesianos FEST 2026").

```bash
docker exec -it salesianos_backend uv run python manage.py seed_inscripciones
```

> **Nota:** Ambos comandos son **idempotentes**. Esto significa que si los ejecutás más de una vez, no van a duplicar datos, solo van a actualizar los existentes si algo cambió.

## Migraciones

Si hacés cambios en los modelos y necesitás correr las migraciones en Docker:

```bash
# Para aplicar las migraciones
docker exec -it salesianos_backend uv run python manage.py migrate

# Para crear nuevas migraciones (si desarrollás)
docker exec -it salesianos_backend uv run python manage.py makemigrations
```

## Compatibilidad género / modalidad de la disciplina

Una persona sólo puede tener una participación **ACTIVA** en una disciplina cuya `modalidad` admita su `genero` persistido.

| Género \ Modalidad | `M` (Masculino) | `F` (Femenino) | `X` (Mixto) |
|---|---|---|---|
| `M` (Masculino) | ✅ | ❌ | ✅ |
| `F` (Femenino) | ❌ | ✅ | ✅ |

- **Un solo dueño de la regla**: `modules/salesianos_fest/domain/validators/participacion.py` (`es_genero_compatible_con_modalidad`). La auditoría, el servicio de escritura, `Participacion.clean()` y los formularios del admin la llaman; nadie mantiene una copia privada.
- **Falla cerrada**: cualquier par fuera de la lista —incluido un género o una modalidad desconocidos— se rechaza.
- **Modalidad `X` (Mixto)**: acepta cualquier género (`M` y `F`) de forma independiente. Hoy **no** exige una composición mínima mixta (aún no existe el cierre de nóminas de equipo); ese requisito queda diferido.
- **Sólo aplica al estado `ACTIVA`.** Retirar o desactivar (`A` → `R`) nunca se bloquea, y el historial inactivo nunca bloquea una edición.
- **Sin migración**: el cambio no agrega ni altera campos, tablas, constraints ni datos.

### 1. Auditoría (solo lectura) — obligatoria antes de activar la validación

Comando exacto (desde el contenedor):

```bash
# Todas las ediciones
docker exec -it salesianos_backend uv run python manage.py auditar_genero_disciplinas

# Una edición concreta
docker exec -it salesianos_backend uv run python manage.py auditar_genero_disciplinas --evento-id <uuid>
```

Salida determinista, un registro por línea:

```
VIOLATION|<evento_id>|<participacion_id>|<persona_id>|<genero>|<disciplina_id>|<modalidad>
SUMMARY|scanned=<n>|violations=<n>
```

| Código de salida | Significado |
|---|---|
| `0` | El alcance auditado **no** tiene violaciones. |
| `1` | Hay violaciones (`CommandError`) **o** el `--evento-id` es inválido o no existe. |

Las filas se ordenan por `(evento_id, participacion_id)`, así que dos corridas sobre la misma base producen la misma salida. El comando **nunca escribe**: el SHA-256 de la base y su `mtime` quedan idénticos antes y después.

### 2. Remediación

Cada fila `VIOLATION` se resuelve por una de estas vías (las tres funcionan con la validación ya activa):

| Vía | Qué hacer | Restricción |
|---|---|---|
| **A** | Cambiar la `modalidad` de la disciplina a `X` (Mixto). | Siempre permitido: `X` admite a todos. Resuelve de una vez todas las violaciones de esa disciplina. |
| **B** | Retirar la participación (`A` → `R`). | Siempre permitido. Sólo corresponde si la persona ya no participa. Para reactivarla (`R` → `A`) hay que aplicar la vía A antes, o moverla a una disciplina compatible. |
| **C** | Mover la persona a una disciplina compatible con su género. | El destino debe ser compatible; un destino incompatible se rechaza con `409`. |

Las guardas del admin bloquean los cambios que romperían una participación activa: cambiar `Persona.genero` o `Disciplina.modalidad` hacia una modalidad incompatible se rechaza y **el valor original se conserva**. Reintentar con `X` (Mixto) nunca falla.

### 3. Secuencia de despliegue

1. **Auditoría sin validación** — desplegar el comando de auditoría (y sólo eso). No requiere migración.
2. **Correr la auditoría en producción** con el comando exacto de la sección 1 y archivar la salida.
3. **Remediar todas las violaciones** reportadas (sección 2).
4. **Re-correr la auditoría** → debe terminar con `violations=0` y código de salida `0`.
5. **Registrar la aprobación** de la sección 6.
6. **Activar la validación** — desplegar el enforcement del ciclo de vida, las guardas del admin y el aviso en la UI. Sin migración en ningún paso.

### 4. Rollback

El rollback **desactiva la validación y conserva la auditoría**:

- [ ] Desactivar el enforcement del ciclo de vida (alta, traslado y reactivación) en `domain/services/core/participacion_service.py`.
- [ ] Desactivar la guarda del modelo `Participacion.clean()` en `domain/models/participacion.py`.
- [ ] Desactivar las guardas de edición del admin (`modules/salesianos_fest/forms.py` y `modules/usuarios/forms.py`).
- [ ] Desactivar el aviso en la UI (dejar de aplicar el predicado en `domain/selectors/inscripcion_selector.py`).
- [ ] **Conservar** el comando `auditar_genero_disciplinas`: es la única herramienta de diagnóstico y siempre es seguro ejecutarlo.

No hay rollback de datos: la auditoría no escribe y la validación no altera el esquema. El mapeo público `409 / GENERO_NO_PERMITIDO` puede mantenerse: sólo responde a operaciones que ya se están rechazando.

### 5. Comportamiento público (`409`)

Cuando una operación de API crearía una incompatibilidad activa:

| Campo | Valor |
|---|---|
| Estado HTTP | `409` |
| `error.code` | `GENERO_NO_PERMITIDO` |
| Mensaje público | `La disciplina seleccionada no es compatible con el género de la persona.` |

El mensaje es texto fijo del catálogo `PUBLIC_ERROR_MESSAGES` de `core/exceptions.py`: **no** expone UUIDs, IDs, nombres, documentos ni los códigos concretos de género o modalidad. El detalle técnico queda en los logs del servidor.

El frontend es **advisory**, no autoritativo: el selector de participantes deja de ofrecer los candidatos incompatibles y muestra el motivo del backend, pero un envío directo sigue siendo rechazado por el backend con `409`.

### 6. Aprobación de producción (gate)

> **La validación no se activa en producción hasta que esta lista esté completa y firmada.** La auditoría de desarrollo no alcanza como sustituto: hay que correrla sobre la base de producción.

- [ ] Auditoría de producción ejecutada con el comando exacto (sección 1).
- [ ] Salida archivada: `SUMMARY|scanned=<n>|violations=0` y código de salida `0`.
- [ ] Todas las violaciones de la primera corrida remediadas y verificadas una por una.
- [ ] Segunda corrida de la auditoría: `violations=0`, código de salida `0`.
- [ ] Despliegue de enforcement, guardas de admin y aviso en la UI habilitado **después** de esta aprobación.

| Campo | Valor |
|---|---|
| Fecha de la auditoría | `YYYY-MM-DD` |
| Alcance (ediciones auditadas) | `evento_id` / todas |
| `scanned` / `violations` | `N` / `N` |
| Revisado por | `nombre` |
| Aprobado por | `nombre` |

---

## Módulo de competencias (cuadros eliminatorios)

El módulo `modules.competencias` administra los cuadros eliminatorios de una
jornada: competencias, equipos, rondas, encuentros, horarios, resultados y
correcciones auditadas. Tiene **dos superficies**: la administrativa (con
escrituras, `RequireAdmin`) y la pública (solo lectura, limitada a las
ediciones activas).

El documento operativo completo —superficies HTTP, uso del administrador,
despliegue por fases, rollback y gate de verificación— está en
[`modules/competencias/README.md`](./modules/competencias/README.md).

### Secuencia de despliegue

1. **Esquema** — `manage.py migrate` (4 tablas vivas + 4 históricas, sin
   backfill). Rutas **ocultas**: sin navegación.
2. **Administración planificada** — se agrega la entrada
   `/administracion/competencias` y se prueban competencias y cuadros.
3. **Resultados y avance** — se habilitan resultado, avance y corrección.
4. **Lectura pública** — se publica `GET /api/competencias*`.

### Rollback

- **Antes de usar el módulo**: `manage.py migrate competencias zero`.
- **Después de usar el módulo**: **no se borra nada**. Se deshabilitan las
  escrituras y la navegación, se cancelan las competencias en uso
  (`CANCELADA`, terminal y auditable) y las tablas quedan en **solo lectura**.
  La API responde `409 DELETE_NOT_ALLOWED` ante el borrado físico de un
  recurso en uso: esa es la garantía de que la historia no se pierde.

### Gate de verificación (PostgreSQL)

La suite local corre en SQLite. La portabilidad del esquema a PostgreSQL está
cubierta sin servidor (DDL renderizado en modo `collect_sql`), pero la
**verificación contra un PostgreSQL real es un gate de release externo**: hay
que correr `migrate`, `makemigrations --check --dry-run`, `manage.py check` y
la suite del módulo contra esa base antes de producción. El detalle está en
la sección 7.1 del README del módulo.
