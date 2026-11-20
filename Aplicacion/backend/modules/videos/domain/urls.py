"""El invariante de la URL de un video.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.2, §10

Este módulo es el ÚNICO dueño de la regla "la URL de un video es una
dirección `http` o `https`". Es lógica de DOMINIO puro: no toca la base de
datos ni depende de Django, así que el servicio de dominio y el esquema HTTP
pueden consultarlo y NO pueden divergir.

Por qué la regla vive aquí y no en un `if` suelto:

- `javascript:`, `data:` y `ftp:` no son direcciones de video. Aceptarlos
  abre la puerta a que un enlace se interprete como código en el navegador.
- El validador por defecto de Django (`URLValidator`) admite `ftp`/`ftps`: la
  lista explícita de esquemas es la que hace falta.
- El backend NUNCA renderiza HTML: devuelve la URL como dato. La decisión de
  cómo presentarla (archivo, embed permitido o enlace externo) es del
  cliente, con su propia lista blanca de proveedores.
"""

from urllib.parse import urlsplit

#: Los ÚNICOS esquemas que puede tener la URL de un video.
ESQUEMAS_PERMITIDOS = ("http", "https")


def es_url_http_valida(url: str) -> bool:
    """Si la URL es una dirección `http`/`https` con host.

    `urlsplit` no lanza excepción con una entrada cualquiera: devuelve un
    esquema vacío para lo que no es una URL, y eso ya es un rechazo.
    """
    if not isinstance(url, str):
        return False

    try:
        partes = urlsplit(url.strip())
    except ValueError:
        return False

    if partes.scheme.lower() not in ESQUEMAS_PERMITIDOS:
        return False

    return bool(partes.netloc)


__all__ = [
    "ESQUEMAS_PERMITIDOS",
    "es_url_http_valida",
]
