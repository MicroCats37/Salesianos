"""
Puertos (interfaces) del módulo `usuarios`.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3 · `contratos/03` §3.

Sólo hay UN puerto: la consulta a la fuente externa de documentos. El
servicio HTTP concreto vive en `infrastructure/services.py`; los tests
inyectan un doble por el grafo de fixtures
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §6: prohibido `unittest.mock.patch`).

El puerto devuelve ESTADOS TIPADOS, no excepciones de red: quien lo consume
decide qué estado es reintentable y cuál no (`FR-03` §3.3).
"""

from abc import ABC, abstractmethod

from modules.usuarios.domain.results import ConsultaDocumentoResultado


class IConsultaDocumentoClient(ABC):
    """Consulta de identidad civil en una fuente documental externa."""

    @abstractmethod
    async def consultar(
        self,
        numero_documento: str,
    ) -> ConsultaDocumentoResultado:
        """Consulta el documento y devuelve el estado tipado de la respuesta.

        La fuente recibe el documento CRUDO y devuelve el tipo que reconoce:
        es ella quien decide qué vocabulario aplica. El módulo de identidad
        compara ese tipo con el solicitado.

        NUNCA inventa una identidad: si la fuente falla, devuelve
        `FUENTE_NO_DISPONIBLE` o `TIMEOUT`.
        """
        ...


__all__ = ["IConsultaDocumentoClient"]
