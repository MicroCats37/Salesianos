# Administración Operativa FEST

Documento operativo del área `/administracion`: qué se puede consultar, con
qué filtros, quién puede hacerlo y qué límites tiene el MVP.

- **Backend**: `backend/modules/administracion/` (módulo Django sin modelos ni
  migraciones, solo lectura).
- **Frontend**: `frontend/src/features/admin/` + `frontend/src/app/(app)/administracion/`.
- **Alcance del MVP**: estrictamente **read-only**. La superficie no escribe.

---

## 1. Roles y autorización

| Regla | Valor |
|---|---|
| Quién es administrador | `is_staff OR is_superuser`, evaluado **en el servidor** en cada request. |
| Enforcement | `RequireAdmin` (`backend/core/permissions.py`) en todos los controllers de `/administracion`. |
| Anónimo | `401` · `AUTHENTICATION_REQUIRED` (el JWT corre primero). |
| Autenticado no administrador | `403` · `ACTION_NOT_ALLOWED`. |
| Administrador | `200`. |
| `is_superuser` | Nivel de emergencia. No se muestra, no se asigna ni se degrada desde esta interfaz. |
| Guard del frontend | **Solo orientativo**: `app/(app)/administracion/layout.tsx` llama a `GET /api/auth/me` y redirige. La cookie `USER_SESSION` **no** es autoridad: la única bandera es `es_admin`, calculada por el backend con la misma regla. |
| Sesión frontend | Un `403` en cualquier endpoint admin muestra "Acceso denegado", limpia la sesión y vuelve a `/dashboard`. Un `401` limpia la sesión y vuelve a `/login`. |

La Flag `es_admin` de `/api/auth/me` y el permiso `RequireAdmin` del backend
comparten **la misma regla**: `is_staff OR is_superuser`. No hay dos verdades.

---

## 2. Alcance del evento

Toda la superficie opera sobre **la edición activa**, resuelta **en el servidor**
a partir de `settings.EVENTO_ACTIVO_NOMBRE` (si no, la edición activa más
reciente). El cliente **nunca** envía `evento_id`.

- Las listas de la A3 a la A12 están acotadas a la edición activa.
- Un id de otra edición responde `404` · `RESOURCE_NOT_FOUND`, igual que un id
  inexistente: la superficie nunca confirma la existencia de un recurso fuera
  de su alcance.
- **Excepción documentada**: las cuentas (A13/A14) son identidades globales, no
  filas de una edición. El listado de cuentas no se acota al evento; las
  inscripciones que muestra el detalle (A14) **sí** están acotadas al evento
  activo.
- Si no hay edición activa: `404` · `EVENTO_ACTIVO_NO_ENCONTRADO`.

---

## 3. Endpoints (A1–A14)

Prefijo: `/api/administracion`. Todos son **GET**.

| # | Endpoint | Respuesta | Notas |
|---|---|---|---|
| A1 | `GET /resumen` | `AdminResumenOut` | Los ocho bloques métricos: evento, inscripciones, pagos, cupos, equipos, participantes, acreditaciones, accesos. |
| A2 | `GET /catalogos` | `AdminCatalogosOut` | Opciones de filtro: disciplinas, paquetes, promociones, categorías, puntos de acceso y vocabularios de estado. |
| A3 | `GET /inscripciones` | `PaginatedData[AdminInscripcionListItemOut]` | Listado de inscripciones. |
| A4 | `GET /inscripciones/{inscripcion_id}` | `AdminInscripcionDetailOut` | Detalle con seis bloques: equipos (con plantilla), participantes, compras, asignaciones, aceptaciones y saldo. |
| A5 | `GET /pagos` | `PaginatedData[AdminPagoListItemOut]` | Compras y su orden de pago. Montos desde el **snapshot congelado** de la línea de compra. |
| A6 | `GET /pagos/{orden_pago_id}` | `AdminPagoDetailOut` | Orden con sus intentos de pago (campos explícitos, sin internos del proveedor). |
| A7 | `GET /equipos` | `PaginatedData[AdminEquipoListItemOut]` | Equipos con su estado de plantilla **derivado** en el servidor. |
| A8 | `GET /participantes` | `PaginatedData[AdminParticipanteListItemOut]` | Personas registradas (el *pool*). Estado de pool derivado, nunca persistido. |
| A9 | `GET /participaciones` | `PaginatedData[AdminParticipacionListItemOut]` | Filas de plantilla por disciplina. **No es lo mismo que A8.** |
| A10 | `GET /acreditaciones` | `PaginatedData[AdminAcreditacionListItemOut]` | Acreditaciones. Nunca expone `codigo_qr`. |
| A11 | `GET /acreditaciones/{acreditacion_id}` | `AdminAcreditacionDetailOut` | Detalle con su registro de accesos. Nunca expone `codigo_qr`. |
| A12 | `GET /accesos` | `PaginatedData[AdminAccesoListItemOut]` | Registro de accesos. Por defecto, más recientes primero. |
| A13 | `GET /usuarios` | `PaginatedData[AdminUsuarioListItemOut]` | Cuentas globales. Nunca expone contraseña, hash, token ni `is_superuser`. |
| A14 | `GET /usuarios/{usuario_id}` | `AdminUsuarioDetailOut` | Cuenta con las inscripciones que posee **dentro del evento activo**. |

Existe además `GET /health` (sonda del módulo: estado y edición activa), usada
para verificar el registro de la app y el cableado de DI. No expone datos de
negocio.

### 3.1 Personas ≠ participaciones

Un cupo pagado habilita a una persona en **todas** las disciplinas contratadas.
Por eso `personas` y `participaciones` son dos cifras distintas, y la tabla de
inscripciones las muestra en **dos columnas distintas**. El cliente nunca las
reconcilia ni recalcula ninguna: todas las cifras las calcula el backend.

### 3.2 Filtros por endpoint

| Endpoint | Filtros |
|---|---|
| A3 | `estado` (8 estados de inscripción), `paquete_id`, `promocion_id`, `responsable_persona_id`, `q` |
| A5 | `estado_compra`, `estado_orden`, `tipo` (`INICIAL`/`AMPLIACION`), `desde`, `hasta`, `q` |
| A7 | `inscripcion_id`, `disciplina_id`, `estado`, `roster` (`COMPLETO`/`INCOMPLETO`), `q` |
| A8 | `estado_pool` (`LISTO`, `ESPERANDO_PAGO`, `SIN_CAPACIDAD`, `CUPO_POR_ASIGNAR`), `disciplina_id`, `con_cupo`, `q` |
| A9 | `disciplina_id`, `rol` (`J`/`C`/`D`), `estado` (`A`/`R`), `inscripcion_id`, `q` |
| A10 | `estado`, `autorizacion_fiesta` (`AUTOMATICA`/`AUTORIZADA`/`BLOQUEADA`), `acceso_fiesta`, `q` |
| A12 | `resultado` (`PERMITIDO`/`DENEGADO`), `punto_acceso`, `desde`, `hasta`, `q` |
| A13 | `estado` (`activo`/`inactivo`), `es_admin`, `q` |

Reglas comunes:

- Los filtros se combinan con **AND**.
- Un valor fuera del vocabulario → `422` · `INVALID_REQUEST` (nunca un 500 ni
  un filtro silencioso).
- Un UUID mal formado → `422`. Un UUID bien formado que no existe → lista
  **vacía** (no es un error).
- `desde` / `hasta` son fechas ISO `YYYY-MM-DD`. Aplican a la fecha de
  creación de la fila (A5) y a la fecha del acceso (A12).
- `q` es texto libre sobre los campos **documentados** de cada recurso, con
  un tope de 120 caracteres. Los metacaracteres SQL son seguros.

### 3.3 Contrato canónico de paginación y orden

| Parámetro | Por defecto | Regla |
|---|---|---|
| `page` | 1 | Base 1; los valores menores se recortan a 1. |
| `page_size` | 25 | Máximo 100. Un valor **superior** se recorta, **no** es un error. |
| `q` | — | Texto libre, recortado y con espacios colapsados, tope de 120 caracteres. |
| `ordering` | por recurso | **Lista blanca del servidor**, formato `campo` / `-campo`. Un valor desconocido → `422` · `INVALID_REQUEST`. |

El cliente envía un **nombre público de campo**; el servidor lo traduce a la
expresión ORM autorizada. El texto crudo del cliente **nunca** se interpola en
un queryset.

Campos permitidos por recurso:

| Endpoint | Campos |
|---|---|
| A3 | `created_at`, `estado`, `responsable`, `paquete` |
| A5 | `created_at`, `total`, `cantidad`, `estado_compra`, `estado_orden`, `pagada_en` |
| A7 | `created_at`, `nombre`, `disciplina`, `estado` |
| A8 | `created_at`, `persona`, `estado` |
| A9 | `created_at`, `persona`, `equipo`, `disciplina`, `rol`, `estado` |
| A10 | `persona`, `estado`, `autorizacion_fiesta` |
| A12 | `fecha_hora`, `resultado`, `punto_acceso` |
| A13 | `created_at`, `username`, `nombres`, `last_login` |

La respuesta de toda lista tiene la misma forma canónica
(`core/pagination.py::PaginatedData`):

```json
{ "items": [], "total": 0, "page": 1, "page_size": 25, "total_pages": 0 }
```

Una página fuera de rango responde `items: []` con `200` — nunca `404`.

---

## 4. Límites del MVP (read-only)

**No existe** en esta superficie:

| Fuera del MVP | Dónde vive hoy |
|---|---|
| Exportación CSV / PDF | — |
| Acciones masivas (override de fiesta, re-emisión de QR, cambio de estado en lote) | — |
| Mutaciones privilegiadas (validar/rechazar inscripción, revocar cupo, cancelar compra, cambiar rol o estado de una cuenta) | Fase siguiente, en los módulos de negocio que las poseen |
| Gestión de contraseñas de cualquier tipo | Django admin |
| Gráficos más allá de los tiles de KPI; timeline de actividad; notificaciones; delegación de administración; selector multi-edición | — |
| Tablas de negocio nuevas o migraciones | — |

La superficie realiza **cero escrituras**: el módulo `modules/administracion`
no registra ninguna ruta `POST`/`PUT`/`PATCH`/`DELETE` bajo
`/api/administracion`, y una prueba lo verifica sobre el esquema OpenAPI y
sobre las peticiones reales.

> **Excepción por módulo:** `/api/administracion/competencias*` **sí** declara
> escrituras — pertenece al módulo `competencias`, no a este. La afirmación de
> cero escrituras aplica a las rutas A1–A14 y a `/health` de este módulo
> (ver la sección 7).

### 4.1 Gestión de contraseñas: explícitamente excluida

- La interfaz **no** crea, cambia, restablece ni permite leer contraseñas.
- El listado de cuentas (A13) **nunca** expone `password`, `password_hash`
  ni ningún token.
- El restablecimiento de contraseña queda en el **Django admin**.
- `is_superuser` no se expone ni se puede asignar o degradar desde aquí.
- **Deuda conocida**: `token_blacklist` está instalado pero no se usa; la
  revocación de tokens al desactivar una cuenta es trabajo aparte.

### 4.2 Fronteras de QR y secretos de pago

- **QR**: `codigo_qr` **nunca** aparece en A10 ni en A11. El QR vivo es una
  credencial portadora y solo se entrega por la acción explícita de generación
  del módulo propietario, con su propia autorización.
- **Pagos**: A5 y A6 **nunca** exponen `metadata`, `token_sesion`,
  `transaction_id` ni `response_message`. Los intentos de pago (A6) declaran
  campos explícitos: `id`, `status`, `amount`, `currency`, `metodo_pago`,
  `response_code`, `created_at`.
- La respuesta pública **nunca** contiene UUIDs internos, IDs de base de datos,
  request ids, trazas, rutas, constraints SQL, textos crudos de excepción ni
  secretos. Los errores salen del catálogo público de
  `backend/core/exceptions.py`.

---

## 5. Rutas del frontend

| Ruta | Contenido |
|---|---|
| `/administracion` | Overview: tiles de KPI y listas de atención (A1, A2). |
| `/administracion/inscripciones` | Listado de inscripciones (A3). |
| `/administracion/inscripciones/[id]` | Detalle de inscripción con seis tabs (A4). |
| `/administracion/pagos` | Pagos (A5) con panel de detalle (A6). |
| `/administracion/equipos` | Equipos (A7). |
| `/administracion/participantes` | Personas registradas (A8) y participaciones por disciplina (A9). |
| `/administracion/acreditaciones` | Acreditaciones (A10) con detalle (A11) y registro de accesos (A12). |
| `/administracion/usuarios` | Cuentas (A13) con panel de detalle (A14). |

El estado de cada lista vive en la **URL** (página, tamaño, término, orden y
filtros), así la vista es compartible. Las páginas con dos listas usan un
prefijo por tab (`participantes_*`, `participaciones_*`, `acreditaciones_*`,
`accesos_*`): el filtro de una tab **nunca** viaja al endpoint de la otra
—que lo rechazaría con `422`— y cambiar una tab no borra el estado de la otra.

Estados obligatorios en cada tabla: cargando (skeleton), error inline con
"Reintentar", vacío, vacío filtrado ("Limpiar filtros") y `403`.

---

## 6. Verificación

```bash
# Backend — suite de la administración
cd backend && python -m pytest modules/administracion/tests -q

# Backend — suite completa (la deuda preexistente está aparte)
cd backend && python -m pytest -q --ignore=scripts

# Backend — chequeos de Django
cd backend && DJANGO_SETTINGS_MODULE=config.settings.development python manage.py check
cd backend && DJANGO_SETTINGS_MODULE=config.settings.development python manage.py makemigrations --check --dry-run

# Frontend — pruebas unitarias del área
cd frontend && node --experimental-strip-types --test "src/features/admin/utils/*.test.ts" "src/features/admin/schemas/*.test.ts"

# Frontend — tipos, lint del alcance y build
cd frontend && npx tsc --noEmit
cd frontend && npx biome check src/features/admin "src/app/(app)/administracion"
cd frontend && npm run build
```

La matriz de verificación A1–A14 (ruta, autorización, filtros, orden,
paginación, alcance de evento, cero escrituras y ausencia de secretos) vive en
`backend/modules/administracion/tests/integration/test_admin_matriz_a1_a14.py`.

---

## 7. Nota: el módulo `competencias` tiene su propia superficie

Este documento cubre **sólo** el módulo `modules/administracion`, que es
read-only y **no escribe**. Los **cuadros eliminatorios** viven en un módulo
distinto (`modules.competencias`) con **escrituras administrativas**
(`/api/administracion/competencias*`) y una **superficie pública de solo
lectura** (`/api/competencias*`).

Su contrato operativo —superficies, uso, despliegue por fases, rollback en
solo lectura y gate de PostgreSQL— está en
[`backend/modules/competencias/README.md`](../backend/modules/competencias/README.md).
