"""
PersonaResolucionFlujo — flujo async de la resolución EXACTA de una identidad.

Resuelve la `Persona` que YA EXISTE en la aplicación a partir de su
identidad civil. Es el complemento del lookup externo de documento
(`PersonaBusquedaFlujo`): aquel consulta RENIEC/SUNAT y NO conoce el id
interno de la aplicación; este devuelve el id de una persona ya registrada.

Reglas del flujo:
1. la coincidencia es EXACTA: `(tipo_documento, numero_documento)` y nada
   más — no hay búsqueda difusa ni listado;
2. la consulta es de LECTURA: el flujo NUNCA crea ni modifica una `Persona`;
3. la ausencia de la persona es un error TIPADO (404), no una lista vacía;
4. el resultado lleva SOLO el id, el nombre y el documento ya consultado.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.usuarios.domain.constants import TipoDocumentoChoices
from modules.usuarios.domain.exceptions import (
    PersonaNoEncontradaError,
    TipoDocumentoInvalidoError,
)
from modules.usuarios.domain.results import PersonaResueltaResult
from modules.usuarios.domain.selectors import PersonaSelector


def _normalizar_tipo_documento(tipo_documento: str) -> str:
    """Normaliza el tipo de documento: sin espacios y en mayúsculas."""
    return (tipo_documento or "").strip().upper()


def _normalizar_numero_documento(numero_documento: str) -> str:
    """Normaliza el número de documento: sin espacios alrededor.

    El número NO se modifica más allá de los espacios: un pasaporte es
    alfanumérico y la identidad civil es EXACTA.
    """
    return (numero_documento or "").strip()


class PersonaResolucionFlujo:
    """
    Flujo async de la resolución exacta de una identidad registrada.
    """

    @inject
    def __init__(self, persona_selector: PersonaSelector):
        self.persona_selector = persona_selector

    async def _proceso_resolver(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> PersonaResueltaResult:
        """
        Resuelve la `Persona` que corresponde EXACTAMENTE al documento.

        Args:
            tipo_documento: Tipo de documento (DNI, CE, PAS).
            numero_documento: Número de documento.

        Returns:
            PersonaResueltaResult con el id, el nombre y el documento.

        Raises:
            TipoDocumentoInvalidoError: el tipo de documento no pertenece al
                vocabulario cerrado de la identidad (422).
            PersonaNoEncontradaError: no hay una `Persona` registrada con
                ese documento exacto (404).
        """
        tipo = _normalizar_tipo_documento(tipo_documento)
        numero = _normalizar_numero_documento(numero_documento)

        if tipo not in TipoDocumentoChoices.values:
            raise TipoDocumentoInvalidoError()

        persona = await sync_to_async(self.persona_selector.obtener_por_documento)(
            tipo,
            numero,
        )

        if persona is None:
            raise PersonaNoEncontradaError()

        return PersonaResueltaResult(
            persona_id=str(persona.id),
            nombre_completo=f"{persona.nombres} {persona.apellidos}".strip(),
            tipo_documento=persona.tipo_documento,
            numero_documento=persona.numero_documento,
        )
