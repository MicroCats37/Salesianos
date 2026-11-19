# DOM-04 — Catálogo de marketplace y multimedia con el protocolo multipart corregido

**Artifact:** `evidence/domains/DOM-04-marketplace-catalog-media.md` · **Packet:** `DOM-04` (`wave-02-domain-backend`) · **Owner:** A5
**Original plan task:** `T-040` · **Freezes:** `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0`
**Date:** 2026-11-19 · **Status:** completed · **Mode:** Standard (no hay `strict_tdd` activo)

---

## 1. Qué se entregó

El módulo `Aplicacion/backend/modules/marketplace/**` (nuevo, 57 archivos):

| Capa | Contenido |
|---|---|
| Modelos | `CategoriaProducto`, `Producto`, `ProductoImagen` (galería ordenada, imagen principal explícita) |
| Alcance | `CategoriaProducto` y `Producto` cuelgan de `eventos.Edicion` (`PROTECT`) |
| Precios | `precio` (`Decimal`), `precio_oferta` (`Decimal`), `oferta_inicia`/`oferta_termina` (`datetime` tipados) |
| Dominio | `ProductoCoreService` (escritura + proyección), `ProductoMediaService` (escritura y limpieza de archivos) |
| Flujo | `ProductoFlujo` — async, único lugar con `transaction.atomic()`, con limpieza de media en todos los caminos |
| Orquestador | `ProductoOrchestrator` — fachada delgada; resuelve el alcance por el puerto `IAlcanceEdicion` |
| Puerto | `IAlcanceEdicion` (lo declara el dominio) + adaptador `AlcanceEdicionEventos` (en `infrastructure/`) |
| Presentación | `ProductoHydrator` (protocolo multipart), `ProductoPresenter` / `ProductoListaPresenter` / `ProductoDetallePresenter` / `CategoriaListaPresenter`, schemas compuestos en tres bloques |
| HTTP | `POST /marketplace/productos` (RT-MD-01) · `GET /marketplace/categorias` (RT-MK-01) · `GET /marketplace/productos` (RT-MK-02) · `GET /marketplace/productos/{slug}` (RT-MK-03) |
| Migración | `modules/marketplace/migrations/0001_initial.py` |
| Tests | **35 tests** (11 multipart/HTTP, 12 limpieza y coherencia, 7 contrato, 5 e2e de lectura) |

**Líneas:** producción **1 962** · migración **258** · tests **1 115** · total **3 335**.
El paquete NO crea commit (`git stash` y `git commit` nunca invocados); `git rev-parse HEAD` sigue en `f3df5401c56b41c340f257e67d5a306904a9e670`.

---

## 2. Protocolo multipart — versión y forma EXACTA

**Versión del protocolo:** `PROTO-MD-1.0.0` (DOM-04), IMPLEMENTA `FREEZE-MD-1.0.0` (FR-06 §2.4). No hay una segunda versión: el protocolo es el congelado.

| Parte | Nombre | Contenido |
|---|---|---|
| Datos | campo `data` | JSON del payload; cada `File` viaja sustituido por su token `file_<uuid>` |
| Archivos | campo `files` | una o más partes; el `filename` es `<token>___<realname>` |

**Forma del payload de alta** (`CrearProductoIn`):

```json
{
  "nombre": "Agua mineral",
  "slug": "agua-mineral",
  "precio": "3.50",
  "imagenes": [
    {"token": "file_aaa111", "es_principal": true, "texto_alternativo": "Frente"}
  ]
}
```

**Matching EXACTAMENTE UNA VEZ.** Cada token aparece **una sola vez** en el payload: por eso la imagen principal y el texto alternativo viajan DENTRO del objeto de la imagen y no en campos aparte (duplicar el token sería, correctamente, un token duplicado). El matching lo hace `core.media.resolver_tokens_media(payload, archivos)`, que:

| Situación | Código | Status |
|---|---|---|
| token del payload sin parte de archivo | `MEDIA_TOKEN_NO_RESUELTO` | 400 |
| parte de archivo que el payload no referencia | `MEDIA_ARCHIVO_HUERFANO` | 400 |
| token repetido en el payload o con dos partes | `MEDIA_TOKEN_DUPLICADO` | 400 |
| MIME fuera de allowlist o firma incoherente | `MEDIA_TIPO_NO_PERMITIDO` | 400 |
| tamaño > 5 MiB | `MEDIA_TAMANO_EXCEDIDO` | 413 |
| dimensiones fuera de rango (hook `GOV-01-OPEN-10`) | `MEDIA_DIMENSIONES_INVALIDAS` | 400 |

**Orden de los errores** (decidido explícitamente, no heredado): (1) `data` ausente o con JSON inválido → 422 `VALIDATION_ERROR` · (2) protocolo multipart → 400/413 `MEDIA_*` · (3) schema del payload → 422 `VALIDATION_ERROR` con `field_errors` · (4) contenido del archivo → 400/413 `MEDIA_*`.

**El módulo NO usa los helpers heredados** `core/types.py::hydrate_form` ni `parse_request_payload`: lanzan `HttpError` con texto interpolado y no usan los códigos de media del catálogo. Consume `core.media` (`parsear_archivos_media`, `resolver_tokens_media`, `validar_archivo_media`, `construir_ruta_media`, `limpiar_archivos_media`), como exige FND-01.

**UNA representación del archivo.** `ImagenProductoUploadData` (token + `UploadedFile` + MIME detectado + extensión + tamaño + nombre original) viaja desde el borde HTTP hasta el flujo dentro de `ProductoCreateData.imagenes`. No hay un segundo argumento de archivos en ninguna firma: el controller no vuelve a recibirlos y el flujo no los vuelve a pedir. El DTO interno lleva `datetime` (nunca cadenas) y `Decimal` (nunca `float`).

---

## 3. Catálogo, precios y ofertas

| Regla | Dónde vive | Evidencia |
|---|---|---|
| Coherencia de edición (producto y categoría en la MISMA edición) | `ProductoCoreService.crear` → `ProductoCategoriaIncoherenteError` (422) | `test_una_categoria_de_otra_edicion_se_rechaza` |
| Slug único POR EDICIÓN (categoría y producto) | `UniqueConstraint` en la base de datos | `test_el_slug_del_producto_es_unico_por_edicion`, `..._dentro_de_la_edicion` |
| Coherencia del precio y de la ventana de oferta | `ProductoCoreService.validar_oferta` → `OfertaInvalidaError` (422) | `test_una_ventana_de_oferta_invertida_se_rechaza` |
| **El precio efectivo lo decide el DOMINIO** | `Producto.oferta_activa()` / `Producto.precio_efectivo()` → viajan en el result | `test_el_precio_efectivo_lo_decide_el_dominio`, `test_el_result_expone_el_precio_efectivo` |
| Orden canónico de la galería `orden ASC, id ASC` | `ProductoImagen.Meta.ordering` | `test_el_orden_de_la_galeria_es_orden_por_id` |
| Una sola imagen principal por producto (campo EXPLÍCITO, nunca "la primera") | `es_principal` + `UniqueConstraint` condicional + validación en dominio | `test_solo_hay_una_imagen_principal_por_producto` |
| Un módulo lógico deshabilitado no expone catálogo ni escrituras (RN-E02) | `ProductoOrchestrator._resolver_actual_sync` → `ModuloNoHabilitadoError` (409) | `test_el_modulo_deshabilitado_no_expone_catalogo` |
| El cliente NUNCA elige la edición | el orquestador sustituye el `edicion_id` del payload por la edición resuelta | `test_alta_json_sin_imagenes` |

**El catálogo NO inventa existencias.** `Producto` no declara stock: el inventario es de DOM-06 (`MovimientoInventario`). El código `PRODUCTO_NO_DISPONIBLE` queda declarado y catalogado para `RT-CM-03` (DOM-05) y para la operación de stock (DOM-06), pero DOM-04 NO lo usa.

**Degradación por archivo ausente** (FR-06 §2.7): si el archivo ya no está en el volumen, la imagen viaja con `disponible = false` y `url = null`, y se registra una incidencia de media en el log. La galería NO lanza 500 ni oculta el hueco — `test_el_detalle_trae_la_galeria_ordenada`.

---

## 4. Limpieza de media — los tres caminos obligatorios (FR-06 §2.5)

| Camino | Comportamiento | Evidencia |
|---|---|---|
| **Validación fallida** | NO se escribe nada: la validación ocurre en el borde HTTP, antes de tocar el disco | `test_firma_de_contenido_invalida_se_rechaza`, `test_tamano_excedido_se_rechaza` |
| **Rollback de transacción** | Los archivos escritos durante la operación se BORRAN: la base se revierte sola, el volumen no | `test_un_rollback_deja_el_volumen_sin_residuos` |
| **Reemplazo de imagen** | El archivo anterior se borra DESPUÉS de que el nuevo quedó persistido; si el reemplazo falla, el anterior sigue en su sitio y el nuevo se limpia | `test_reemplazar_borra_el_archivo_anterior_despues_del_nuevo`, `test_un_reemplazo_fallido_conserva_el_archivo_anterior` |
| **Borrado de entidad** | Al borrar una imagen o un producto, sus archivos se borran | `test_borrar_una_imagen_borra_su_archivo`, `test_borrar_un_producto_borra_todos_sus_archivos` |

**Mecanismo.** `ProductoFlujo` registra la ruta ANTES de escribir (para que un fallo posterior no deje un huérfano) y la sustituye por la ruta real después (`get_available_name` puede desambiguar un choque de nombre). En el `except` del flujo se invoca `core.media.limpiar_archivos_media(rutas)`.

**Residuo cero, demostrado.** En todos los rechazos y en todos los rollbacks el volumen de test queda SIN archivos:

```
assert [ruta for ruta in media_root.rglob("*") if ruta.is_file()] == []
```

**El volumen real NO se toca.** Los tests apuntan `MEDIA_ROOT` a un directorio temporal (`fixture media_root`); después de las 35 pruebas, `Aplicacion/backend/media` **NO existe** y `Aplicacion/backend/db.sqlite3` **NO existe**.

**Ruta de almacenamiento** (FR-06 §2.2): `MEDIA_ROOT/productos/<producto_id>/<uuid><ext>`. El nombre enviado por el cliente se ignora (`upload_to` devuelve la ruta precalculada) y la extensión sale del MIME **detectado** (`.jpg` / `.png` / `.webp`). Comprobado en `test_alta_multipart_guarda_la_galeria_en_orden`.

---

## 5. Migraciones

| Migración | Contenido | Reversible |
|---|---|---|
| `modules/marketplace/migrations/0001_initial.py` | `CategoriaProducto`, `Producto`, `ProductoImagen` + 3 `UniqueConstraint` | sí (`migrate marketplace zero` → OK) |

Esquema físico verificado sobre un SQLite real:

| Restricción | Tipo |
|---|---|
| `marketplace_categoria_slug_unico_edicion` | UNIQUE `(edicion_id, slug)` |
| `marketplace_producto_slug_unico_edicion` | UNIQUE `(edicion_id, slug)` |
| `marketplace_imagen_principal_unica` | UNIQUE parcial `WHERE es_principal = 1` (índice parcial, `PRAGMA index_list` → `u=1, partial=1`) |

---

## 6. Comandos, exits y resultados

Entorno: workdir `Aplicacion/backend` · `.\\.venv\\Scripts\\python.exe` (Python 3.10.0, Django 5.2.11, Pydantic 2.12.5, pytest-django 4.9.0, ninja 1.5.3, ninja-extra 0.31.0, injector 0.24.0, Pillow 11.1.0).
Variable de entorno de todo el bloque: `DJANGO_SETTINGS_MODULE = "modules.marketplace.tests.settings_overlay"` (overlay idempotente; el registro permanente es de A0).

| # | Comando | Exit | Resultado |
|---|---|---|---|
| V1 | `python -m pytest modules/marketplace/tests -q -k "producto or imagen or multipart"` | **0** | **35 passed** |
| V2 | `python -m pytest modules/marketplace/tests -q` | **0** | **35 passed** |
| V3 | `python manage.py makemigrations --check --dry-run` | **0** | `No changes detected` |
| V4 | `python manage.py check` | **0** | `System check identified no issues` |
| V5 | `python manage.py migrate` (base SQLite en archivo) | **0** | `Applying marketplace.0001_initial... OK` |
| V6 | `python manage.py showmigrations marketplace` | **0** | `[X] 0001_initial` |
| V7 | `python manage.py migrate marketplace zero` | **0** | `Unapplying marketplace.0001_initial... OK` |
| V8 | `python manage.py migrate` (replay) | **0** | `Applying marketplace.0001_initial... OK` |
| V9 | `PRAGMA index_list` / `table_info` sobre el SQLite real | **0** | 3 restricciones presentes (ver §5) |
| V10 | `python -m pytest core/tests -q` | **0** | **100 passed** — baseline de FND-01 INTACTO |
| V11 | `python -m pytest -q --ignore=modules/salesianos_fest` (raíz completa del objetivo) | **0** | **329 passed** (294 de FND-05 + 35 de DOM-04), 0 fallos |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | vacío — raíz normativa intacta |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | vacío — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` (sin cambios) |
| R4 | `git status --short -- Aplicacion/backend` | **0** | la ÚNICA ruta nueva de este paquete es `modules/marketplace/` |
| R5 | `Test-Path Aplicacion/backend/media` · `db.sqlite3` · `test_db.sqlite3` | **0** | `False` `False` `False` — sin residuos |
| R6 | `git stash` / `git commit` | — | **nunca invocados** |

**Fallo de colección ajeno, NO es regresión.** `python -m pytest -q` sobre la raíz completa (sin `--ignore`) aborta con:

```
RuntimeError: Model class modules.salesianos_fest.domain.models.catalogo.Disciplina
doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

Es el módulo `modules/salesianos_fest/**`, propiedad de **DOM-01** (trabajo concurrente en curso): su app todavía no está registrada en `INSTALLED_APPS`, porque el registro permanente es una petición a A0 (igual que la de DOM-04). DOM-04 no lo tocó, no lo revirtió y no lo fusionó. V11 corre la raíz completa EXCLUYENDO ese módulo: **329 passed, 0 fallos**.

**Baseline conocido sin cambios:** los dos `manage.py` con los settings por defecto (`config.settings.production`, sin `DB_NAME`) siguen fallando con `DB_NAME` — idéntico a FND-01…FND-05. Con el overlay (o `--settings=config.settings.development`) ambos salen 0. Este paquete NO introduce fallos nuevos.

---

## 7. Peticiones a A0 (registradas, NO aplicadas)

Ningún archivo compartido fue editado por este paquete. Estas son las peticiones:

| # | Petición | Archivo de A0 | Prioridad |
|---|---|---|---|
| **A0-01** | Registrar la app: `INSTALLED_APPS += ["modules.marketplace"]` | `config/settings/base.py` | **BLOQUEANTE** |
| **A0-02** | Registrar el wiring de DI: `NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.marketplace.di.MarketplaceModule"]` | `config/settings/base.py` | **BLOQUEANTE** |
| **A0-03** | Registrar el controller: `registrar_controladores(ProductoController)` | `config/api.py` | **BLOQUEANTE** (sin esto las rutas no existen: FR-07 §3.1) |
| **A0-04** | **Añadir la entrada `default` a `STORAGES`** | `config/settings/base.py` | **BLOQUEANTE** — ver abajo |
| **A0-05** | Explicitar el tipo del dinero en el cable (`Decimal` → cadena) o corregir `_decimal_to_float` | `core/responses.py` | media |
| **A0-06** | Catalogar los códigos nuevos del módulo | `core/exceptions.py` | media |
| **A0-07** | Retirar el overlay `modules/marketplace/tests/settings_overlay.py` | — | con A0-01/A0-02 |

### A0-04 — `STORAGES` sin entrada `default` (defecto real del backend objetivo)

`config/settings/base.py` declara `STORAGES` con SÓLO la entrada `staticfiles`. Django 5 necesita también `default`; sin ella `default_storage` no existe y **ningún módulo puede escribir media**:

```
django.core.files.storage.handler.InvalidStorageError:
Could not find config for 'default' in settings.STORAGES.
```

El overlay de test replica el ajuste (`STORAGES.setdefault("default", FileSystemStorage)`) para que DOM-04 se pueda VERIFICAR, pero **el backend objetivo no puede persistir imágenes hasta que A0 lo aplique**. Es un defecto de A0, no de DOM-04, y bloquea el despliegue de la tienda (y el de patrocinadores, DOM-08).

### A0-06 — códigos nuevos que hay que catalogar

Ya están en el catálogo público: `MEDIA_TIPO_NO_PERMITIDO`, `MEDIA_TAMANO_EXCEDIDO`, `MEDIA_TOKEN_NO_RESUELTO`, `MEDIA_ARCHIVO_HUERFANO`, `MEDIA_TOKEN_DUPLICADO`, `MEDIA_DIMENSIONES_INVALIDAS`, `MODULO_NO_HABILITADO`.

Nuevos de DOM-04 (el `error.code` ya viaja estable y legible por máquina; sólo falta la prosa pública):

| Código | Status | Prosa propuesta |
|---|---|---|
| `PRODUCTO_NO_ENCONTRADO` | 404 | "No se encontró el producto solicitado." |
| `PRODUCTO_SLUG_DUPLICADO` | 409 | "Ya existe un producto con ese identificador en la edición." |
| `PRODUCTO_NO_DISPONIBLE` | 409 | "El producto seleccionado no está disponible." |
| `PRODUCTO_CATEGORIA_INCOHERENTE` | 422 | "La categoría indicada pertenece a otra edición." |
| `CATEGORIA_PRODUCTO_NO_ENCONTRADA` | 404 | "No se encontró la categoría de producto solicitada." |
| `CATEGORIA_PRODUCTO_SLUG_DUPLICADO` | 409 | "Ya existe una categoría con ese identificador en la edición." |
| `PRODUCTO_IMAGEN_NO_ENCONTRADA` | 404 | "No se encontró la imagen de producto solicitada." |
| `OFERTA_INVALIDA` | 422 | "La oferta indicada no es válida." |
| `GALERIA_INVALIDA` | 422 | "La galería del producto no es válida." |

### A0-05 — el dinero en el cable

`core/responses.py` serializa los `Decimal` como **cadena decimal** (`"3.50"`), no como número: `success_response()` llama `model_dump(mode="json")` (que en Pydantic v2 convierte el `Decimal` en texto) ANTES de que `_decimal_to_float` pueda actuar, y la clave de configuración `ser_json_decimal_to_float` **no existe en Pydantic v2** (se ignora en silencio). Es el comportamiento observable y CONGELADO del backend objetivo (afecta a todos los módulos con dinero). DOM-04 mantiene `Decimal` en el dominio y en el schema HTTP (el tipo correcto) y el test lo fija explícitamente; el espejo Zod de A7 tiene que reflejarlo. A0 debe decidir si la intención es el número (corregir el orden en `_decimal_to_float`) o la cadena (ratificarla).

---

## 8. Desviaciones y decisiones

| ID | Decisión | Por qué |
|---|---|---|
| `D-DOM04-01` | El módulo declara el puerto `IAlcanceEdicion` y el adaptador vive en `infrastructure/` | `eventos` está CONGELADO (FND-02) y DOM-04 no puede editarlo; el dominio no debe conocer el módulo que provee el dato. Es el mismo patrón de FND-05 (el consumidor declara el puerto) |
| `D-DOM04-02` | El alcance se resuelve con el nivel 3 (edición publicada ÚNICA) también para las ESCRITURAS | La edición publicada es única POR EVENTO (`UniqueConstraint` condicional), es la MISMA que la interfaz muestra (`GET /ediciones/actual`) y la ambigüedad es imposible por construcción. Ante ausencia o ambigüedad, la respuesta es un error del catálogo: nunca se opera sobre "la edición que haya" |
| `D-DOM04-03` | El cliente NUNCA elige la edición | El orquestador sustituye el `edicion_id` del payload por la edición resuelta. El payload HTTP ni siquiera declara `edicion_id` |
| `D-DOM04-04` | La galería viaja como lista de OBJETOS (`{token, es_principal, texto_alternativo}`) | Es la única forma de tener la imagen principal EXPLICÍTICA (FR-06 §2.6) manteniendo el matching exactamente-una-vez: duplicar el token en un campo aparte sería un token duplicado |
| `D-DOM04-05` | `es_principal` NO se asigna por posición | FR-06 §2.6 prohíbe "la primera imagen es la principal" implícito. Si no se declara, ninguna imagen es principal y la galería degrada con aviso |
| `D-DOM04-06` | El módulo NO declara stock | El inventario es de DOM-06. El catálogo no inventa existencias (SHOP-01) |
| `D-DOM04-07` | Se implementan 4 rutas (RT-MD-01, RT-MK-01/02/03) | Son las que el ledger (FR-07 §3.3) y el registro de rutas provisionales (SH-05 §1.6) asignan a `marketplace`. Las de pedido, stock y entrega son de DOM-05/DOM-06/DOM-08 |
| `D-DOM04-08` | Los helpers heredados `core/types.py` NO se usan | Lanzan `HttpError` con texto interpolado y no usan los códigos de media. FND-01 los dejó intactos a propósito: el consumo es de `core.media` |
| `D-DOM04-09` | El overlay de settings replica también el ajuste de `STORAGES` | Sin él no se puede verificar el paquete. Es la réplica de A0-04, y el overlay se retira cuando A0 aplique el registro permanente |
| `D-DOM04-10` | El wire del dinero es la CADENA decimal | Es el comportamiento congelado del envelope (`core/responses.py`). Se registra en A0-05 |
| `D-DOM04-11` | `precio_oferta` MAYOR que `precio` NO se rechaza | Es una política comercial, no una incoherencia estructural. Queda como decisión abierta de A5 + producto (`OD-DOM04-01`) |
| `D-DOM04-12` | El módulo no crea ni borra categorías por HTTP | El ledger no declara una ruta de escritura de categorías para `marketplace`; la capability de dominio existe (`ProductoFlujo.crear_categoria`) para DOM-05/DOM-06 y para A0 si abre la ruta |

### Decisiones abiertas que este paquete deja declaradas

| ID | Pregunta | Owner |
|---|---|---|
| `OD-DOM04-01` | ¿Puede una oferta ser MAYOR que el precio normal? (hoy se permite) | A5 + producto |
| `OD-DOM04-02` | ¿Se permite una oferta sin ventana temporal? (hoy sí: `precio_oferta` sin `oferta_inicia`/`oferta_termina` la hace vigente desde ya) | A5 + producto |
| `OD-DOM04-03` | Límites exactos de dimensiones por tipo de imagen | `GOV-01-OPEN-10` (A0 + A5) |
| `OD-DOM04-04` | Política de copia de seguridad del volumen | `GOV-01-OPEN-09` (A0 + producto) |
| `OD-DOM04-05` | ¿Se abre una ruta HTTP de escritura de categorías (`RT-MK-xx`)? | A0 + A7 (ledger) |

---

## 9. Rollback

El rollback es de ALCANCE DE PAQUETE y NO toca el media del usuario:

1. `python manage.py migrate marketplace zero` (desaplica `0001_initial`; verificado OK).
2. Borrar `Aplicacion/backend/modules/marketplace/**` (todo el paquete es nuevo: no hay archivo previo que restituir).
3. Retirar el overlay `modules/marketplace/tests/settings_overlay.py` (lo retira A0 con A0-01/A0-02).
4. Revertir `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (sólo la fila DOM-04 y la transición) y los topics de Engram.
5. **NO tocar** `Aplicacion/backend/media/`: el volumen es estado durable y puede contener media de otros paquetes o del usuario. Este paquete sólo crea media en directorios temporales de test, que pytest borra.

**Punto de rollback:** `f3df5401c56b41c340f257e67d5a306904a9e670` (sin cambios; este paquete NO creó commit y `git stash` nunca se invocó).

**Restauración del media de test:** los archivos de los tests viven bajo `%TEMP%/pytest-of-<usuario>/pytest-*/test_*/media/` y los borra pytest. El volumen real del proyecto nunca se escribió (R5: `Aplicacion/backend/media` → `False`).

---

## 10. Preparación de los paquetes siguientes

| Paquete | Estado tras DOM-04 | Qué le falta |
|---|---|---|
| **DOM-05** (pedido de marketplace) | **Listo para empezar** | El catálogo, los precios/ofertas autoritativos, la galería ordenada y `PRODUCTO_NO_DISPONIBLE` ya existen. DOM-05 implementa `RT-CM-03` (`POST /marketplace/pedidos`), el `Pedido`/`PedidoDetalle` con snapshot de precio (RN-M03) y la reserva de stock. Depende del modelo de existencias de DOM-06 |
| **DOM-08** (patrocinadores) | **Parcialmente listo** | El contrato de media (`core/media.py`) y el protocolo quedan CONSUMIDOS por DOM-04: DOM-08 usa `core.media` con el MISMO protocolo y el MISMO código `MEDIA_*`. Reutiliza el `ProductoHydrator` como patrón (no como código: son dominios distintos) |
| **DOM-06** (inventario/entrega) | **Sin cambios** | `Producto` NO declara stock a propósito; DOM-06 puede añadirlo con una migración aditiva (`002_*`) sin romper `0001_initial` |
| **API-03 / API-04** | **Esperando A0-01…A0-04** | El espejo Zod 1:1 necesita el tipo del dinero ratified (A0-05) |
| **XCT-03** | **Parcialmente listo** | El protocolo, la limpieza y los códigos de media están implementados y probados; falta la política de despliegue (A0-04, `GOV-01-OPEN-09`) |
| **UI-02…UI-05** | **Sin cambios** | Las rutas del catálogo (`SHOP-01`, `SHOP-02`) ya tienen contrato: `RT-MK-01/02/03` |

**Concurrencia preservada.** `Aplicacion/backend/modules/salesianos_fest/**` (DOM-01) y `Aplicacion/frontend/**` (FND-06 / UI-01A) NO fueron tocados, revertidos ni fusionados por este paquete.
