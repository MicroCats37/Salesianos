"""`BeneficiarioFlujo` — la asignación y la revocación de los derechos de entrada.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC,
ABREN `transaction.atomic()`.

Este flujo implementa la parte de `FL-06` que sigue ("Asigna pases a
Personas mediante documento; se respeta límite/duplicidad") y las reglas
congeladas que la acompañan.

**RN-P02 — Sólo se asigna capacidad PAGADA.** Un lote `PENDIENTE` no tiene
capacidad asignable: la activación de derechos (FND-05) es la que la
habilita. La comprobación y la reserva ocurren DENTRO de la misma
transacción.

**RN-P07 — No se asigna más de lo comprado y no se duplica el derecho.** Dos
guardas, dos autoridades:

| Guardia | Autoridad | Cómo |
|---|---|---|
| capacidad | `UPDATE ... WHERE asignados < cantidad` | la BASE DE DATOS decide quién entra |
| duplicado | `UNIQUE (edicion, pase, persona) WHERE estado='ACTIVO'` | la BASE DE DATOS rechaza el segundo derecho |

**RN-P08 — La revocación es permanente y auditada.** El derecho revocado deja
de ser canjeable para validaciones futuras; los consumos ya occurring
permanecen. Es IDEMPOTENTE: revocar dos veces informa del estado final.

**LO QUE NO SE INVENTA (`PD-02` / `GOV-01-OPEN-08`):** la revocación NO
devuelve la unidad al lote y NO permite reasignarla a otra persona. La
política comercial de reasignación sigue ABIERTA; este paquete congela la
INTERFAZ de la revocación, no la política.
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.salesianos_fest.domain.constants import (
    CausaOperativaCompraPase,
    EstadoCompraPase,
)
from modules.salesianos_fest.domain.exceptions import (
    CompraPaseNoEncontradaError,
    CompraPaseNoPagadaError,
    PaseBeneficiarioNoEncontradoError,
    PaseDuplicadoError,
    PersonaNoEncontradaError,
    SinPasesDisponiblesError,
)
from modules.salesianos_fest.domain.ports import (
    IObtensionPersonaService,
    IResolucionPersonaService,
)
from modules.salesianos_fest.domain.results.pase_result import (
    PaseBeneficiarioRevocadoResult,
    PaseBeneficiarioResult,
    PaseBeneficiariosResult,
    PaseCompraDetalleResult,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import (
    AsignarBeneficiarioData,
    RevocarBeneficiarioData,
)
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.beneficiario_core_service import (
    BeneficiarioCoreService,
)
from modules.salesianos_fest.domain.services.core.pase_core_service import (
    PaseCoreService,
)


class BeneficiarioFlujo:
    """La asignación y la revocación de los derechos de entrada."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        pase_core: PaseCoreService,
        beneficiario_core: BeneficiarioCoreService,
        resolucion_persona: IResolucionPersonaService,
        obtencion_persona: IObtensionPersonaService,
    ):
        self.pase_selector = pase_selector
        self.pase_core = pase_core
        self.beneficiario_core = beneficiario_core
        self.resolucion_persona = resolucion_persona
        self.obtencion_persona = obtencion_persona

    # ── Lectura ─────────────────────────────────────────────────────────────

    async def obtener_beneficiarios(self, compra_pase_id) -> PaseBeneficiariosResult:
        """Los derechos otorgados en un lote."""
        compra_pase = await sync_to_async(self._obtener_compra_pase)(compra_pase_id)
        return await sync_to_async(self._construir_beneficiarios)(compra_pase)

    async def obtener_compra(self, compra_pase_id) -> PaseCompraDetalleResult:
        """El detalle del lote con sus derechos.

        Es el shape del listado de beneficiarios MÁS los datos comerciales
        del lote: el frontend consume una sola forma para el detalle y para
        la lista.
        """
        compra_pase = await sync_to_async(self._obtener_compra_pase)(compra_pase_id)
        return await sync_to_async(self._construir_detalle_compra)(compra_pase)

    # ── Asignación ──────────────────────────────────────────────────────────

    async def asignar_beneficiario(
        self,
        compra_pase_id,
        data: AsignarBeneficiarioData,
        actor=None,
    ) -> PaseBeneficiariosResult:
        """Asigna UN pase del lote a una persona.

        La persona puede llegar por IDENTIFICADOR o por DOCUMENTO. La
        resolución y el registro de la identidad son de `usuarios`: este
        módulo NO crea identidades por su cuenta.

        Returns:
            Los derechos del lote tras la asignación.
        """
        compra_pase = await sync_to_async(self._obtener_compra_pase)(compra_pase_id)
        await sync_to_async(self._verificar_pagada)(compra_pase)
        persona = await sync_to_async(self._resolver_beneficiario)(data)

        actor_usuario_id, actor_persona_id = await sync_to_async(
            self._actor_ids
        )(actor)

        try:
            await sync_to_async(self._asignar_sync)(
                compra_pase,
                persona,
                data,
                actor_usuario_id,
                actor_persona_id,
            )
        except IntegrityError as error:
            # La restricción parcial ÚNICA de la base de datos es la
            # autoridad del «no duplicar el derecho». Se traduce FUERA de la
            # transacción, para que la unidad reservada se libere con el
            # rollback.
            if self._es_duplicado(error):
                raise PaseDuplicadoError() from error
            raise

        return await sync_to_async(self._construir_beneficiarios)(compra_pase)

    # ── Revocación ──────────────────────────────────────────────────────────

    async def revocar_beneficiario(
        self,
        compra_pase_id,
        persona_id,
        data: RevocarBeneficiarioData,
        actor=None,
    ) -> PaseBeneficiarioRevocadoResult:
        """Revoca el derecho de una persona en el lote.

        Es IDEMPOTENTE (`FR-05` §2.3): la segunda revocación no es un error,
        informa del estado final con `ya_revocado=True`.

        Returns:
            El derecho revocado y su estado final.
        """
        compra_pase = await sync_to_async(self._obtener_compra_pase)(compra_pase_id)
        beneficiario = await sync_to_async(self._obtener_beneficiario)(
            compra_pase,
            persona_id,
        )
        actor_usuario_id, actor_persona_id = await sync_to_async(
            self._actor_ids
        )(actor)

        derecho, ya_revocado = await sync_to_async(self._revocar_sync)(
            beneficiario,
            data,
            actor_usuario_id,
            actor_persona_id,
        )
        return PaseBeneficiarioRevocadoResult(
            compra_pase_id=str(compra_pase.id),
            derecho_id=str(derecho.id),
            persona_id=str(derecho.persona_id),
            estado=derecho.estado,
            revocado_en=derecho.revocado_en,
            ya_revocado=ya_revocado,
            motivo=derecho.motivo_revocacion,
        )

    # ── Internos (sync) ─────────────────────────────────────────────────────

    def _obtener_compra_pase(self, compra_pase_id):
        """El lote de pases, o `COMPRA_PASE_NO_ENCONTRADA`."""
        compra_pase = self.pase_selector.obtener_compra_pase(compra_pase_id)
        if compra_pase is None:
            raise CompraPaseNoEncontradaError()
        return compra_pase

    @staticmethod
    def _verificar_pagada(compra_pase) -> None:
        """El lote debe estar `PAGADA`: una compra pendiente NO habilita.

        `RN-P02`: la capacidad asignable es la que la ACTIVACIÓN de derechos
        habilitó, y la activación ocurre cuando el pago está confirmado.
        """
        if compra_pase.estado != EstadoCompraPase.PAGADA:
            raise CompraPaseNoPagadaError()

    def _resolver_beneficiario(self, data: AsignarBeneficiarioData):
        """La persona que recibe el pase.

        Por IDENTIFICADOR: se busca en el padrón. Por DOCUMENTO: se resuelve
        y, si no existe, se REGISTRA como identidad civil — sin cuenta.
        """
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
    def _asignar_sync(
        self,
        compra_pase,
        persona,
        data: AsignarBeneficiarioData,
        actor_usuario_id,
        actor_persona_id,
    ):
        """Reserva la unidad y otorga el derecho, en una sola transacción.

        La reserva es un `UPDATE` CONDICIONAL: la condición viaja DENTRO de
        la sentencia, así que dos asignaciones simultáneas no pueden
        sobre-asignar el lote. La base de datos decide quién entra.
        """
        if not self.pase_core.reservar_pase(compra_pase.id):
            raise SinPasesDisponiblesError()

        return self.beneficiario_core.asignar(
            compra_pase=compra_pase,
            pase=compra_pase.pase,
            persona=persona,
            cantidad=1,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            motivo=data.motivo,
        )

    def _obtener_beneficiario(self, compra_pase, persona_id):
        """El derecho de esa persona en ese lote, o `None`."""
        beneficiario = self.pase_selector.obtener_beneficiario(
            compra_pase.id,
            persona_id,
        )
        if beneficiario is None:
            raise PaseBeneficiarioNoEncontradoError()
        return beneficiario

    @transaction.atomic()
    def _revocar_sync(
        self,
        beneficiario,
        data: RevocarBeneficiarioData,
        actor_usuario_id,
        actor_persona_id,
    ):
        """Revoca el derecho y devuelve `(derecho, ya_revocado)`."""
        return self.beneficiario_core.revocar(
            beneficiario=beneficiario,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            motivo=data.motivo,
        )

    def _construir_detalle_compra(self, compra_pase) -> PaseCompraDetalleResult:
        """Proyecta el detalle completo del lote."""
        base = self._construir_beneficiarios(compra_pase)
        return PaseCompraDetalleResult(
            compra_pase_id=base.compra_pase_id,
            compra_id=str(compra_pase.compra_id) if compra_pase.compra_id else "",
            orden_pago_id=(
                str(compra_pase.compra.orden_pago_id)
                if compra_pase.compra_id and compra_pase.compra.orden_pago_id
                else ""
            ),
            estado=base.estado,
            pase_id=str(compra_pase.pase_id),
            pase_nombre=compra_pase.pase.nombre,
            edicion_id=str(compra_pase.edicion_id),
            edicion_nombre=compra_pase.edicion.nombre,
            cantidad=base.cantidad,
            asignados=base.asignados,
            disponibles=base.disponibles,
            precio_unitario=compra_pase.precio_unitario,
            total=compra_pase.total,
            moneda=compra_pase.moneda,
            causa_operativa=(
                CausaOperativaCompraPase.COMPRA_PASE_REUTILIZADA
                if compra_pase.estado == EstadoCompraPase.PENDIENTE
                else CausaOperativaCompraPase.COMPRA_PASE_CREADA
            ),
            beneficiarios=base.beneficiarios,
        )

    def _construir_beneficiarios(self, compra_pase) -> PaseBeneficiariosResult:
        """Proyecta los derechos del lote."""
        asignados = self.pase_selector.contar_beneficiarios(compra_pase.id)
        disponibles = max(compra_pase.cantidad - asignados, 0)
        return PaseBeneficiariosResult(
            compra_pase_id=str(compra_pase.id),
            estado=compra_pase.estado,
            cantidad=compra_pase.cantidad,
            asignados=asignados,
            disponibles=disponibles,
            beneficiarios=[
                BeneficiarioFlujo._proyectar_beneficiario(beneficiario)
                for beneficiario in self.pase_selector.listar_beneficiarios(
                    compra_pase.id
                )
            ],
        )

    @staticmethod
    def _proyectar_beneficiario(beneficiario) -> PaseBeneficiarioResult:
        """Proyecta un derecho de entrada."""
        persona = beneficiario.persona
        return PaseBeneficiarioResult(
            id=str(beneficiario.id),
            pase_id=str(beneficiario.pase_id),
            pase_nombre=beneficiario.pase.nombre,
            edicion_id=str(beneficiario.edicion_id),
            persona_id=str(beneficiario.persona_id),
            persona_nombres=persona.nombres,
            persona_apellidos=persona.apellidos,
            persona_tipo_documento=persona.tipo_documento,
            persona_numero_documento=persona.numero_documento,
            origen=beneficiario.origen,
            estado=beneficiario.estado,
            cantidad=beneficiario.cantidad,
            cantidad_consumida=beneficiario.cantidad_consumida,
            cantidad_disponible=max(
                beneficiario.cantidad - beneficiario.cantidad_consumida,
                0,
            ),
            asignado_en=beneficiario.asignado_en,
            motivo=beneficiario.motivo,
            revocado_en=beneficiario.revocado_en,
            motivo_revocacion=beneficiario.motivo_revocacion,
        )

    @staticmethod
    def _es_duplicado(error: IntegrityError) -> bool:
        """Si el `IntegrityError` es la restricción de no duplicar el derecho.

        La traducción es INTENCIONAL y conservadora: mira el nombre de la
        restricción, no el texto crudo de la excepción (que puede variar
        entre motores). Un error de integridad que NO es de duplicado no se
        disfraza de duplicado.
        """
        texto = str(error).lower()
        return "unique" in texto and "pase_beneficiario" in texto


__all__ = ["BeneficiarioFlujo"]
