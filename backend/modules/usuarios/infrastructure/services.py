"""Infrastructure services — external integrations for usuarios module."""

import hashlib
import random
from datetime import date

import httpx

from modules.usuarios.domain.exceptions import ReniecNotFoundError, SunatNotFoundError
from modules.usuarios.domain.ports import IConsultaExternaClient
from modules.usuarios.domain.results import ConsultaDocumentoResult


class ConsultaExternaSimulator(IConsultaExternaClient):
    """Simulador determinístico para consultas DNI/RUC sin depender del scraper."""

    _SUNAT_SIMULADOS = {
        "20492913151": {"razon_social": "MUNICIPALIDAD PROVINCIAL DE LIMA"},
        "20131312957": {"razon_social": "COLEGIO DE INGENIEROS DEL PERU"},
        "20600099773": {"razon_social": "CONSORCIO CAM LIMA NORTE"},
    }

    _SUNAT_RAZONES_SOCIALES = [
        "EMPRESA CONSTRUCTORA",
        "SERVICIOS GENERALES",
        "INDUSTRIA MANUFACTURERA",
        "COMERCIO AL POR MAYOR",
        "COMERCIO AL POR MENOR",
        "TRANSPORTES Y LOGISTICA",
        "SERVICIOS PROFESIONALES",
        "AGRICULTURA Y GANADERIA",
        "PESCA Y ACUICULTURA",
        "MINERIA Y CANTERAS",
        "ENERGIA Y AGUA",
        "CONSTRUCCION",
        "HOSTELERIA Y RESTAURACION",
        "ACTIVIDADES INMOBILIARIAS",
        "EDUCACION",
        "SALUD",
        "ENTRETENIMIENTO",
        "ADMINISTRACION PUBLICA",
    ]

    _RENIEC_SIMULADOS = {
        "45406196": {
            "nombre_completo": "ZARATE TORRES, DENNIS JOEL",
            "fecha_nacimiento": date(1986, 8, 24),
        },
        "12345678": {
            "nombre_completo": "PEREZ GOMEZ, CARLOS MANUEL",
            "fecha_nacimiento": date(1990, 3, 15),
        },
        "87654321": {
            "nombre_completo": "LOPEZ SANCHEZ, MARIA ELENA",
            "fecha_nacimiento": date(1983, 11, 7),
        },
    }

    _RENIEC_NOMBRES = [
        "JUAN",
        "CARLOS",
        "MIGUEL",
        "LUIS",
        "JOSE",
        "MARIA",
        "ELENA",
        "ANA",
        "PATRICIA",
        "LORENA",
        "FERNANDO",
        "RODRIGO",
        "VERONICA",
        "CARMEN",
        "FRANCISCO",
    ]

    _RENIEC_APELLIDOS = [
        "GARCIA",
        "PEREZ",
        "LOPEZ",
        "SANCHEZ",
        "RODRIGUEZ",
        "MARTINEZ",
        "TORRES",
        "RAMIREZ",
        "FLORES",
        "VARGAS",
        "HUAMAN",
        "QUISPE",
        "MENDOZA",
        "CASTILLO",
        "JIMENEZ",
    ]

    async def consultar_documento(self, documento: str) -> ConsultaDocumentoResult:
        length = len(documento)

        if length == 11:
            return await self._consultar_ruc(documento)
        if length == 8:
            return await self._consultar_dni(documento)

        return ConsultaDocumentoResult(
            tipo_documento="DESCONOCIDO",
            numero_documento=documento,
            razon_social="",
        )

    async def _consultar_ruc(self, ruc: str) -> ConsultaDocumentoResult:
        data = self._SUNAT_SIMULADOS.get(ruc)
        if data:
            return ConsultaDocumentoResult(
                tipo_documento="RUC",
                numero_documento=ruc,
                razon_social=data["razon_social"],
            )

        seed = int(hashlib.md5(ruc.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        return ConsultaDocumentoResult(
            tipo_documento="RUC",
            numero_documento=ruc,
            razon_social=f"{rng.choice(self._SUNAT_RAZONES_SOCIALES)} S.A.C.",
        )

    async def _consultar_dni(self, dni: str) -> ConsultaDocumentoResult:
        data = self._RENIEC_SIMULADOS.get(dni)
        if data:
            return ConsultaDocumentoResult(
                tipo_documento="DNI",
                numero_documento=dni,
                razon_social=data["nombre_completo"],
            )

        seed = int(hashlib.md5(dni.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        nombres = f"{rng.choice(self._RENIEC_NOMBRES)} {rng.choice(self._RENIEC_NOMBRES)}"
        apellidos = f"{rng.choice(self._RENIEC_APELLIDOS)} {rng.choice(self._RENIEC_APELLIDOS)}"
        return ConsultaDocumentoResult(
            tipo_documento="DNI",
            numero_documento=dni,
            razon_social=f"{apellidos}, {nombres}",
        )


class RealConsultaExternaClient(IConsultaExternaClient):
    """Cliente real del microservicio scraper de documentos."""

    def __init__(self):
        self._base_url = "http://scraper:8001"
        self._timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=5.0)

    async def consultar_documento(self, documento: str) -> ConsultaDocumentoResult:
        from core.exceptions import HttpError
        import os

        base_url = os.environ.get("SCRAPER_URL", self._base_url)

        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=self._timeout) as client:
                response = await client.get(f"/consultar/{documento}")
        except httpx.ConnectTimeout:
            raise HttpError(503, "No se pudo conectar al scraper de documentos")
        except httpx.ReadTimeout:
            raise HttpError(504, "Timeout esperando respuesta del scraper")
        except httpx.ConnectError:
            raise HttpError(503, "Scraper de documentos no disponible — verifique que el servicio esté corriendo")
        except httpx.HTTPError as e:
            raise HttpError(503, f"Error de red con el scraper: {e}")

        if response.status_code == 200:
            data = response.json()
            return ConsultaDocumentoResult(
                tipo_documento=data["tipo_documento"],
                numero_documento=data["numero_documento"],
                razon_social=data["razon_social"],
            )

        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        detail = body.get("detail", "Sin detalle")
        error_code = body.get("error", "UNKNOWN")

        if response.status_code == 404:
            if len(documento) == 8:
                raise ReniecNotFoundError(documento)
            raise SunatNotFoundError(documento)

        if response.status_code == 422:
            raise HttpError(422, f"Documento inválido: {detail}")
        if response.status_code == 504:
            raise HttpError(504, f"Portal de documentos no respondió a tiempo: {detail}")
        if response.status_code == 502:
            raise HttpError(502, f"Formato del portal cambió [{error_code}]: {detail}")
        if response.status_code == 503:
            raise HttpError(503, f"Portal de documentos no disponible [{error_code}]: {detail}")

        raise HttpError(response.status_code, f"Error inesperado del scraper: {detail}")
