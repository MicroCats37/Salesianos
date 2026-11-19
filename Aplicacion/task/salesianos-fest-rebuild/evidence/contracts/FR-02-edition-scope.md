# FR-02 — Scope de edición (reemplazo del evento activo global)

**Freeze:** `FREEZE-ED-1.0.0` · **Propietario:** A0 (config) + A1 (módulo `eventos`) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `RN-E01`, `RN-E02` · `DEC-01` · `FL-01` · plan `funcional/01` §1, `funcional/03` §1, `implementacion/01` §5

---

## 1. El supuesto que este freeze elimina

`EVENTO_ACTIVO_NOMBRE` es hoy la **única** selección de edición del sistema. Es una constante de settings resuelta por nombre, y el cliente **nunca** envía `evento_id`.

### 1.1 Evidencia verificada (código congelado, solo lectura)

| Ubicación | Contenido verificado |
|---|---|
| `backend/config/settings/base.py:141` | `EVENTO_ACTIVO_NOMBRE = env("EVENTO_ACTIVO_NOMBRE", default="Salesianos FEST 2026")` |
| `Aplicacion/backend/config/settings/base.py:132` | misma constante presente en el **destino** (variante de destino, −15 líneas respecto al origen) |
| `backend/modules/administracion/domain/services/core/admin_evento_activo_service.py:9,40` | resuelve el evento activo por `getattr(settings, "EVENTO_ACTIVO_NOMBRE", "")` |
| `backend/modules/eventos/domain/selectors/evento_selector.py:6` | idem — "the client never sends `evento_id`" |
| `backend/modules/salesianos_fest/domain/services/core/pase_service.py:40,45` | idem para el catálogo de pases |
| `backend/modules/administracion/domain/services/orchestrators/admin_resumen_orchestrator.py:55` | idem para el resumen administrativo |
| `backend/modules/administracion/domain/services/orchestrators/admin_fundacion_orchestrator.py:37,41` | idem para el health administrativo |
| `backend/modules/administracion/presentation/controllers/admin_resumen_controller.py:71` | idem (documentado en el controller) |
| `backend/modules/administracion/domain/exceptions.py:17` | el módulo ya contempla la ausencia de evento activo como caso de error |
| `backend/modules/administracion/tests/fixtures/evento_fixtures.py:5,18,20` | la fixture crea el evento con el nombre exacto de la constante |
| `backend/modules/eventos/tests/integration/test_evento_selector.py:7` | el test de integración depende de la constante |

**Lectura:** 15 referencias en `backend/` (2 en archivos de test). La constante se resuelve por **nombre**, no por identidad estable, y no admite más de una edición activa.

### 1.2 Por qué se elimina

- `RN-E01` exige que cada edición conserve inscripciones, competencias, precios, pases y operaciones **propios**. Un singleton por nombre no puede sostener dos ediciones simultáneas ni historial.
- `RN-E02` exige habilitación **por evento/edición** de funcionalidades opcionales.
- `FL-01` exige que el visitante vea "la edición publicada y módulos habilitados", y el plan `funcional/04` dice que en ausencia de edición activa se informe con claridad "sin atribuir operaciones a otra edición".
- `implementacion/01` §5 lista `EVENTO_ACTIVO_NOMBRE` como **explícitamente no heredable** sin revisión.

## 2. Decisión congelada

### 2.1 Identificadores

| Concepto | Identificador | Regla |
|---|---|---|
| `Evento` | `id` UUID (pk) + `nombre` + `slug` | familia de evento. Conservar/revisar (C) |
| `Edicion` | `id` UUID (pk) + `evento_id` FK + `nombre` + `slug` + `anio` + `estado` | **nuevo** (N en `funcional/03` §1) |
| `Edicion.estado` | `BORRADOR` \| `PUBLICADA` \| `CERRADA` | exactamente una `PUBLICADA` por evento como máximo |
| Scope activo | `edicion_id` UUID | identificador estable, nunca un nombre |

`Edicion` es la unidad de scope. `Evento` es la familia que agrupa ediciones y **no** es un scope de datos.

### 2.2 Resolución del scope — orden congelado y único

Una ruta con scope de edición resuelve **exactamente una** `Edicion`, en este orden. No hay fallback silencioso entre niveles.

| # | Origen | Regla |
|---|---|---|
| 1 | `edicion_id` explícito en la ruta o query | Caso normal para administración y operaciones por recurso. Si no existe → `404 EDICION_NO_ENCONTRADA` |
| 2 | Edición activa del actor autenticado | Solo si el actor tiene **exactamente una** edición activa. Si tiene varias → `409 EDICION_AMBIGUA` con la lista de candidatas en `details` |
| 3 | Edición `PUBLICADA` única | Si hay **exactamente una** `PUBLICADA` → se usa. Si hay **cero** → `404 EDICION_NO_PUBLICADA` con mensaje neutro. Si hay **más de una** → `409 EDICION_AMBIGUA` |
| 4 | Sin resolución | `404 EDICION_NO_RESUELTA`. **Prohibido** elegir una edición por defecto |

**Regla dura:** en ningún nivel se resuelve la edición "la primera", "la más reciente" o "la que coincida con un nombre por defecto". Ante ambigüedad o ausencia, se responde con error; nunca se opera sobre la edición equivocada (`implementacion/01` §4, "Selección de edición (ruta/contexto) — Nunca mutar inadvertidamente edición equivocada").

### 2.3 Prohibiciones

1. **Prohibido** reintroducir una constante de "edición activa" en `settings`. `EVENTO_ACTIVO_NOMBRE` **se elimina** de `Aplicacion/backend/config/settings/base.py`.
2. **Prohibido** resolver el scope por **nombre**. Solo por `id` o por `slug` resuelto a `id` en el borde de entrada.
3. **Prohibido** que el frontend envíe un nombre de evento/edición para selection. Envía `edicion_id` cuando la ruta lo admite; si no lo admite, resuelve el backend.
4. **Prohibido** que un módulo consulto la edición activa global desde settings. Cada módulo recibe el `edicion_id` resuelto por su controller.
5. **Prohibido** que un listado operativo devuelva datos de más de una edición sin filtro explícito. Un listado sin `edicion_id` debe declarar en su contrato qué editions incluye.

### 2.4 Transición de `EVENTO_ACTIVO_NOMBRE`

| Fase | Uso permitido de la constante | Owner |
|---|---|---|
| GOV-01 (este freeze) | Solo lectura, evidencia. **Prohibido** su uso en código nuevo | A0 |
| FND-02 (`T-010`) | Admisible **únicamente** como valor semilla al crear la primera `Edicion` de una instalación nueva, y **solo** en un comando de gestión, no en el arranque del servidor | A1 |
| FND-02 cierre | La constante se **elimina** de `Aplicacion/backend/config/settings/base.py`. Test que verifica que `settings` ya **no** expone `EVENTO_ACTIVO_NOMBRE` | A1 |
| FND-06 (`T-017`) | El frontend deja de asumir "la edición actual" implícita y pasa a leer la edición resuelta desde la respuesta de catálogo | A7 |

**Prueba de remoción (obligatoria, FND-02):** `rg -n "EVENTO_ACTIVO_NOMBRE" Aplicacion/backend` debe devolver **0 coincidencias** al cerrar FND-02, salvo la mención documental en este freeze.

### 2.5 Funcionalidades opcionales por edición (RN-E02)

`Edicion` expone la configuración de módulos habilitados. El valor por defecto de cada módulo es **deshabilitado**: un módulo no habilitado no expone catálogo, no expone rutas de escritura y no necesita modelo ni datos.

| Módulo lógico | Clave de habilitación |
|---|---|
| Inscripciones deportivas | `inscripciones` |
| Pases / beneficios | `pases` |
| Marketplace | `marketplace` |
| Competencias | `competencias` |
| Patrocinadores | `patrocinadores` |

La habilitación es **datos de configuración de la edición**, no un flag de despliegue. El backend la aplica; la UI refleja la salida del backend.

### 2.6 Cuando la edición no está publicada

- Catálogo público: `404 EDICION_NO_PUBLICADA`, mensaje neutro. **Prohibido** inventar un catálogo estático con precios ficticios (`FL-01` paso 3).
- Historial público de ediciones: **no expuesto** en esta versión. La propuesta de `FL-01` paso 4 sigue siendo propuesta, no requisito (`[PROPUESTO]`, no ratificada aquí).

## 3. Contrato de datos mínimo de `Edicion`

```
Edicion
  id: UUID            (pk)
  evento_id: UUID     FK → Evento
  nombre: str
  slug: str           único por evento
  anio: int
  estado: BORRADOR | PUBLICADA | CERRADA
  modulos_habilitados: list[str]   # claves de la tabla §2.5
  fecha_inicio: date | null
  fecha_fin: date | null
  created_at, updated_at
```

Invariante: **como máximo una `Edicion` en estado `PUBLICADA` por `Evento`.** Se expresa con `UniqueConstraint` condicional sobre `(evento_id)` filtrado por `estado = 'PUBLICADA'` (`django-app-architecture-contract.md` §6.4).

El wrapper HTTP (`EdicionOut`) se define en `FR-07` y su versión en `FREEZE-PS-1.0.0`.

## 4. Impacto por consumidor

| Consumidor | Depende de | Acción requerida |
|---|---|---|
| FND-02 (`T-010`) | este freeze | Implementar `Edicion`, `EdicionSelector`, la resolución por orden y la eliminación de `EVENTO_ACTIVO_NOMBRE` |
| FND-01 (`T-016`, `T-018`) | este freeze | `config/api.py` y `core/` deben aceptar el scope resuelto; ningún módulo lee settings |
| DOM-01..DOM-08 | `T-010` | Todo modelo con FK a edición lleva `edicion_id`; todo filtro operativo es por `edicion_id` |
| UI-01..UI-05 | `T-017` | El frontend resuelve la edición desde el backend; no mantiene una constante propia |
| API-01..API-05 | `T-082` | Cada ruta declara si es edition-scoped y con qué mecanismo (path, query o resolución) |

## 5. Criterios de aceptación de este freeze

- [x] `EVENTO_ACTIVO_NOMBRE` queda **explícitamente reemplazado**, con orden de resolución único, prohibitions y plan de eliminación.
- [x] El mecanismo no admite ambigüedad silenciosa: dos ediciones publicadas → error, nunca una elegida por defecto.
- [x] La habilitación por edición (RN-E02) queda con valores por defecto **deshabilitados**.
- [x] Los consumidores y sus owners quedan nombrados.

## 6. Decisiones abiertas que este freeze NO resuelve

| ID | Pendiente | Por qué no se resuelve aquí | Owner |
|---|---|---|---|
| `GOV-01-OPEN-02` | Exposición del histórico público de ediciones | El plan lo marca `[PROPUESTO]` (`FL-01` paso 4). No se ratifica. | A0 + producto |
| `GOV-01-OPEN-03` | Calendario y ciclo de vida exacto de una `Edicion` (fechas, cierre, reapertura) | No hay requisito aprobado. `Edicion.fecha_inicio/fecha_fin` quedan **nullables y sin semántica** hasta que se defina | A0 + producto |
| `PD-05` (relacionada) | Stock compartido entre ediciones o por edición | Afecta al modelo de existencias, no al scope | A5 + producto |
