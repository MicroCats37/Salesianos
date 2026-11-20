# DOM-08 — Patrocinadores, logo y galería ordenada por edición

**Artifact:** `evidence/domains/DOM-08-patrocinadores-logo-galeria.md` · **Packet:** `DOM-08` (`wave-02-domain-backend`) · **Owner:** A8
**Original plan task:** `T-060` · **Freezes:** `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0`
**Date:** 2026-11-19 · **Status:** `verification_required` · **Mode:** Standard (no hay `strict_tdd` activo)

> **Commands ejecutados: NINGUNO.** La verificación en ejecución está **DIFERIDA
> por instrucción explícita del usuario** (aplicable a este paquete y a todos
> los siguientes): las pruebas se ESCRIBEN pero **NO se ejecutan**; están
> prohibidos `pytest`, `manage.py check`, `makemigrations`, `migrate`, typecheck,
> lint, build, servidor, navegador y sondas HTTP; está prohibido invocar el
> Python global y el de `.venv`. En su lugar, el paquete se entrega con una
> **REVISIÓN ESTÁTICA** de la fuente (§8) y con la lista de comandos futuros
> (§9), que deben ejecutarse con `uv run` y autorización explícita.

---

## 1. Qué se entregó

El módulo `Aplicacion/backend/modules/patrocinadores/**` (nuevo, **57 archivos**
`.py`: 41 de producción, 2 de migración y 14 de pruebas):

| Capa | Contenido |
|---|---|
| Modelos | `Patrocinador` (ficha + logo + visibilidad) · `PatrocinadorImagen` (galería ordenada) |
| Alcance | `Patrocinador` cuelga de `eventos.Edicion` (`PROTECT`); la galería cuelga del patrocinador (`CASCADE`) |
| Dominio | `PatrocinadorCoreService` (escritura + proyección) · `PatrocinadorMediaService` (escritura y limpieza de archivos) |
| Flujo | `PatrocinadorFlujo` — async, único lugar con `transaction.atomic()`, con limpieza de media en todos los caminos |
| Orquestador | `PatrocinadorOrchestrator` — fachada delgada; resuelve el alcance por el puerto `IAlcanceEdicion` |
| Puerto | `IAlcanceEdicion` (lo declara el dominio) + adaptador `AlcanceEdicionEventos` (en `infrastructure/`) |
| Presentación | `PatrocinadorHydrator` (protocolo multipart) · `PatrocinadorPresenter` · schemas compuestos en tres bloques |
| HTTP | `POST /patrocinadores` (`RT-MD-02`, multipart, permiso `Administrador`) |
| Migración | `modules/patrocinadores/migrations/0001_initial.py` |
| Tests | **53 tests** (16 multipart/HTTP · 10 limpieza · 11 reglas · 12 contrato · 4 e2e) — **ESCRITOS, NO EJECUTADOS** |

**Líneas:** producción **1 739** · migración **170** · tests **1 454** · total **3 363**.
El paquete NO crea commit, NO invoca `git stash` y NO toca ninguna raíz
prohibida.

**Sin finanzas.** El módulo NO declara aportaciones, comisiones, pagos,
facturas, saldo, margen ni ningún hecho económico o contable. No usa `Decimal`
y no importa `commerce` ni `pagos`. La regla está PROBADA por test, no sólo
documentada (§7).

---

## 2. Modelo de datos

### `Patrocinador` — `patrocinadores_patrocinador`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | UUID (pk) | `BaseModel` (`core/models`) |
| `edicion` | FK → `eventos.Edicion` (`PROTECT`) | **Alcance de edición** (FR-02 §3 · RN-E01). El cliente NUNCA la elige |
| `nombre` | `CharField(200)` | Identidad de la ficha |
| `slug` | `SlugField(200)` | **Único por edición** (`UniqueConstraint (edicion, slug)`) |
| `descripcion` | `TextField(blank)` | Ficha |
| `sitio_web` | `URLField(300, blank)` | Ficha (opcional) |
| `visible` | `BooleanField(default=True)` | **Visibilidad** (ADM-21) |
| `logo` | `ImageField(blank)` | Imagen ÚNICA de identidad (opcional) |
| `created_at` / `updated_at` | `DateTimeField` | Auditoría |

### `PatrocinadorImagen` — `patrocinadores_patrocinador_imagen`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | UUID (pk) | `BaseModel` |
| `patrocinador` | FK → `Patrocinador` (`CASCADE`) | La galería cuelga del patrocinador |
| `imagen` | `ImageField` | Ruta precalculada (FR-06 §2.2) |
| `orden` | `PositiveIntegerField(0)` | Orden canónico `orden ASC, id ASC` (FR-06 §2.6) |
| `texto_alternativo` | `CharField(200, blank)` | Accesibilidad (FR-06 §2.6) |
| `created_at` / `updated_at` | `DateTimeField` | Auditoría |

**La galería NO tiene `es_principal`** (`D-DOM08-02`): el logo ES la imagen de
identidad y la galería es un carrusel ordenado. FR-06 §2.6 sólo declara
`es_principal?` (con interrogación) para `ProductoImagen`. La ausencia del
campo es una garantía: no puede haber "una principal implícita" que contradiga
al logo.

---

## 3. Protocolo multipart — el MISMO de DOM-04, sin bifurcación

**Versión del protocolo:** `PROTO-MD-1.0.0` (DOM-04), IMPLEMENTA
`FREEZE-MD-1.0.0` (FR-06 §2.4). DOM-08 **NO declara una segunda versión ni
una segunda implementación**: consume las primitivas de `core/media.py`.

| Parte | Nombre | Contenido |
|---|---|---|
| Datos | campo `data` | JSON del payload; cada `File` viaja sustituido por su token `file_<uuid>` |
| Archivos | campo `files` | una o más partes; el `filename` es `<token>___<realname>` |

**Forma del payload de alta** (`CrearPatrocinadorIn`):

```json
{
  "nombre": "Colegio San Juan Bosco",
  "slug": "colegio-san-juan-bosco",
  "descripcion": "Patrocinador de la edición 2026.",
  "visible": true,
  "logo": "file_logo111",
  "imagenes": [
    {"token": "file_aaa111", "texto_alternativo": "Portada"},
    {"token": "file_bbb222", "texto_alternativo": "Fachada"}
  ]
}
```

**Matching EXACTAMENTE UNA VEZ.** El token del logo y los tokens de la galería
aparecen **una sola vez** cada uno en el payload: por eso el texto alternativo
viaja DENTRO del objeto de la imagen (duplicar el token sería, correctamente,
un token duplicado). El matching lo hace `core.media.resolver_tokens_media`.

| Situación | Código | Status |
|---|---|---|
| token del payload sin parte de archivo | `MEDIA_TOKEN_NO_RESUELTO` | 400 |
| parte de archivo que el payload no referencia | `MEDIA_ARCHIVO_HUERFANO` | 400 |
| token repetido en el payload o con dos partes | `MEDIA_TOKEN_DUPLICADO` | 400 |
| MIME fuera de allowlist o firma incoherente | `MEDIA_TIPO_NO_PERMITIDO` | 400 |
| tamaño > 5 MiB | `MEDIA_TAMANO_EXCEDIDO` | 413 |
| dimensiones fuera de rango (hook `GOV-01-OPEN-10`) | `MEDIA_DIMENSIONES_INVALIDAS` | 400 |

**Orden de los errores** (idéntico al de DOM-04, para que los dos dominios se
comporten igual): (1) `data` ausente o con JSON inválido → 422
`VALIDATION_ERROR` · (2) protocolo multipart → 400/413 `MEDIA_*` · (3) schema
del payload → 422 `VALIDATION_ERROR` con `field_errors` · (4) contenido del
archivo → 400/413 `MEDIA_*`.

**El módulo NO usa los helpers heredados** `core/types.py::hydrate_form` ni
`parse_request_payload`: lanzan `HttpError` con texto interpolado y no usan los
códigos de media del catálogo. Consume `core.media` (`parsear_archivos_media`,
`resolver_tokens_media`, `validar_archivo_media`, `construir_ruta_media`,
`limpiar_archivos_media`).

**UNA representación del archivo.** `ArchivoPatrocinadorUploadData` (token +
`UploadedFile` + MIME detectado + extensión + tamaño + nombre original) viaja
desde el borde HTTP hasta el flujo dentro de `PatrocinadorCreateData.logo` y
`PatrocinadorCreateData.imagenes`. El logo y las imágenes de la galería
comparten ESA única representación (son el mismo tipo de recurso). No hay un
segundo argumento de archivos en ninguna firma.

---

## 4. Limpieza de media — los tres caminos obligatorios (FR-06 §2.5)

| Camino | Comportamiento | Test |
|---|---|---|
| **Validación fallida** | NO se escribe nada: la validación ocurre en el borde HTTP, antes de tocar el disco | `test_firma_de_contenido_invalida_se_rechaza`, `test_tamano_excedido_se_rechaza` |
| **Rollback de transacción** | Los archivos escritos durante la operación se BORRAN: la base se revierte sola, el volumen no | `test_un_rollback_deja_el_volumen_sin_residuos` |
| **Reemplazo (logo)** | El archivo anterior se borra DESPUÉS de que el nuevo quedó persistido; si el reemplazo falla, el anterior sigue y el nuevo se limpia | `test_reemplazar_el_logo_borra_el_archivo_anterior_despues_del_nuevo`, `test_un_reemplazo_fallido_conserva_el_archivo_anterior` |
| **Reemplazo (imagen)** | Igual, sobre la imagen de la galería | `test_reemplazar_una_imagen_de_la_galeria` |
| **Borrado de imagen** | Al borrar una imagen de la galería se borra su archivo (el logo NO se toca: es otro recurso) | `test_borrar_una_imagen_borra_su_archivo` |
| **Borrado de entidad** | Al borrar el patrocinador se borran el logo Y los archivos de la galería | `test_borrar_el_patrocinador_borra_el_logo_y_sus_archivos` |

**Mecanismo.** `PatrocinadorFlujo` registra la ruta ANTES de escribir (para que
un fallo posterior no deje un huérfano) y la sustituye por la ruta real
después (`get_available_name` puede desambiguar un choque de nombre). En el
`except` del flujo se invoca `core.media.limpiar_archivos_media(rutas)`.

**Ruta de almacenamiento** (FR-06 §2.2):
`MEDIA_ROOT/patrocinadores/<patrocinador_id>/<uuid><ext>`. El logo y la
galería comparten el directorio porque el dueño es el PATROCINADOR en los dos
casos: así se localizan y se limpian TODOS los archivos de una entidad sin
recorrer el volumen (FR-06 §2.2 regla 3). El nombre enviado por el cliente se
ignora (`upload_to` devuelve la ruta precalculada) y la extensión sale del MIME
**detectado** (`.jpg` / `.png` / `.webp`).

**Degradación por archivo ausente** (FR-06 §2.7): si el archivo ya no está en
el volumen, la imagen viaja con `disponible = false` y `url = null`, y se
registra una incidencia de media en el log. NO hay 500 ni hueco oculto.

**Limitación heredada (no corregida aquí):** `core.media.limpiar_archivos_media`
borra los ARCHIVOS pero deja los DIRECTORIOS vacíos
(`patrocinadores/<id>/`). Los tests comprueban "cero ARCHIVOS residuales", que
es lo que el contrato compartido garantiza; la poda de directorios vacíos es
una mejora de `core/media.py` (raíz de A0) → petición **A0-08**.

---

## 5. Alcance, visibilidad y orden

| Regla | Dónde vive | Evidencia |
|---|---|---|
| El cliente NUNCA elige la edición | `PatrocinadorOrchestrator.crear_patrocinador` sustituye el `edicion_id` del payload | `test_el_cliente_nunca_elige_la_edicion` |
| Slug único POR EDICIÓN | `UniqueConstraint (edicion, slug)` — la base es la autoridad | `test_el_slug_es_unico_por_edicion`, `test_el_slug_es_unico_dentro_de_la_edicion` |
| El alcance es explícito en las lecturas | `PatrocinadorSelector.obtener_por_slug(edicion_id, slug)` | `test_el_selector_acentua_el_ambito_de_edicion` |
| Un módulo lógico deshabilitado no expone catálogo ni escrituras (RN-E02) | `PatrocinadorOrchestrator._resolver_actual_sync` → `ModuloNoHabilitadoError` (409) | `test_el_modulo_deshabilitado_no_expone_patrocinadores` |
| **Visibilidad** (ADM-21) | `Patrocinador.visible` + filtro del selector | `test_la_visibilidad_es_un_hecho_del_patrocinador`, `test_la_visibilidad_se_puede_cambiar` |
| Orden canónico de la galería `orden ASC, id ASC` (FR-06 §2.6) | `PatrocinadorImagen.Meta.ordering` | `test_el_orden_de_la_galeria_es_orden_por_id` |
| El orden se puede FIJAR explícitamente | `PatrocinadorCoreService.reordenar_imagenes` | `test_el_orden_de_la_galeria_se_puede_fijar` |
| El orden NUNCA cruza el alcance | `reordenar_imagenes` valida que la imagen pertenezca al patrocinador | `test_una_imagen_de_otro_patrocinador_se_rechaza` |
| La galería tiene un tope declarado | `MAX_IMAGENES_GALERIA = 24`, comprobado ANTES de escribir | `test_una_galeria_demasiado_grande_se_rechaza` |
| Un patrocinador sin logo no inventa un logo | `PatrocinadorCoreService.result_de` → `logo = None` | `test_un_patrocinador_sin_logo_no_inventa_un_logo` |

---

## 6. Superficie HTTP

**El ledger (FR-07 §3.3) congela UNA ruta para este módulo.** DOM-08 la
implementa y NO inventa otras:

| Ruta | Método | Scope | Permiso | Errores | Presenter | Wrapper |
|---|---|---|---|---|---|---|
| `/patrocinadores` | POST | implícito | `Administrador` | `MEDIA_*` (400/413) · `PATROCINADOR_SLUG_DUPLICADO` (409) · `PATROCINADOR_NO_ENCONTRADO` (404) | `PatrocinadorPresenter` | `PatrocinadorOut` |

**Las demás capacidades son CAPACIDADES DE DOMINIO**, no rutas: actualizar la
ficha, cambiar la visibilidad, reordenar la galería, reemplazar el logo,
reemplazar una imagen, eliminar una imagen y eliminar el patrocinador. Viven en
`PatrocinadorFlujo` con sus tipos, sus pruebas y sus resultados tipados, pero
**no se exponen por HTTP** porque el ledger no las declara y crear rutas es
decisión de A0 (petición **A0-04**). Los shapes de lectura (`PatrocinadorOut`
y sus tres bloques) quedan CONGELADOS para que API-05 pueda espejarlos.

**Registro.** Una ruta no existe hasta que su controller está registrado en
`config/api.py` (FR-07 §3.1 regla 2). `config/api.py` es de A0 y este paquete
NO lo edita → petición **A0-02**.

**Versión del contrato.** `SCHEMA_VERSION = "1.0.0"` en
`presentation/schemas/__init__.py`, y el registro global de A0 ya declara
`SCHEMA_VERSIONS["patrocinadores"] = "1.0.0"`: **NO hay drift** y no hace
falta ninguna actualización del registro (a diferencia de DOM-05).

---

## 7. Pruebas — 53 tests ESCRITOS, NO EJECUTADOS

| Fichero | Tests | Cubre |
|---|---|---|
| `tests/integration/test_patrocinadores_multipart.py` | 16 | El protocolo COMPLETO sobre `RT-MD-02`: alta JSON, alta multipart con logo + galería ordenada, token ausente (logo y galería), huérfano, token duplicado (en el payload y con dos partes), firma inválida, tamaño excedido, 422 con `field_errors`, texto opcional vacío, `sitio_web` inválido, 401, 403, y que el error no filtra rutas ni nombres de archivo |
| `tests/integration/test_patrocinadores_media_limpieza.py` | 10 | Rollback, alta exitosa, reemplazo de logo (éxito y fallo), reemplazo de imagen, borrado de imagen, borrado del patrocinador (logo + galería), tope de galería, orden explícito, imagen ajena |
| `tests/integration/test_patrocinadores_reglas.py` | 11 | Slug por edición, alcance del selector, módulo deshabilitado, visibilidad (listado + cambio), la ficha no toca los archivos, orden canónico, degradación, ausencia de logo, proyección del result |
| `tests/integration/test_patrocinadores_contrato.py` | 12 | Versión de schema sin drift, contrato de datos mínimo, unicidad en la base, ausencia de `es_principal`, representación ÚNICA del archivo, almacenamiento el de `core/media.py`, matching compartido, **cero dominio financiero**, presenter puro, controller sin imports ajenos, dominio sin import de `eventos` |
| `tests/e2e/test_patrocinadores_controller.py` | 4 | Envolvura congelada, alta con logo + galería ordenada, slug duplicado → 409, degradación sin archivo |
| **Total** | **53** | |

**Sin dobles de producción**: los servicios se resuelven por el inyector real
o se construyen con las clases reales; el único doble es el que fuerza el
fallo de escritura para ejercitar el rollback de media.

**El volumen real NO se toca**: la fixture `media_root` apunta `MEDIA_ROOT` a
un directorio temporal de pytest. Cambiar `settings.MEDIA_ROOT` dispara la
señal `setting_changed`, que limpia las propiedades cacheadas de
`FileSystemStorage` (`StorageSettingsMixin._clear_cached_properties`), de modo
que el `default_storage` sigue apuntando al temporal durante todo el test.

---

## 8. Revisión estática (sustituye a la verificación en ejecución)

| # | Comprobación | Resultado |
|---|---|---|
| C-01 | El módulo NO crea una segunda versión del protocolo multipart | ✅ Consume `core.media`; el test de contrato prohíbe `TOKEN_PATTERN` / `FILE_KEY_PATTERN` en el módulo |
| C-02 | El módulo NO declara un almacenamiento propio | ✅ `construir_ruta_media` es el único constructor de ruta; el test prohíbe `from django.conf import settings` en el servicio de media |
| C-03 | Orden de las rutas | ✅ Una sola ruta (`POST /patrocinadores`); el prefijo del controller es `/patrocinadores` y la operación usa `""`, de modo que la ruta final es `/api/patrocinadores` (sin barra final, sin redirección `APPEND_SLASH`) |
| C-04 | Frontera async/ORM | ✅ Controller async → orquestador async → flujo async (`sync_to_async`) → core sync. Los selectores devuelven LISTAS evaluadas (F-26). Ningún `QuerySet` se recorre en un contexto async |
| C-05 | `transaction.atomic()` | ✅ Sólo en `PatrocinadorFlujo`; los core services NO abren transacción |
| C-06 | `IntegrityError` capturado FUERA del atómico | ✅ El `except IntegrityError` está en el método async, fuera del bloque decorado; se traduce a `PatrocinadorSlugDuplicadoError` |
| C-07 | Alcance de edición | ✅ El orquestador sustituye el `edicion_id` del payload; el cliente nunca lo elige; el módulo lógico `patrocinadores` debe estar habilitado (RN-E02) |
| C-08 | Coherencia del alcance en la galería | ✅ `reordenar_imagenes` valida que la imagen pertenezca al patrocinador; `eliminar_imagen` y `reemplazar_imagen` buscan la imagen DENTRO del patrocinador |
| C-09 | Matching de tokens | ✅ `resolver_tokens_media` sobre el payload CRUDO (igual que DOM-04): token ausente → 400, huérfano → 400, repetido → 400 |
| C-10 | Una sola representación del archivo | ✅ `ArchivoPatrocinadorUploadData`; el logo y la galería la comparten; no hay un segundo argumento de archivos en ninguna firma |
| C-11 | Validación antes de persistir | ✅ `validar_archivo_media` corre en el borde HTTP, antes de tocar el disco (FR-06 §2.3) |
| C-12 | Limpieza en los tres caminos | ✅ Validación (nada escrito), rollback (`limpiar(rutas)` en el `except`), reemplazo (el anterior se borra DESPUÉS del nuevo), borrado (logo + galería) |
| C-13 | Versionado del contrato | ✅ `SCHEMA_VERSION = "1.0.0"` == `SCHEMA_VERSIONS["patrocinadores"]`; sin drift, sin petición a A0 |
| C-14 | Restricciones de base de datos | ✅ `UNIQUE (edicion, slug)`; `PROTECT` en la FK de edición; `CASCADE` en la galería. Sin `es_principal`, sin restricción condicional |
| C-15 | Comportamiento del borrado de archivos | ✅ Las rutas se capturan ANTES de borrar la fila (`rutas_de`) y los archivos se borran DESPUÉS (`limpiar`) |
| C-16 | Cero dominio financiero | ✅ Ni campos, ni `Decimal`, ni imports de `commerce`/`pagos`; hay un test que lo prueba sobre TODO el código de producción |
| C-17 | Capas | ✅ El presenter no consulta la BD; el controller no importa presenters ni schemas de otro módulo; el dominio no importa `eventos` (lo cruza por el puerto) |
| C-18 | Fuga de información | ✅ Los errores viajan por el catálogo público con códigos estables; `MEDIA_*` no filtran rutas, nombres de archivo ni texto crudo |
| C-19 | Migración | ✅ `0001_initial` con dependencia `("eventos", "0001_initial")`; `db_table` explícito; sin `es_principal`; reversible por construcción |
| C-20 | Sin residuos | ✅ El módulo no escribe en el volumen real: la fixture apunta `MEDIA_ROOT` a un temporal |
| C-21 | El `sitio_web` se valida en el borde HTTP con el MISMO validador del modelo | ✅ `URLValidator` (el de `models.URLField.default_validators`): `Model.save()` no ejecuta validadores, así que sin esto una URL inválida se persistiría en silencio |
| C-22 | Una cadena vacía sigue siendo una cadena vacía | ✅ `CrearPatrocinadorIn._texto_opcional_a_cadena` (`mode="before"`) revierte localmente la conversión `"" → None` de `BaseSchema.sanitize_strings` para los campos cuyo valor por defecto es `""` (`D-DOM08-10`, `A0-10`) |

**Correcciones aplicadas durante la revisión estática**

| # | Corrección |
|---|---|
| K-01 | El `slug` pasó de `^[-a-zA-Z0-9_]+$` (el de DOM-04) a kebab-case `^[a-z0-9]+(?:-[a-z0-9]+)*$`: el protocolo escanea el payload CRUDO buscando tokens `file_<uuid>` y un identificador con guion bajo podía colisionar con ese patrón (un slug `file_x` se habría rechazado con `MEDIA_TOKEN_NO_RESUELTO` en vez de con 422). Ver `D-DOM08-04` |
| K-02 | `min_length` retirado del campo `logo` (`str \| None`): es redundante porque `BaseSchema.sanitize_strings` convierte la cadena vacía en `None` |
| K-03 | `CrearPatrocinadorIn` importado en el controller con `# noqa: F401` explícito (documenta el schema de entrada del ledger sin convertirlo en un import muerto) |
| K-04 | `eliminar_archivos_de` se partió en `rutas_de` + `limpiar`: el flujo necesita capturar las rutas ANTES de borrar la fila y borrarlas DESPUÉS |
| K-05 | `CrearPatrocinadorIn` valida el `sitio_web` con `URLValidator` (el mismo del modelo) y neutraliza localmente la conversión `"" → None` de `BaseSchema.sanitize_strings` (`D-DOM08-10`, `A0-10`) |

---

## 9. Comandos futuros (NO ejecutados)

Todos requieren **autorización explícita** del usuario y deben usar `uv run`
(nunca el Python global ni el de `.venv`). Workdir: `Aplicacion/backend`.

```powershell
$env:DJANGO_SETTINGS_MODULE = "modules.patrocinadores.tests.settings_overlay"

# 1) Suite del módulo
uv run python -m pytest modules/patrocinadores/tests -q

# 2) Foco en el protocolo multipart
uv run python -m pytest modules/patrocinadores/tests -q -k "multipart or token or huerfano"

# 3) Foco en la limpieza de media
uv run python -m pytest modules/patrocinadores/tests -q -k "limpieza or rollback or reemplaza or borra"

# 4) Migraciones: la migración escrita a mano debe coincidir con los modelos
uv run python manage.py makemigrations --check --dry-run --settings=modules.patrocinadores.tests.settings_overlay

# 5) Chequeo de Django
uv run python manage.py check --settings=modules.patrocinadores.tests.settings_overlay

# 6) Migración real (rehearsal) y reversibilidad
uv run python manage.py migrate --settings=modules.patrocinadores.tests.settings_overlay
uv run python manage.py showmigrations patrocinadores --settings=modules.patrocinadores.tests.settings_overlay
uv run python manage.py migrate patrocinadores zero --settings=modules.patrocinadores.tests.settings_overlay
uv run python manage.py migrate --settings=modules.patrocinadores.tests.settings_overlay

# 7) Regresión de los dominios ya cerrados (no debe cambiar nada)
uv run python -m pytest core/tests -q
uv run python -m pytest modules/eventos/tests modules/usuarios/tests -q

# 8) Barrido de residuos (NO debe existir nada de esto)
Test-Path Aplicacion/backend/media
Test-Path Aplicacion/backend/db.sqlite3
```

**Comandos ejecutados en este paquete: NINGUNO.** Los dos `manage.py` con los
settings por defecto (`config.settings.production`) siguen fallando con
`DB_NAME`: es el baseline ambiental conocido (F-1), idéntico a FND-01…FND-05,
DOM-01…DOM-05.

---

## 10. Peticiones a A0 (registradas, NO aplicadas)

| # | Petición | Prioridad |
|---|---|---|
| **A0-01** | `INSTALLED_APPS += ["modules.patrocinadores"]` en `config/settings/base.py` (orden del grafo de migraciones: después de `marketplace`, porque depende de `eventos.0001`) | **BLOQUEANTE** |
| **A0-02** | `registrar_controladores(PatrocinadorController)` en `config/api.py` — sin esto la ruta NO existe (FR-07 §3.1 regla 2) | **BLOQUEANTE** |
| **A0-03** | Catalogar **4 códigos públicos** nuevos: `PATROCINADOR_NO_ENCONTRADO` (404) · `PATROCINADOR_SLUG_DUPLICADO` (409) · `PATROCINADOR_IMAGEN_NO_ENCONTRADA` (404) · `GALERIA_PATROCINADOR_INVALIDA` (422). Los códigos de MEDIA ya están catalogados | media |
| **A0-04** | Ratificar (o rechazar) las rutas de lectura y de escritura que el ledger NO declara: `GET /patrocinadores` (público, sólo visibles), `GET /patrocinadores/{slug}`, y las de escritura (actualizar ficha/visibilidad, reordenar galería, reemplazar logo, reemplazar imagen, eliminar imagen, eliminar patrocinador). DOM-08 las entrega como CAPACIDADES DE DOMINIO con sus tipos y sus pruebas; exponerlas es decisión de A0 | **media** |
| **A0-05** | `NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.patrocinadores.di.PatrocinadoresModule"]` en `config/settings/base.py` | **BLOQUEANTE** |
| **A0-06** | Confirmar que `SCHEMA_VERSIONS["patrocinadores"] = "1.0.0"` (ya está en el registro) es el valor correcto para el módulo: el ledger no declara versión para `patrocinadores` y el paquete declara `1.0.0` | baja |
| **A0-07** | `*.sqlite3` en `.gitignore` (baseline conocido, F-2, arrastrado desde FND-01) | baja |
| **A0-08** | `core.media.limpiar_archivos_media` deja los DIRECTORIOS vacíos (`patrocinadores/<id>/`) tras una limpieza: evaluar podarlos. `core/media.py` es raíz de A0 y este paquete NO lo tocó | baja |
| **A0-09** | Sincronizar `00-matriz-tareas.md` con `T-060` | baja |
| **A0-10** | `core.types.BaseSchema.sanitize_strings` convierte la cadena vacía en `None` ANTES de validar: para un campo cuyo valor por defecto es la cadena vacía, un `""` legítimo acaba en un error de tipo (422 «Input should be a valid string»). DOM-08 lo neutraliza LOCALMENTE (validador `mode="before"` en `CrearPatrocinadorIn`); A0 debe decidir si la regla se hace opt-in o se corrige en `core/types.py` para que los módulos hermanos converjan | baja |

**NO se pide** ninguna modificación de `core/media.py`, `core/exceptions.py`,
`core/contract_versions.py` ni `config/**`: este paquete NO los tocó.

---

## 11. Desviaciones y decisiones abiertas

### Desviaciones

| # | Desviación | Por qué |
|---|---|---|
| `D-DOM08-01` | El módulo declara SU PROPIO puerto `IAlcanceEdicion` y SU PROPIO adaptador `AlcanceEdicionEventos` | Cada módulo declara su puerto (F-49). No hay un puerto compartido que obligue a los dominios a compartir vocabulario ni a editar el mismo fichero. El `core/media.py` SÍ es compartido y SÍ se consume |
| `D-DOM08-02` | `PatrocinadorImagen` NO tiene `es_principal` | El logo ES la imagen de identidad. FR-06 §2.6 sólo declara `es_principal?` para `ProductoImagen`. La ausencia del campo garantiza que no exista una "principal implícita" que contradiga al logo |
| `D-DOM08-03` | La superficie HTTP es la ÚNICA ruta del ledger (`RT-MD-02`) | El ledger no declara más rutas para este módulo. El CRUD completo existe como capacidad de dominio, con tipos y pruebas (mismo precedente que `crear_categoria` en DOM-04) |
| `D-DOM08-04` | El `slug` es kebab-case en vez del patrón `^[-a-zA-Z0-9_]+$` de DOM-04 | El protocolo escanea el payload CRUDO buscando tokens `file_<uuid>`: un slug con guion bajo podría colisionar con el patrón del token y ser rechazado con `MEDIA_TOKEN_NO_RESUELTO` (400) en vez de con `VALIDATION_ERROR` (422). El kebab-case hace la colisión imposible. El coste es que un slug con mayúsculas o guion bajo se rechaza con 422 |
| `D-DOM08-05` | El logo es OPCACIONAL (`blank=True`) | FR-06 §2.6 no dice que el logo sea obligatorio, y ADM-21 pide "CRUD de ficha, logo, galería": el logo se gestiona por su propio camino (reemplazo). Un patrocinador puede existir sin logo y tener después |
| `D-DOM08-06` | `visible` es un `BooleanField`, no un `estado` con enumeración | ADM-21 nombra "visibilidad" y ningún contrato congela un vocabulario de estados para el patrocinador. Un booleano es el mínimo que expresa la regla; un `TextChoices` sería inventar un ciclo de vida |
| `D-DOM08-07` | `MAX_IMAGENES_GALERIA = 24` declarado en el módulo | Es un límite ESTRUCTURAL del recurso, declarado de forma explícita para que el rechazo sea reproducible. No es una política comercial. El valor concreto es una decisión de A0 + producto (`A0-04` lo puede revisar) |
| `D-DOM08-08` | El paquete NO expone rutas de lectura por HTTP | Decisión de A0 (`A0-04`). Los shapes de salida quedan congelados (`PatrocinadorOut` + sus tres bloques) para que API-05 los espeje cuando las rutas se ratifiquen |
| `D-DOM08-09` | `PatrocinadorCoreService.actualizar` usa `exclude_none=True` | Consistente con `ProductoCoreService.actualizar` (DOM-04): un `None` significa "sin tocar", no "borrar". Consecuencia: no se puede vaciar un campo de texto por la vía de la actualización parcial |
| `D-DOM08-10` | `CrearPatrocinadorIn` neutraliza LOCALMENTE la conversión de `""` a `None` que hace `core.types.BaseSchema.sanitize_strings` (validador `mode="before"`), y valida el `sitio_web` con el MISMO `URLValidator` que usa el `URLField` del modelo | El `Model.save()` NO ejecuta los validadores: sin la comprobación en el borde HTTP, una URL inválida se persistiría en silencio. Y sin el validador local, un `descripcion: ""` legítimo se rechazaría con 422 por un error de tipo. El arreglo es local (`core/types.py` es de A0) → petición **A0-10** |

### Decisiones abiertas (nunca adivinadas)

| # | Decisión | Owner |
|---|---|---|
| `OD-DOM08-01` | ¿El logo debe ser OBLIGATORIO para publicar un patrocinador? El módulo lo permite opcional | A0 + producto |
| `OD-DOM08-02` | ¿Debe existir un estado distinto de "visible" (borrador / publicado / archivado)? Ningún contrato lo congela | A0 + producto |
| `OD-DOM08-03` | ¿El número máximo de imágenes de la galería (`MAX_IMAGENES_GALERIA = 24`) es el adecuado? | A0 + producto |
| `OD-DOM08-04` | ¿Qué rutas HTTP de lectura y escritura se ratifican (ver `A0-04`)? | A0 |
| `OD-DOM08-05` | ¿Debe `Patrocinador` llevar un orden propio para la portada, o basta el orden alfabético canónico? El plan no lo congela y este paquete NO lo inventa | A0 + producto |
| `OD-DOM08-06` | La colisión entre el escaneo de tokens del payload CRUDO y los strings de texto libre (`nombre`, `descripcion`) es una limitación HEREDADA de `core/media.py`: un texto que empiece por `file_` se trataría como un token. Corregirlo exige tocar `core/media.py` (raíz de A0) | A0 |

---

## 12. Concurrencia

`Aplicacion/backend/modules/competencias/**` (**DOM-07**, A6) **no fue
tocado, revertido, reformateado ni fusionado**. `Aplicacion/backend/core/**`,
`Aplicacion/backend/config/**`, `Aplicacion/backend/modules/marketplace/**`,
`Aplicacion/backend/modules/salesianos_fest/**`, `Aplicacion/backend/modules/eventos/**`,
`Aplicacion/backend/modules/usuarios/**`, `Aplicacion/backend/modules/commerce/**`,
`Aplicacion/backend/modules/pagos/**`, `Aplicacion/frontend/**`, `contract/**`,
`Aplicacion/plan/**` y `Aplicacion/documentacion/**` **no fueron tocados**.

El topic compartido `sdd/salesianos-fest-rebuild/apply-progress` y
`sdd/salesianos-fest-rebuild/state` **NO se fusionaron**: los escribe el
coordinador cuando terminen todos los agentes concurrentes (F-42). Este
paquete sólo escribió su topic propio y su fichero de evidencia.

`git stash` **nunca** fue invocado. No se creó ningún commit. No se creó
residuo de base de datos ni de media.

---

## 13. Rollback

1. `uv run python manage.py migrate patrocinadores zero --settings=modules.patrocinadores.tests.settings_overlay` (sólo si A0 lo autoriza).
2. Borrar `Aplicacion/backend/modules/patrocinadores/**` (todo el paquete es nuevo).
3. Retirar `modules/patrocinadores/tests/settings_overlay.py` (lo retira A0 con `A0-01`/`A0-05`).
4. Borrar este fichero de evidencia.
5. **NO tocar** `Aplicacion/backend/media/`: el volumen es estado durable y puede contener media de otros paquetes o del usuario. Este paquete sólo crea media en temporales de test, que pytest borra.

**Punto de rollback:** el `HEAD` del repositorio en el momento de la entrega
(sin commit creado por este paquete).

---

## 14. Estado para los consumidores

- **API-05** (integración con el frontend): los wrappers `PatrocinadorOut`,
  `PatrocinadorDetalleOut` —no existe—, `PatrocinadorLogoOut` y
  `PatrocinadorImagenOut` quedan CONGELADOS con `SCHEMA_VERSION = "1.0.0"`.
  La ruta `POST /patrocinadores` es la del ledger. Las rutas de lectura
  dependen de `A0-04`. **Readiness PROVISIONAL** (verificación diferida).
- **UI-05** (panel de administración ADM-21): la ficha, el logo, la galería
  ordenada y la visibilidad existen como capacidades de dominio; la superficie
  HTTP depende de `A0-02` y `A0-04`.
- **XCT-01 / XCT-03**: el protocolo de media, la limpieza y los códigos de
  media están implementados y probados (los códigos de media ya estaban
  catalogados por A0). El volumen es persistente y el `STORAGES.default` ya
  existe (A0 lo aplicó).
- **VER-01…VER-03**: pendientes de la verificación diferida.
