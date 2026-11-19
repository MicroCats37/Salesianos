"""
`PersonaResolucionFlujo` — resolver local → fuente externa.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §3 · `FL-02` · `RN-U03`.

Es async y ABRE la transacción cuando la operación confirma una identidad
(`contract/django-app-architecture-contract.md` §4.4,
`contract/PLAN_REFACTORIZACION.md` §4 — el `@transaction.atomic` vive aquí y
en ningún otro sitio). El resolver de consulta NO escribe nada.

Reglas congeladas que implementa este flujo:

1. **Orden obligatorio**: primero local; la fuente externa SÓLO si no existe
   localmente (`FR-03` §3.2 regla 1).
2. **Persistencia diferida**: una `Persona` externa se persiste únicamente al
   confirmar la operación real (`FR-03` §3.2 regla 2).
3. **Anti-duplicado**: la confirmación va por `UniqueConstraint` + reintento
   CONTROLADO ante `IntegrityError`; nunca con `get_or_create` silencioso
   (`FR-03` §3.2 regla 3).
4. **Prohibido usar el resolver para validar titularidad** (`FR-03` §3.2
   regla 6): este flujo no conoce la titularidad y jamás devuelve una
   credencial.
"""

import logging
from datetime import datetime, timezone

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.usuarios.domain.constants import (
    EstadoConsultaDocumentoChoices,
    OrigenDatosChoices,
    OrigenResolucionChoices,
)
from modules.usuarios.domain.exceptions import (
    PersonaDuplicadaError,
    PersonaNoEncontradaError,
)
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.ports import IConsultaDocumentoClient
from modules.usuarios.domain.results import (
    ConsultaDocumentoResultado,
    PersonaDatosExternos,
    PersonaResolucionResult,
)
from modules.usuarios.domain.schemas import (
    PersonaConfirmarData,
    PersonaCreateData,
    normalizar_numero_documento,
    normalizar_tipo_documento,
)
from modules.usuarios.domain.selectors import PersonaSelector, UsuarioSelector
from modules.usuarios.domain.services.core.persona_core_service import (
    PersonaCoreService,
)

logger = logging.getLogger(__name__)

#: Intentos de creación ante una carrera perdida.
INTENTOS_CREACION = 3


def separar_nombre_completo(nombre_completo: str) -> tuple[str, str]:
    """Separa el nombre completo en `(apellidos, nombres)`.

    La fuente externa entrega el nombre completo en formato
    `"APELLIDOS, NOMBRES"`. Cuando el separador no existe NO se inventa el
    reparto: el nombre completo va a `nombres` y los apellidos quedan vacíos
    (`FR-03` §3.2 — está prohibido fabricar identidades).
    """
    bruto = str(nombre_completo or "").strip()
    if not bruto:
        return "", ""
    if "," in bruto:
        izquierda, derecha = bruto.split(",", 1)
        return izquierda.strip(), derecha.strip()
    return "", bruto


class PersonaResolucionFlujo:
    """Resolución de una identidad por documento."""

    @inject
    def __init__(
        self,
        consulta_documento_client: IConsultaDocumentoClient,
        persona_core_service: PersonaCoreService,
        persona_selector: PersonaSelector,
        usuario_selector: UsuarioSelector,
    ):
        self.consulta_documento_client = consulta_documento_client
        self.persona_core_service = persona_core_service
        self.persona_selector = persona_selector
        self.usuario_selector = usuario_selector

    # ── Consulta ───────────────────────────────────────────────────────────

    async def buscar_local(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> PersonaResolucionResult:
        """Busca la identidad SÓLO en la base local.

        Es el primer paso obligatorio del resolver: si la persona ya existe,
        la fuente externa no se consulta nunca (`FR-03` §3.2 regla 1).
        """
        tipo = normalizar_tipo_documento(tipo_documento)
        numero = normalizar_numero_documento(numero_documento)
        persona = await sync_to_async(self.persona_selector.obtener_por_documento)(
            tipo,
            numero,
        )
        if persona is None:
            return PersonaResolucionResult(origen=OrigenResolucionChoices.LOCAL)
        return PersonaResolucionResult(
            origen=OrigenResolucionChoices.LOCAL,
            persona=persona,
            persona_id=str(persona.id),
        )

    async def consultar_externa(
        self,
        numero_documento: str,
    ) -> ConsultaDocumentoResultado:
        """Consulta la fuente externa y devuelve su estado tipado.

        NUNCA fabrica una identidad: si la fuente falla, el estado lo dice.
        """
        numero = normalizar_numero_documento(numero_documento)
        if not numero:
            raise PersonaNoEncontradaError()
        return await self.consulta_documento_client.consultar(numero)

    async def resolver(
        self,
        tipo_documento: str,
        numero_documento: str,
    ) -> PersonaResolucionResult:
        """Resuelve el documento: primero local, después la fuente externa.

        Devuelve el resultado con ORIGEN EXPLÍCITO. Los fallos NO se lanzan
        aquí: se expresan como origen + estado, y el orquestador los traduce
        a las excepciones de dominio con código estable (`FR-03` §3.1).
        """
        tipo = normalizar_tipo_documento(tipo_documento)
        numero = normalizar_numero_documento(numero_documento)

        local = await self.buscar_local(tipo, numero)
        if local.es_local and local.persona is not None:
            return local

        consulta = await self.consultar_externa(numero)

        if consulta.estado == EstadoConsultaDocumentoChoices.ENCONTRADO:
            if consulta.tipo_documento and consulta.tipo_documento != tipo:
                # La fuente reconoce el documento con otro tipo: para el tipo
                # pedido ese documento NO existe.
                return PersonaResolucionResult(
                    origen=OrigenResolucionChoices.NO_ENCONTRADO,
                    estado=EstadoConsultaDocumentoChoices.NO_ENCONTRADO,
                )
            apellidos, nombres = separar_nombre_completo(consulta.nombre_completo)
            if not nombres:
                return PersonaResolucionResult(
                    origen=OrigenResolucionChoices.FUENTE_NO_DISPONIBLE,
                    estado=EstadoConsultaDocumentoChoices.DATOS_INCOMPLETOS,
                )
            return PersonaResolucionResult(
                origen=OrigenResolucionChoices.EXTERNO,
                datos=PersonaDatosExternos(
                    tipo_documento=tipo,
                    numero_documento=numero,
                    nombres=nombres,
                    apellidos=apellidos,
                ),
                estado=EstadoConsultaDocumentoChoices.ENCONTRADO,
            )

        if consulta.estado == EstadoConsultaDocumentoChoices.NO_ENCONTRADO:
            return PersonaResolucionResult(
                origen=OrigenResolucionChoices.NO_ENCONTRADO,
                estado=EstadoConsultaDocumentoChoices.NO_ENCONTRADO,
            )

        # Timeout, fuente caída o datos incompletos: el origen es la fuente
        # externa y el estado fino queda disponible para el llamador.
        return PersonaResolucionResult(
            origen=OrigenResolucionChoices.FUENTE_NO_DISPONIBLE,
            estado=consulta.estado,
        )

    # ── Confirmación (la operación real que persiste) ──────────────────────

    async def confirmar(self, data: PersonaConfirmarData) -> Persona:
        """Confirma la identidad y PERSISTE la `Persona`.

        Éste es el único camino que escribe una `Persona` derivada de la
        fuente externa. La escritura es segura ante peticiones concurrentes
        con el mismo documento (`RN-U03`).
        """
        if data.origen_datos == OrigenDatosChoices.EXTERNO.value and (
            data.datos_obtenidos_en is None
        ):
            data = data.model_copy(
                update={"datos_obtenidos_en": datetime.now(timezone.utc)}
            )
        return await sync_to_async(self._confirmar_sync)(data)

    def _confirmar_sync(self, data: PersonaConfirmarData) -> Persona:
        """Escritura atómica de la identidad confirmada.

        Anti-duplicado concurrente (`FR-03` §3.2 regla 3): la `UniqueConstraint`
        de la base de datos es la autoridad. Quien pierde la carrera NO
        falla: vuelve a leer la fila ganadora y devuelve ESA persona. No se
        usa `get_or_create` silencioso, que ocultaría la carrera.
        """
        payload = PersonaCreateData(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
            genero=data.genero,
            origen_datos=data.origen_datos,
            datos_obtenidos_en=data.datos_obtenidos_en,
        )

        for _ in range(INTENTOS_CREACION):
            try:
                with transaction.atomic():
                    persona = self.persona_core_service.crear(payload)
            except IntegrityError:
                # Carrera perdida: la fila ganadora ya existe.
                existente = self.persona_core_service.obtener_por_documento(
                    payload.tipo_documento,
                    payload.numero_documento,
                )
                if existente is None:
                    # La fila desapareció entre el fallo y la relectura:
                    # se reintenta la creación.
                    continue
                if self._tiene_cuenta(existente):
                    # La identidad ya está vinculada a una cuenta: no se
                    # reescribe ni se duplica (`FR-03` §1.2).
                    raise PersonaDuplicadaError()
                return existente

            if self._tiene_cuenta(persona):
                raise PersonaDuplicadaError()
            return persona

    def _tiene_cuenta(self, persona: Persona) -> bool:
        """Si la identidad ya está vinculada a una cuenta (`FR-03` §1.2).

        El acceso inverso `persona.usuario` de un `OneToOneField` nullable
        lanza `RelatedObjectDoesNotExist` cuando no hay cuenta, así que la
        comprobación va por el selector.
        """
        return self.usuario_selector.obtener_por_persona(str(persona.id)) is not None

        logger.warning(
            "No se pudo confirmar la identidad tras %s intentos.",
            INTENTOS_CREACION,
        )
        raise PersonaDuplicadaError()


__all__ = [
    "INTENTOS_CREACION",
    "PersonaResolucionFlujo",
    "separar_nombre_completo",
]
