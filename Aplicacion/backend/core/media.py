"""Contrato de multimedia del backend Salesianos FEST.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`

Este módulo es el ÚNICO lugar donde vive la política de media del backend. Los
módulos de dominio (`marketplace`, `patrocinadores`) lo CONSUMEN; no lo
reimplementan.

Qué fija este módulo:

| Aspecto | Regla |
|---|---|
| Raíz | `MEDIA_ROOT` — volumen **persistente**. Es estado durable, no un caché |
| URL | `MEDIA_URL` — sin CDN |
| Ruta | `MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><ext>` |
| Nombre | **Nunca** el nombre enviado por el usuario: se deriva de un UUID del servidor |
| Extensión | Se deriva del MIME **detectado**, nunca del declarado |
| Allowlist MIME | `image/jpeg`, `image/png`, `image/webp` (`image/svg+xml` PROHIBIDO) |
| Tamaño máximo | 5 MiB por archivo (configurable) |
| Firma | Se validan los bytes mágicos contra el MIME declarado, ANTES de persistir |
| Dimensiones | Hook activo cuando hay límites configurados (ver `GOV-01-OPEN-10`) |
| Protocolo multipart | `data` (JSON con tokens `file_<uuid>`) + `files` (`<token>___<realname>`) |
| Rechazos | token ausente, archivo huérfano y token duplicado, con códigos estables |
| Limpieza | Obligatoria en validación fallida, rollback, reemplazo y borrado |

Expectativas de persistencia, respaldo y limpieza:

- **Persistencia.** `MEDIA_ROOT` se monta como volumen persistente del
  despliegue. Un archivo escrito es estado de negocio: no se borra por cache
  miss y no se regenera.
- **Respaldo (backup).** La política de copia de seguridad del volumen está
  PENDIENTE de ratificación (`GOV-01-OPEN-09`, owner A0 + producto). Este
  módulo NO inventa ni fija credenciales, rutas remotas ni ventanas: expone
  el interruptor `MEDIA_BACKUP_ENABLED` para que la política se active cuando
  esté definida, y el comportamiento por defecto es "sin copia" (fail-safe
  explícito, no silencioso).
- **Limpieza (cleanup).** Un archivo nunca se escribe antes de ser validado.
  Si la validación falla, no hay nada que borrar. Si la escritura ocurre y la
  transacción posterior falla, el llamador debe invocar `limpiar_archivos_media`
  con las rutas escritas. Borrar un archivo huérfano en el volumen es
  obligatorio: el volumen no es un caché.

Este módulo NO escribe en disco ni abre transacciones: valida, decide y
resuelve. La escritura y la transacción son del módulo de dominio.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from core.exceptions import (
    MediaArchivoHuerfanoError,
    MediaDimensionesInvalidasError,
    MediaTamanoExcedidoError,
    MediaTokenDuplicadoError,
    MediaTokenNoResueltoError,
    MediaTipoNoPermitidoError,
)

logger = logging.getLogger(__name__)

# ── Constantes del contrato ──────────────────────────────────────────────────

#: Patrón del token de archivo del protocolo multipart (`FILE_KEY_PATTERN`).
TOKEN_PATTERN = re.compile(r"^file_[A-Za-z0-9_-]+$")

#: Separador entre el token y el nombre real dentro del nombre de la parte.
TOKEN_SEPARATOR = "___"

#: Extensión storage por MIME detectado.
EXTENSIONES_POR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

#: Bytes mágicos por MIME. La firma manda sobre el `Content-Type` declarado.
_FIRMAS = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)

#: Cuántos bytes se leen para detectar la firma de contenido.
_BYTES_DE_FIRMA = 12


# ── Configuración efectiva (leída en cada llamada) ────────────────────────────


def media_root() -> Path:
    """Raíz persistente del volumen de media."""
    return Path(settings.MEDIA_ROOT)


def media_url() -> str:
    """URL pública del volumen de media."""
    return str(settings.MEDIA_URL)


def allowed_mime_types() -> frozenset[str]:
    """Allowlist MIME vigente."""
    return frozenset(settings.MEDIA_ALLOWED_MIME_TYPES)


def max_size_bytes() -> int:
    """Tamaño máximo por archivo, en bytes."""
    return int(settings.MEDIA_MAX_SIZE_BYTES)


def allowed_domains() -> frozenset[str]:
    """Dominios (primer segmento de la ruta) autorizados."""
    return frozenset(settings.MEDIA_DOMAINS)


def min_dimension() -> int:
    """Dimensión mínima en píxeles. `0` desactiva la validación."""
    return int(settings.MEDIA_MIN_DIMENSION)


def max_dimension() -> int:
    """Dimensión máxima en píxeles. `0` desactiva la validación."""
    return int(settings.MEDIA_MAX_DIMENSION)


# ── Detección y validación ───────────────────────────────────────────────────


def detect_mime_type(head: bytes) -> str | None:
    """Detecta el MIME real a partir de los bytes mágicos.

    Devuelve `None` cuando la firma no corresponde a ningún tipo permitido.
    Nunca confía en el `Content-Type` declarado por el cliente.
    """
    if not head:
        return None
    for firma, mime in _FIRMAS:
        if head.startswith(firma):
            return mime
    if len(head) >= _BYTES_DE_FIRMA and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def extension_for_mime(mime: str) -> str:
    """Extensión storage normalizada para el MIME detectado."""
    try:
        return EXTENSIONES_POR_MIME[mime]
    except KeyError:  # pragma: no cover - defensa; la allowlist lo impide
        raise MediaTipoNoPermitidoError() from None


@dataclass(frozen=True)
class MediaValidado:
    """Resultado de validar un archivo de media en el borde HTTP."""

    mime_detectado: str
    extension: str
    tamano: int
    nombre_original: str

    @property
    def nombre_extension(self) -> str:
        """Nombre storage derivado del MIME detectado (nunca del cliente)."""
        return f"{uuid.uuid4().hex}{self.extension}"


def _leer_firma(upload: UploadedFile) -> bytes:
    """Lee los primeros bytes del archivo y rebobina el cursor."""
    position = None
    try:
        position = upload.tell()
    except Exception:  # pragma: no cover - algunos streams no soportan tell
        position = None
    try:
        head = upload.read(_BYTES_DE_FIRMA) or b""
    finally:
        try:
            upload.seek(position if position is not None else 0)
        except Exception:  # pragma: no cover
            pass
    return head


def _leer_dimensiones(upload: UploadedFile) -> tuple[int, int] | None:
    """Dimensiones (ancho, alto) del archivo, o `None` si no se pueden leer."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow es dependencia del proyecto
        logger.warning("Pillow no disponible: no se validan dimensiones de media.")
        return None

    position = None
    try:
        position = upload.tell()
    except Exception:  # pragma: no cover
        position = None
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            return image.size
    except Exception as exc:
        logger.warning("No se pudieron leer las dimensiones del archivo: %s", exc)
        return None
    finally:
        try:
            upload.seek(position if position is not None else 0)
        except Exception:  # pragma: no cover
            pass


def validar_archivo_media(upload: UploadedFile) -> MediaValidado:
    """Valida un archivo de media ANTES de persistirlo.

    Orden de las comprobaciones (FR-06 §2.3):

    1. tamaño máximo;
    2. MIME declarado dentro de la allowlist;
    3. firma de contenido coherente con el MIME declarado;
    4. dimensiones, cuando hay límites configurados.

    El nombre declarado por el cliente no se usa para nada: la extensión
    sale del MIME **detectado**.
    """
    if upload is None:
        raise MediaTipoNoPermitidoError()

    tamano = int(getattr(upload, "size", 0) or 0)
    if tamano > max_size_bytes():
        raise MediaTamanoExcedidoError()

    declarado = (getattr(upload, "content_type", "") or "").split(";")[0].strip().lower()
    permitidos = allowed_mime_types()
    if declarado not in permitidos:
        raise MediaTipoNoPermitidoError()

    detectado = detect_mime_type(_leer_firma(upload))
    if detectado is None or detectado not in permitidos:
        raise MediaTipoNoPermitidoError()
    if detectado != declarado:
        # `Content-Type` mentiroso: se rechaza igual que un tipo no permitido.
        raise MediaTipoNoPermitidoError()

    _validar_dimensiones(upload)

    return MediaValidado(
        mime_detectado=detectado,
        extension=extension_for_mime(detectado),
        tamano=tamano,
        nombre_original=str(getattr(upload, "name", "") or ""),
    )


def _validar_dimensiones(upload: UploadedFile) -> None:
    """Valida las dimensiones cuando hay límites configurados.

    Los límites exactos por tipo están PENDIENTES (`GOV-01-OPEN-10`); con los
    valores por defecto (`0`) la comprobación no hace nada.
    """
    minimo = min_dimension()
    maximo = max_dimension()
    if minimo <= 0 and maximo <= 0:
        return

    dimensiones = _leer_dimensiones(upload)
    if dimensiones is None:
        raise MediaDimensionesInvalidasError()

    ancho, alto = dimensiones
    if minimo > 0 and (ancho < minimo or alto < minimo):
        raise MediaDimensionesInvalidasError()
    if maximo > 0 and (ancho > maximo or alto > maximo):
        raise MediaDimensionesInvalidasError()


# ── Ruta de almacenamiento ───────────────────────────────────────────────────


def construir_ruta_media(dominio: str, entidad_id: Any, extension: str) -> str:
    """Ruta relativa dentro de `MEDIA_ROOT`.

        MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><extension>

    - El nombre NUNCA es el enviado por el usuario.
    - `entidad_id` permite localizar y limpiar los archivos de una entidad sin
      recorrer el volumen.
    """
    if dominio not in allowed_domains():
        raise ValueError(f"dominio de media no permitido: {dominio!r}")

    if not extension.startswith("."):
        extension = f".{extension}"

    return f"{dominio}/{entidad_id}/{uuid.uuid4().hex}{extension}"


def ruta_absoluta_media(ruta_relativa: str) -> Path:
    """Ruta absoluta en disco de una ruta relativa de media."""
    return media_root() / ruta_relativa


def url_publica_media(ruta_relativa: str) -> str:
    """URL pública de una ruta relativa de media."""
    base = media_url()
    if not base.endswith("/"):
        base = f"{base}/"
    return f"{base}{ruta_relativa.lstrip('/')}"


def limpiar_archivos_media(rutas: Iterable[str]) -> list[str]:
    """Borra los archivos escritos y devuelve las rutas eliminadas.

    Se invoca en los caminos de limpieza obligatoria: validación fallida
    (nada escrito), rollback de la transacción, reemplazo de imagen y borrado
    de la entidad. El borrado es best-effort: un archivo que no se puede
    borrar queda registrado en el log, nunca se ignora en silencio.
    """
    eliminadas: list[str] = []
    for ruta in rutas or []:
        absoluta = ruta_absoluta_media(ruta)
        try:
            if absoluta.exists():
                absoluta.unlink()
                eliminadas.append(ruta)
        except OSError as exc:
            logger.error(
                "No se pudo eliminar el archivo de media %s: %s", ruta, exc
            )
    return eliminadas


# ── Protocolo multipart ──────────────────────────────────────────────────────


def parsear_archivos_media(request_files: Any) -> dict[str, UploadedFile]:
    """Convierte las partes de archivo en `{token: archivo}`.

    Cada parte se llama `<token>___<realname>`. Una parte sin ese formato no
    tiene token resoluble y se rechaza con `MEDIA_TOKEN_NO_RESUELTO`.
    """
    if request_files is None:
        return {}

    if hasattr(request_files, "getlist"):
        # Un MultiValueDict sin la clave "files" NO es un error: es una
        # petición sin archivos.
        try:
            partes = request_files.getlist("files")
        except KeyError:
            partes = []
    elif isinstance(request_files, dict) and "files" in request_files:
        partes = request_files["files"]
    else:
        partes = []

    if not isinstance(partes, (list, tuple)):
        partes = [partes]

    mapeados: dict[str, UploadedFile] = {}
    for parte in partes:
        nombre = getattr(parte, "name", "") or ""
        if TOKEN_SEPARATOR not in nombre:
            raise MediaTokenNoResueltoError()
        token, nombre_real = nombre.split(TOKEN_SEPARATOR, 1)
        if not TOKEN_PATTERN.match(token):
            raise MediaTokenNoResueltoError()
        if token in mapeados:
            raise MediaTokenDuplicadoError()
        try:
            parte.name = nombre_real
        except Exception:  # pragma: no cover - streams inmutables
            pass
        mapeados[token] = parte

    return mapeados


def _tokens_del_payload(payload: Any) -> list[str]:
    """Tokens de archivo referenciados por el payload, en orden de aparición."""
    tokens: list[str] = []

    def _recorrer(nodo: Any) -> None:
        if isinstance(nodo, dict):
            for valor in nodo.values():
                _recorrer(valor)
        elif isinstance(nodo, (list, tuple)):
            for valor in nodo:
                _recorrer(valor)
        elif isinstance(nodo, str) and TOKEN_PATTERN.match(nodo):
            tokens.append(nodo)

    _recorrer(payload)
    return tokens


def resolver_tokens_media(
    payload: Any, archivos: dict[str, UploadedFile]
) -> dict[str, UploadedFile]:
    """Resuelve los tokens de archivo del payload contra las partes recibidas.

    Cierra la brecha de archivos huérfanos que el código heredado no
    detectaba (FR-06 §2.4):

    - token del payload sin parte correspondiente → `MEDIA_TOKEN_NO_RESUELTO`;
    - parte de archivo que ningún campo referencia → `MEDIA_ARCHIVO_HUERFANO`;
    - token repetido en el payload o con dos partes → `MEDIA_TOKEN_DUPLICADO`.
    """
    tokens = _tokens_del_payload(payload)

    vistos: set[str] = set()
    for token in tokens:
        if token in vistos:
            raise MediaTokenDuplicadoError()
        vistos.add(token)
        if token not in archivos:
            raise MediaTokenNoResueltoError()

    huerfanos = [token for token in archivos if token not in vistos]
    if huerfanos:
        raise MediaArchivoHuerfanoError()

    return {token: archivos[token] for token in tokens}


__all__ = [
    "EXTENSIONES_POR_MIME",
    "TOKEN_PATTERN",
    "TOKEN_SEPARATOR",
    "MediaValidado",
    "allowed_domains",
    "allowed_mime_types",
    "construir_ruta_media",
    "detect_mime_type",
    "extension_for_mime",
    "limpiar_archivos_media",
    "max_size_bytes",
    "max_dimension",
    "media_root",
    "media_url",
    "min_dimension",
    "parsear_archivos_media",
    "resolver_tokens_media",
    "ruta_absoluta_media",
    "url_publica_media",
    "validar_archivo_media",
]
