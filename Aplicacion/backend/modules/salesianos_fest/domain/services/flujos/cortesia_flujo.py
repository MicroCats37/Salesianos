"""`CortesiaFlujo` — el otorgamiento de una CORTESÍA (derecho gratuito auditado).

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC,
ABREN `transaction.atomic()`.

Este flujo implementa `FL-07` ("Otorgar cortesía administrativa") y las
reglas congeladas que lo acompañan.

**RN-P05 — La cortesía registra actor, fecha y motivo; NO simula un cobro de
S/ 0.** Este flujo no toca `commerce` ni `pagos`: no crea compra, ni orden de
pago, ni transacción. La garantía es ESTRUCTURAL (`CortesiaPase` no tiene
ninguna columna que la enlace a un hecho financiero), no una convención de
código.

**FL-07 paso 2 — El backend registra el derecho gratuito con auditoría.** El
actor es la cuenta autenticada del administrador; el motivo es obligatorio.

**RN-P07 — La cortesía NO puede duplicar un derecho.** La misma persona no
puede tener un derecho ACTIVO de ese pase en esa edición, comprada o de
cortesía: la restricción parcial única de la base de datos es la autoridad.

**LO QUE NO SE INVENTA:** qué tipos de pase admiten cortesía. `FL-07` paso 1
dice "selecciona entrada permitida", pero el plan no congela esa lista: este
paquete NO la inventa y deja la decisión declarada (`OD-DOM03-03`).
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.salesianos_fest.domain.constants import (
    MAX_LEN_MOTIVO_CORTESIA,
    MIN_LEN_MOTIVO_CORTESIA,
    EstadoDerechoPase,
)
from modules.salesianos_fest.domain.exceptions import (
    ActorRequeridoError,
    CortesiaMotivoInvalidoError,
    CortesiaNoEncontradaError,
    PaseDuplicadoError,
    PaseNoDisponibleError,
    PersonaNoEncontradaError,
)
from modules.salesianos_fest.domain.ports import (
    IObtensionPersonaService,
    IResolucionPersonaService,
)
from modules.salesianos_fest.domain.results.pase_result import (
    AdminCortesiaListItemResult,
    AdminCortesiaListaResult,
    AdminCortesiaRevocadaResult,
    CortesiaPaseResult,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import (
    OtorgarCortesiaData,
    RevocarCortesiaData,
)
from modules.salesianos_fest.domain.selectors.cortesia_selector import CortesiaSelector
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.cortesia_core_service import (
    CortesiaCoreService,
)


class CortesiaFlujo:
    """El otorgamiento y la revocación de una cortesía."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        cortesia_core: CortesiaCoreService,
        resolucion_persona: IResolucionPersonaService,
        obtencion_persona: IObtensionPersonaService,
        cortesia_selector: CortesiaSelector,
    ):
        self.pase_selector = pase_selector
        self.cortesia_core = cortesia_core
        self.resolucion_persona = resolucion_persona
        self.obtencion_persona = obtencion_persona
        self.cortesia_selector = cortesia_selector

    async def otorgar_cortesia(
        self,
        data: OtorgarCortesiaData,
        actor=None,
    ) -> CortesiaPaseResult:
        """Registra una cortesía: acta auditada + derecho de entrada.

        Returns:
            El acta de la cortesía.

        Raises:
            ActorRequeridoError: la cortesía requiere una cuenta auditada.
            CortesiaMotivoInvalidoError: el motivo falta o es demasiado
                corto. Sin motivo no hay auditoría (`RN-P05`).
            PaseDuplicadoError: la persona ya tiene un derecho activo de ese
                pase.
        """
        if actor is None or not getattr(actor, "is_authenticated", False):
            raise ActorRequeridoError()

        motivo = self._validar_motivo(data.motivo)
        pase = await sync_to_async(self._resolver_pase)(data.edicion_id, data.pase_id)
        persona = await sync_to_async(self._resolver_persona)(data)
        actor_usuario_id, actor_persona_id = await sync_to_async(self._actor_ids)(actor)

        try:
            cortesia, derecho = await sync_to_async(self._crear_sync)(
                pase,
                persona,
                motivo,
                actor_usuario_id,
                actor_persona_id,
            )
        except IntegrityError as error:
            # La restricción parcial ÚNICA de la base de datos es la
            # autoridad del «no duplicar el derecho». Se traduce FUERA de la
            # transacción para que el acta no quede a medias.
            if self._es_duplicado(error):
                raise PaseDuplicadoError() from error
            raise

        return await sync_to_async(self._construir_resultado)(cortesia, derecho)

    @staticmethod
    def _construir_resultado(cortesia, derecho) -> CortesiaPaseResult:
        """Proyecta las relaciones ORM antes de volver al contexto async.

        El `derecho_id` es el del DERECHO que se acaba de crear en la misma
        transacción que el acta: la credencial de puerta se emite contra él.
        """
        return CortesiaPaseResult(
            id=str(cortesia.id),
            derecho_id=str(derecho.id),
            edicion_id=str(cortesia.edicion_id),
            edicion_nombre=cortesia.edicion.nombre,
            pase_id=str(cortesia.pase_id),
            pase_nombre=cortesia.pase.nombre,
            persona_id=str(cortesia.persona_id),
            persona_nombres=cortesia.persona.nombres,
            persona_tipo_documento=cortesia.persona.tipo_documento,
            persona_numero_documento=cortesia.persona.numero_documento,
            estado=cortesia.estado,
            motivo=cortesia.motivo,
            actor_usuario_id=(
                str(cortesia.actor_usuario_id)
                if cortesia.actor_usuario_id
                else None
            ),
            actor_nombres=(
                cortesia.actor_persona.nombres if cortesia.actor_persona else ""
            ),
            concedido_en=cortesia.concedido_en,
            revocado_en=cortesia.revocado_en,
        )

    # ── Internos (sync) ─────────────────────────────────────────────────────

    async def listar_cortesias(
        self,
        edicion_id=None,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AdminCortesiaListaResult:
        """El listado administrativo de actas de cortesía.

        El listado NUNCA expone el token de ninguna compra ni el detalle de
        un pago: son hechos de otros dominios.
        """
        return await sync_to_async(self._construir_cortesias)(
            edicion_id,
            estado,
            page,
            page_size,
        )

    def _construir_cortesias(
        self,
        edicion_id,
        estado,
        page: int,
        page_size: int,
    ) -> AdminCortesiaListaResult:
        """Proyecta el listado administrativo de cortesías."""
        page = max(1, int(page or 1))
        page_size = max(1, min(int(page_size or 25), 100))
        total = self.pase_selector.contar_cortesias(edicion_id, estado)
        offset = (page - 1) * page_size
        actas = list(
            self.pase_selector.listar_cortesias(edicion_id, estado)[
                offset : offset + page_size
            ]
        )
        return AdminCortesiaListaResult(
            items=[
                AdminCortesiaListItemResult(
                    id=str(cortesia.id),
                    derecho_id=self._derecho_id_de(cortesia),
                    pase_nombre=cortesia.pase.nombre,
                    edicion_nombre=cortesia.edicion.nombre,
                    persona_nombres=cortesia.persona.nombres,
                    persona_tipo_documento=cortesia.persona.tipo_documento,
                    persona_numero_documento=cortesia.persona.numero_documento,
                    estado=cortesia.estado,
                    motivo=cortesia.motivo,
                    actor_nombres=(
                        cortesia.actor_persona.nombres
                        if cortesia.actor_persona
                        else ""
                    ),
                    concedido_en=cortesia.concedido_en,
                )
                for cortesia in actas
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if total else 0,
        )

    @staticmethod
    def _derecho_id_de(cortesia) -> str | None:
        """El identificador del DERECHO de una cortesía, o `None`.

        La credencial de puerta se emite contra el DERECHO, no contra el
        acta: el listado tiene que publicar su identificador para que la
        acción exista de verdad.

        La elección es DETERMINISTA: primero el derecho ACTIVO; si la cortesía
        fue revocada y ya no queda ninguno activo, el más reciente. Un acta
        SIN derecho (corrupción histórica) publica `None`: el identificador
        ausente NUNCA se inventa.

        Los derechos vienen PREFETCHEADOS por el selector: aquí no se consulta
        la base de datos, y el listado NO hace una consulta por fila.
        """
        derechos = list(cortesia.derechos.all())
        if not derechos:
            return None

        activo = next(
            (
                derecho
                for derecho in derechos
                if derecho.estado == EstadoDerechoPase.ACTIVO
            ),
            None,
        )
        elegido = activo or derechos[0]
        return str(elegido.id)

    @staticmethod
    def _validar_motivo(motivo: str) -> str:
        """El motivo es obligatorio y tiene una longitud mínima.

        El texto que se guarda es el que el administrador escribió: es un
        dato de auditoría, no un mensaje público. El cÓDIGO del error es lo
        que decide la prosa que ve el cliente.
        """
        texto = str(motivo or "").strip()
        if len(texto) < MIN_LEN_MOTIVO_CORTESIA:
            raise CortesiaMotivoInvalidoError()
        return texto[:MAX_LEN_MOTIVO_CORTESIA]

    def _resolver_pase(self, edicion_id, pase_id):
        """El pase que se otorga, DENTRO de la edición del alcance.

        El pase tiene que EXISTIR en esa edición (`RN-E01`). No se exige que
        esté `VIGENTE`: una cortesía puede otorgar un pase retirado del
        catálogo, y el pase existente no deja de ser válido por eso.
        """
        pase = self.pase_selector.obtener_pase(edicion_id, pase_id)
        if pase is None:
            raise PaseNoDisponibleError()
        return pase

    def _resolver_persona(self, data: OtorgarCortesiaData):
        """La persona que recibe la cortesía."""
        if data.persona_id:
            persona = self.resolucion_persona.resolver_por_id(data.persona_id)
            if persona is None:
                raise PersonaNoEncontradaError()
            return persona

        if not data.tipo_documento or not data.numero_documento:
            raise PersonaNoEncontradaError()

        return self.obtencion_persona.obtener_o_registrar(
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            nombres=data.nombres,
            apellidos=data.apellidos,
        )

    @staticmethod
    def _actor_ids(actor):
        """Los identificadores del actor, para la auditoría."""
        if actor is None or not getattr(actor, "is_authenticated", False):
            return None, None
        persona_id = getattr(actor, "persona_fk_id", None)
        return getattr(actor, "id", None), persona_id

    @transaction.atomic()
    def _crear_sync(
        self,
        pase,
        persona,
        motivo: str,
        actor_usuario_id,
        actor_persona_id,
    ):
        """Crea el acta y su derecho en una sola transacción."""
        return self.cortesia_core.crear(
            edicion_id=pase.edicion_id,
            pase=pase,
            persona=persona,
            motivo=motivo,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
        )

    @staticmethod
    def _es_duplicado(error: IntegrityError) -> bool:
        """Si el `IntegrityError` es la restricción de no duplicar el derecho."""
        texto = str(error).lower()
        return "unique" in texto and "pase_beneficiario" in texto

    # ── La revocación ────────────────────────────────────────────────────────

    async def revocar_cortesia(
        self,
        data: RevocarCortesiaData,
        actor=None,
    ) -> AdminCortesiaRevocadaResult:
        """Revoca la cortesía: el acta y su derecho quedan `REVOCADOS`.

        Es IDEMPOTENTE (`FR-05` §2.3): revocar dos veces NO es un error; la
        segunda devuelve el MISMO estado final con `ya_revocado=True`.

        **NO TOCA HECHOS FINANCIEROS** (`RN-P05`): la cortesía no los tiene y
        la revocación tampoco los crea. `cantidad_consumida` NO baja y los
        consumos ya realizados quedan (`RN-P08`).

        Returns:
            El acta revocada y si ya lo estaba.

        Raises:
            ActorRequeridoError: la revocación requiere una cuenta auditada.
            CortesiaMotivoInvalidoError: el motivo falta o es demasiado
                corto. Sin motivo no hay auditoría (`RN-P05`).
            CortesiaNoEncontradaError: el acta no existe.
        """
        if actor is None or not getattr(actor, "is_authenticated", False):
            raise ActorRequeridoError()

        motivo = self._validar_motivo(data.motivo)
        actor_usuario_id, actor_persona_id = await sync_to_async(self._actor_ids)(actor)

        return await sync_to_async(self._revocar_sync)(
            data.cortesia_id,
            motivo,
            actor_usuario_id,
            actor_persona_id,
        )

    @transaction.atomic()
    def _revocar_sync(
        self,
        cortesia_id,
        motivo: str,
        actor_usuario_id,
        actor_persona_id,
    ) -> AdminCortesiaRevocadaResult:
        """La revocación del acta y de su derecho, en una sola transacción."""
        cortesia = self.cortesia_selector.obtener_cortesia(cortesia_id)
        if cortesia is None:
            raise CortesiaNoEncontradaError()

        cortesia, ya_revocado = self.cortesia_core.revocar(
            cortesia=cortesia,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            motivo=motivo,
        )
        return self._construir_resultado_revocado(cortesia, ya_revocado)

    @staticmethod
    def _construir_resultado_revocado(
        cortesia,
        ya_revocado: bool,
    ) -> AdminCortesiaRevocadaResult:
        """Proyecta el acta revocada al DTO de salida."""
        return AdminCortesiaRevocadaResult(
            id=str(cortesia.id),
            edicion_id=str(cortesia.edicion_id),
            edicion_nombre=cortesia.edicion.nombre,
            pase_id=str(cortesia.pase_id),
            pase_nombre=cortesia.pase.nombre,
            persona_id=str(cortesia.persona_id),
            persona_nombres=cortesia.persona.nombres,
            persona_tipo_documento=cortesia.persona.tipo_documento,
            persona_numero_documento=cortesia.persona.numero_documento,
            estado=cortesia.estado,
            motivo=cortesia.motivo,
            motivo_revocacion=cortesia.motivo_revocacion or "",
            actor_usuario_id=(
                str(cortesia.actor_usuario_id)
                if cortesia.actor_usuario_id
                else None
            ),
            actor_nombres=(
                cortesia.actor_persona.nombres if cortesia.actor_persona else ""
            ),
            concedido_en=cortesia.concedido_en,
            revocado_en=cortesia.revocado_en,
            ya_revocado=ya_revocado,
        )


__all__ = ["CortesiaFlujo"]
