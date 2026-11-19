"""
`PersonaOrchestrator` — fachada async de la identidad.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3 · `FR-07` (rutas `RT-ID-02`, `RT-ID-03`).

Es DELGADA: un método por endpoint, y sólo delega en el flujo
(`contract/django-app-architecture-contract.md` §4.5).

Su única responsabilidad propia es traducir el ORIGEN del resultado del
resolver a las EXCEPCIONES DE DOMINIO con código estable. El controller nunca
construye respuestas de error (`contract/api-wrapper-presenter-contract.md`
§8): el catálogo público de `core/exceptions.py` convierte el código en prosa
pública.
"""

from injector import inject

from modules.usuarios.domain.constants import (
    EstadoConsultaDocumentoChoices,
    OrigenResolucionChoices,
)
from modules.usuarios.domain.exceptions import (
    FuenteExternaNoDisponibleError,
    FuenteExternaTimeoutError,
    PersonaDatosIncompletosError,
    PersonaNoEncontradaError,
)
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.results import (
    ConsultaDocumentoResultado,
    PersonaResolucionResult,
)
from modules.usuarios.domain.schemas import PersonaConfirmarData
from modules.usuarios.domain.services.flujos.persona_resolucion_flujo import (
    PersonaResolucionFlujo,
)


class PersonaOrchestrator:
    """Fachada async de las operaciones de identidad."""

    @inject
    def __init__(self, flujo: PersonaResolucionFlujo):
        self.flujo = flujo

    # ── RT-ID-02 · resolver ────────────────────────────────────────────────

    async def resolver(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> PersonaResolucionResult:
        """Resuelve el documento y traduce el fallo a excepción de dominio."""
        result = await self.flujo.resolver(tipo_documento, numero_documento)
        self._traducir_fallo(result)
        return result

    # ── RT-ID-01 · consulta externa ────────────────────────────────────────

    async def consultar_externa(self, documento: str) -> ConsultaDocumentoResultado:
        """Consulta la fuente externa por documento.

        La fuente decide qué tipo reconoce; el módulo devuelve el estado
        tipado tal cual.
        """
        consulta = await self.flujo.consultar_externa(documento)
        if consulta.estado == EstadoConsultaDocumentoChoices.NO_ENCONTRADO:
            raise PersonaNoEncontradaError()
        if consulta.estado == EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS:
            raise PersonaDatosIncompletosError()
        if consulta.estado == EstadoConsultaDocumentoChoices.TIMEOUT:
            raise FuenteExternaTimeoutError()
        if consulta.estado == EstadoConsultaDocumentoChoices.FUENTE_NO_DISPONIBLE:
            raise FuenteExternaNoDisponibleError()
        return consulta

    # ── RT-ID-03 · confirmar ────────────────────────────────────────────────

    async def confirmar(self, data: PersonaConfirmarData) -> Persona:
        """Confirma la identidad y la persiste."""
        return await self.flujo.confirmar(data)

    # ── Traducción de fallos ───────────────────────────────────────────────

    @staticmethod
    def _traducir_fallo(result: PersonaResolucionResult) -> None:
        """Convierte un origen fallido en la excepción de dominio estable.

        - `NO_ENCONTRADO` → 404 `PERSONA_NO_ENCONTRADA` (no reintentable).
        - `TIMEOUT` → 504 `FUENTE_EXTERNA_TIMEOUT` (reintentable).
        - `DATOS_INCOMPLETOS` → 422 `PERSONA_DATOS_INCOMPLETOS`.
        - resto → 503 `FUENTE_EXTERNA_NO_DISPONIBLE` (reintentable).
        """
        if result.origen == OrigenResolucionChoices.NO_ENCONTRADO:
            raise PersonaNoEncontradaError()
        if result.origen != OrigenResolucionChoices.FUENTE_NO_DISPONIBLE:
            return
        if result.estado == EstadoConsultaDocumentoChoices.TIMEOUT:
            raise FuenteExternaTimeoutError()
        if result.estado == EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS:
            raise PersonaDatosIncompletosError()
        raise FuenteExternaNoDisponibleError()


__all__ = ["PersonaOrchestrator"]
