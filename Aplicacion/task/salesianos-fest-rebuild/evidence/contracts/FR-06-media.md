# FR-06 — Interfaz de multimedia (imágenes)

**Freeze:** `FREEZE-MD-1.0.0` · **Propietario:** A0 (settings/media) + A5 (marketplace) + A8 (patrocinadores) · **Estado:** FROZEN (GOV-01)
**Trazabilidad:** `DEC-13`, `DEC-14`, `DEC-15`, `DEC-17` · `RN-M02`, `RN-M04`, `RN-M05` · plan `contratos/03-integraciones-y-eventos-internos.md` §5, `funcional/03` §4, `implementacion/01` §1

---

## 1. Estado actual verificado (código congelado, solo lectura)

| Hecho | Ubicación verificada |
|---|---|
| `MEDIA_URL = "/media/"` | `backend/config/settings/base.py:130` |
| `MEDIA_ROOT = BASE_DIR / "media"` | `backend/config/settings/base.py:131` |
| Los media se sirven con `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` | `backend/config/urls.py:25` |
| **No existe ningún `ImageField` ni `upload_to` en el backend** | búsqueda sobre `backend/**/*.py`: 0 coincidencias de `ImageField` / `upload_to` |
| Protocolo multipart ya implementado | `backend/core/utils.py:13` (`FILE_KEY_PATTERN = ^file_[A-Za-z0-9_-]+$`), `:16-50` (`parse_grouped_files`), `:53-93` (`hydrate_and_clean_payload`) |
| Emisor del protocolo en el frontend | `frontend/src/utils/payload-builder.ts:52-99` |

**Conclusión:** la infraestructura de media (settings, URL, servicio) **existe**; el **almacenamiento en el dominio no**. No hay `ProductoImagen` ni `PatrocinadorImagen` implementados. Este freeze define la interfaz que ambos módulos deben cumplir.

## 2. Decisiones congeladas

### 2.1 Almacenamiento

| Aspecto | Regla congelada |
|---|---|
| Tipo de campo | Django `ImageField` (`funcional/03` §4). **Prohibido** storing el binario en el JSON de la API |
| Raíz | `MEDIA_ROOT` como volumen **persistente**. El valor de la clave no cambia en el objetivo |
| URL | `MEDIA_URL` sin cambios. Sin CDN (`DEC-14`) |
| Exposición | Servicio/servidor de archivos del despliegue, con controles de tamaño, tipo y extensión |
| Copia de seguridad | **Responsabilidad de la arquitectura local**, no de este freeze → `GOV-01-OPEN-09` |

### 2.2 Ruta de almacenamiento — patrón único

```
MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><extension>
```

| `<dominio>` | Valores permitidos |
|---|---|
| `productos` | `Producto` y `ProductoImagen` |
| `patrocinadores` | `Patrocinador` (logo) y `PatrocinadorImagen` |

Reglas:

1. **Prohibido** usar el nombre de archivo enviado por el usuario. El nombre se deriva del `uuid` generado en el servidor.
2. La **extensión** se deriva del tipo MIME **detectado**, nunca de la extensión declarada.
3. `entidad_id` es el id del dueño. Permite localizar y limpiar los archivos de una entidad sin recorrer el volumen.
4. El patrón es idéntico para todos los módulos de imágenes: **un solo contrato de subida y almacenamiento local** (`implementacion/01` §3).

### 2.3 Validación — obligatoria antes de persistir

| Regla | Detalle |
|---|---|
| Allowlist MIME | `image/jpeg`, `image/png`, `image/webp`. **Prohibido** `image/svg+xml` (script embebido) |
| Tamaño máximo | 5 MiB por archivo |
| Firma de contenido | Se validan los bytes mágicos del archivo contra el MIME declarado. Un `Content-Type` mentiroso se rechaza con `400 MEDIA_TIPO_NO_PERMITIDO` |
| Extensión | La extensión storage se normaliza a la del tipo detectado |
| Validación de dimensiones | Anchura y altura mínimas y máximas por tipo. Pixel bomb → rechazo |

**Prohibido** persistir un archivo antes de validar su contenido. La validación ocurre en el borde HTTP (controller/servicio), **antes** de tocar el disco.

### 2.4 Protocolo multipart — forma congelada

La implementación existente es **decisiva** (`backend/core/utils.py` + `frontend/src/utils/payload-builder.ts`). Este freeze la fija como contrato:

| Parte | Nombre | Contenido |
|---|---|---|
| Datos | campo `data` | JSON serializado del payload, con cada `File` sustituido por el token `file_<uuid>` |
| Archivos | campo `files` | **una o más** partes. El `filename` de cada parte es `<token>___<realname>` |

| Regla | Comportamiento |
|---|---|
| Patrón del token | `^file_[A-Za-z0-9_-]+$` (`FILE_KEY_PATTERN`) |
| Token ausente en `data` | **Rechazo** `400 MEDIA_TOKEN_NO_RESUELTO`. Hoy el backend lanza `HttpError(400, "Referencia de archivo rota: …")`; el objetivo debe convertirlo al código estable `MEDIA_TOKEN_NO_RESUELTO` desde el catálogo público |
| Archivo huérfano (parte `files` sin token en `data`) | **Rechazo** `400 MEDIA_ARCHIVO_HUERFANO`. **Hoy este caso NO se rechaza**: `parse_grouped_files` indexa el token pero `hydrate_and_clean_payload` nunca lo consulta. Es una brecha de implementación que FND-01 debe cerrar |
| Token duplicado | `400 MEDIA_TOKEN_DUPLICADO` |
| Archivo sin token en ninguna parte | `400 MEDIA_TOKEN_NO_RESUELTO` |
| Un solo archivo por campo | El objetivo admite `0..N` archivos por entidad (galería ordenada). El orden lo fija `orden`, no el nombre del archivo |

### 2.5 Limpieza — obligatoria en todos los caminos

| Situación | Acción |
|---|---|
| Validación fallida (MIME, tamaño, firma) | No se escribe nada. Si ya se había escrito, se borra |
| Rollback de transacción | Los archivos escritos durante la transacción se eliminan |
| Reemplazo de imagen | Se borra el archivo anterior **después** de que el nuevo quedó persistido con éxito |
| Borrado de la entidad | Se borran sus archivos |
| Error de activación de derechos | No aplica: media no participa de la activación |

**Prohibido** dejar archivos huérfanos en el volumen. El volume es estado durable, no un caché.

### 2.6 Imágenes ordenadas

| Entidad | Campo | Regla |
|---|---|---|
| `ProductoImagen` | `producto_id`, `imagen` (`ImageField`), `orden`, timestamps | `orden` entero. El orden canónico es `orden ASC, id ASC` |
| `Patrocinador` | `logo` (`ImageField`) | Imagen única de identidad |
| `PatrocinadorImagen` | `patrocinador_id`, `imagen` (`ImageField`), `orden`, timestamps | Galería ordenada |

**Prohibido** "la primera imagen es la principal" implícito. Si se requiere una imagen principal, es un campo explícito (`es_principal?` en `funcional/03` §1) con `UniqueConstraint` condicional por entidad.

### 2.7 Degradación por archivo ausente

`contratos/03` §7: si la foto deja de existir en disco, la galería **degrada con aviso** y se registra una incidencia de media. No se lanza un error 500 ni se oculta el hueco.

## 3. Módulos que consumen la interfaz

| Módulo | Uso | Owner |
|---|---|---|
| `marketplace` | `ProductoImagen` (0..N), `Producto.logo` opcional | A5 |
| `patrocinadores` | `Patrocinador.logo`, `PatrocinadorImagen` (0..N) | A8 |
| `inscripciones` / `pases` | Sin imágenes en esta versión | — |

## 4. Consumo del freeze

| Consumidor | Depende de | Acción |
|---|---|---|
| FND-01 (`T-016`) | este freeze | `MEDIA_ROOT`/`MEDIA_URL`, validación MIME/tamaño/firma, rechazo de huérfanos, limpieza en rollback, y el helper de subida único |
| DOM-04 (`T-040`) | `T-010`, `T-016` | `CategoriaProducto`, `Producto`, `ProductoImagen` con el patrón de ruta y el orden |
| DOM-08 (`T-060`) | `T-010`, `T-016` | `Patrocinador`, `PatrocinadorImagen` |
| XCT-03 (`T-085`) | `T-016`, `T-018` | Volumen persistente, permisos de media, respaldo, y pruebas de integración de multipart |

## 5. Criterios de aceptación de este freeze

- [x] Ruta de almacenamiento única, sin nombre de usuario, con extensión derivada del tipo detectado.
- [x] Allowlist MIME, tamaño máximo y validación de firma antes de persistir.
- [x] Protocolo multipart fijado en la forma que el código ya implementa (`data` + `files` con `<token>___<realname>`).
- [x] Token ausente, archivo huérfano y token duplicado con códigos de error estables.
- [x] Limpieza obligatoria en validación fallida, rollback, reemplazo y borrado.
- [x] La brecha verificada de archivos huérfanos queda registrada como deuda de FND-01.

## 6. Decisiones abiertas relacionadas

| ID | Pendiente | Owner |
|---|---|---|
| `GOV-01-OPEN-09` | Política de copia de seguridad, permisos del volumen y manejo de nombres eliminados | A0 + producto |
| `GOV-01-OPEN-10` | Límites exactos de dimensiones por tipo de imagen | A0 + A5 |
