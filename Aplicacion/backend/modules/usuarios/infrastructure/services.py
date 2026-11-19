"""
Adaptador HTTP de la fuente externa de documentos.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3 · `contratos/03` §3.

Contrato de la fuente (el microservicio `worker/scraper`, ya existente y
independiente — `Aplicacion/documentacion/01-arquitectura-y-runtime.md` §8):

    GET {SCRAPER_URL}/consultar/{documento}
      200 → {"tipo_documento": str, "numero_documento": str, "razon_social": str}
      404 → el documento no existe
      422 → el documento no tiene un formato válido para la fuente
      502 → la fuente cambió de formato
      503 → la fuente no está disponible
      504 → la fuente no respondió a tiempo

Este adaptador NO inventa credenciales ni payloads: traduce los estados HTTP
a los estados tipados del dominio. Si la fuente no está configurada, NO se
fabrica una identidad: se informa `FUENTE_NO_DISPONIBLE`, que es
RECUPERABLE (`contratos/03` §7).
"""

import logging
import os

import httpx

from modules.usuarios.domain.constants import EstadoConsultaDocumentoChoices
from modules.usuarios.domain.ports import IConsultaDocumentoClient
from modules.usuarios.domain.results import ConsultaDocumentoResultado

logger = logging.getLogger(__name__)

#: Variable de entorno con la URL base de la fuente de documentos.
ENV_BASE_URL = "SCRAPER_URL"

#: Timeout por defecto de la consulta externa (segundos).
TIMEOUT_DEFAULT = 10.0


class ConsultaDocumentoClient(IConsultaDocumentoClient):
    """Cliente HTTP de la fuente externa de documentos."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self._base_url = base_url
        self._timeout = timeout if timeout is not None else TIMEOUT_DEFAULT

    # ── Configuración ──────────────────────────────────────────────────────

    def _resolver_base_url(self) -> str:
        """URL base de la fuente externa, o cadena vacía si no hay ninguna.

        Se lee de `settings.SCRAPER_URL` cuando existe y, si no, de la
        variable de entorno. NO hay valor por defecto: sin fuente
        configurada el resolver informa `FUENTE_NO_DISPONIBLE` en vez de
        adivinar una dirección.
        """
        if self._base_url:
            return self._base_url.rstrip("/")
        try:
            from django.conf import settings

            desde_settings = getattr(settings, "SCRAPER_URL", "")
        except Exception:  # pragma: no cover - settings no configurados
            desde_settings = ""
        base = desde_settings or os.environ.get(ENV_BASE_URL, "")
        return str(base).rstrip("/")

    # ── Consulta ───────────────────────────────────────────────────────────

    async def consultar(self, numero_documento: str) -> ConsultaDocumentoResultado:
        """Consulta el documento en la fuente externa."""
        base_url = self._resolver_base_url()
        if not base_url:
            logger.info(
                "Fuente externa de documentos no configurada (%s ausente).",
                ENV_BASE_URL,
            )
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE,
                numero_documento=str(numero_documento or ""),
            )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as cliente:
                respuesta = await cliente.get(
                    f"/consultar/{numero_documento}",
                    headers={"Accept": "application/json"},
                )
        except httpx.TimeoutException:
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.TIMEOUT,
                numero_documento=str(numero_documento or ""),
            )
        except httpx.HTTPError:
            logger.warning("Fallo de red consultando la fuente de documentos.")
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE,
                numero_documento=str(numero_documento or ""),
            )

        return self._traducir(respuesta, numero_documento)

    # ── Traducción de la respuesta ─────────────────────────────────────────

    @staticmethod
    def _traducir(
        respuesta: httpx.Response,
        numero_documento: str,
    ) -> ConsultaDocumentoResultado:
        """Traduce la respuesta HTTP al estado tipado del dominio.

        El cuerpo del proveedor NUNCA se propaga: sólo se leen los campos del
        contrato y el resto se queda en el log.
        """
        documento = str(numero_documento or "")

        if respuesta.status_code == 200:
            try:
                datos = respuesta.json()
            except ValueError:
                logger.warning("Respuesta no JSON de la fuente de documentos.")
                return ConsultaDocumentoResultado(
                    estado=EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS,
                    numero_documento=documento,
                )
            nombre = str(datos.get("razon_social") or "").strip()
            if not nombre:
                return ConsultaDocumentoResultado(
                    estado=EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS,
                    tipo_documento=str(datos.get("tipo_documento") or ""),
                    numero_documento=str(datos.get("numero_documento") or documento),
                )
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
                tipo_documento=str(datos.get("tipo_documento") or ""),
                numero_documento=str(datos.get("numero_documento") or documento),
                nombre_completo=nombre,
            )

        if respuesta.status_code == 404:
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.NO_ENCONTRADO,
                numero_documento=documento,
            )

        if respuesta.status_code == 422:
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS,
                numero_documento=documento,
            )

        if respuesta.status_code == 504:
            return ConsultaDocumentoResultado(
                estado=EstadoConsultaDocumentoChoices.TIMEOUT,
                numero_documento=documento,
            )

        # 500 / 502 / 503 y cualquier otro status: la fuente no entregó una
        # identidad utilizable. Es RECUPERABLE, no un "no encontrado".
        logger.warning(
            "La fuente de documentos respondió %s para una consulta.",
            respuesta.status_code,
        )
        return ConsultaDocumentoResultado(
            estado=EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE,
            numero_documento=documento,
        )


__all__ = ["ENV_BASE_URL", "TIMEOUT_DEFAULT", "ConsultaDocumentoClient"]
