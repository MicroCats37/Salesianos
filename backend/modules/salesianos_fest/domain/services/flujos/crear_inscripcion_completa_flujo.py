"""CrearInscripcionCompletaFlujo — async flow for atomic inscription + compra + equipos creation.

Atomic flow with transaction.atomic — creates:
1. Inscripcion (BORRADOR) with responsable from authenticated user
2. commerce.Compra (generic, PENDIENTE)
3. OrdenPago (PENDIENTE) with descripcion and referencia_externa snapshots
4. CompraInscripcion (FEST-specific, linked to commerce.Compra)
5. All Equipos (one per discipline slot)

Does NOT create participant roster — that happens later via agregar_persona.

Price snapshot is frozen at Compra creation time (R11).
Quotas are NOT consumed at creation — only after payment confirmation.
Date limits are enforced.

Price revalidation:
- If the client sent `precio_unitario_cotizado`, it MUST match the current
  catalog price within 0.01 tolerance; otherwise we raise PrecioCambioError.
- When the quoted price matches, we USE the quoted price (snapshot of what
  the user saw) instead of the catalog price — this is the user-trust contract.
- If the client did not send a quotation, we fall back to the catalog price.
- `cotizacion_version` is metadata only (logged for traceability, not validated).
"""
import logging
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from django.db import IntegrityError

from modules.salesianos_fest.domain.constants import TipoCompraChoices
from modules.salesianos_fest.domain.exceptions import (
    CantidadInsuficienteError,
    PaqueteNotFoundError,
    FechaLimiteExcedidaError,
    PrecioCambioError,
    InscripcionUniqueConstraintError,
)
from modules.salesianos_fest.domain.models import (
    Inscripcion,
    CompraInscripcion,
    Equipo,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionCompletaCreateData,
)
from modules.salesianos_fest.domain.results.inscripcion_results import (
    InscripcionCompletaResult,
    EquipoResult,
)
from modules.salesianos_fest.domain.services.core.equipo_service import EquipoCoreService
from modules.salesianos_fest.domain.services.core.inscripcion_service import InscripcionCoreService
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices

logger = logging.getLogger(__name__)


def _obtener_precio_vigente(paquete_id: str) -> tuple[Decimal, int]:
    """Get vigente precio_unitario for a paquete and cantidad_disciplinas."""
    from django.db.models import Q
    from django.utils import timezone
    from modules.salesianos_fest.domain.models import PaquetePrecio

    hoy = timezone.now().date()
    precio = (
        PaquetePrecio.objects
        .filter(
            paquete_id=paquete_id,
            activo=True,
            vigente_desde__lte=hoy,
        )
        .filter(
            Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
        )
        .order_by("-vigente_desde")
        .first()
    )
    if precio is None:
        from modules.salesianos_fest.domain.exceptions import PrecioNoEncontradoError
        raise PrecioNoEncontradoError()
    return precio.precio_unitario, precio.paquete.cantidad_disciplinas


class CrearInscripcionCompletaFlujo:
    """
    Atomic flow for creating inscription with initial purchase and teams.

    Creates atomically:
    - Inscripcion (BORRADOR) with server-derived responsable
    - commerce.Compra (generic, PENDIENTE)
    - OrdenPago (PENDIENTE) with descripcion and referencia_externa snapshots
    - CompraInscripcion (FEST composition link)
    - All Equipos specified in the payload
    """

    @inject
    def __init__(
        self,
        inscripcion_core: InscripcionCoreService,
        equipo_core: EquipoCoreService,
        izipay_core: IzipayCoreService,
    ):
        self._inscripcion_core = inscripcion_core
        self._equipo_core = equipo_core
        self._izipay_core = izipay_core

    @sync_to_async
    def _crear_atomico(
        self, data: InscripcionCompletaCreateData, responsable_id: str
    ) -> InscripcionCompletaResult:
        """
        Create inscription, compra, equipos atomically.

        Raises:
            PaqueteNotFoundError: if paquete not found
            CantidadInsuficienteError: if cantidad < minimo_compra_inicial
            FechaLimiteExcedidaError: if evento date limit exceeded
        """
        with transaction.atomic():
            # 1. Load paquete and validate minimo_compra_inicial
            from modules.salesianos_fest.domain.models import Paquete

            try:
                paquete = Paquete.objects.select_related("evento").get(id=data.paquete_id)
            except Paquete.DoesNotExist:
                raise PaqueteNotFoundError()

            if data.cantidad < paquete.minimo_compra_inicial:
                raise CantidadInsuficienteError(
                    minimo=paquete.minimo_compra_inicial,
                    received=data.cantidad,
                )

            # 2. Check fecha_limite for evento
            if not paquete.evento.puede_modificar():
                raise FechaLimiteExcedidaError()

            # 3. Get vigentes price from catalog
            precio_unitario_catalogo, _ = _obtener_precio_vigente(paquete.id)
            precio_float_catalogo = float(precio_unitario_catalogo)

            # 3b. Price resolution — honor the client's quotation when present.
            #
            # The user-trust contract: the frontend displays a quotation, the
            # user confirms within the validity period, and the backend MUST
            # honor that price. We revalidate against the catalog (security)
            # but USE the quoted price (snapshot of what the user saw) when it
            # matches. This avoids "el usuario vio S/40 pero le cobraron S/50".
            if data.precio_unitario_cotizado is not None:
                if abs(data.precio_unitario_cotizado - precio_float_catalogo) > 0.01:
                    raise PrecioCambioError(
                        precio_cotizado=data.precio_unitario_cotizado,
                        precio_actual=precio_float_catalogo,
                        cantidad=data.cantidad,
                    )
                # Quoted price is fresh — USE it as the canonical price.
                precio_unitario = Decimal(str(data.precio_unitario_cotizado))
            else:
                # No quotation sent — fall back to the catalog price.
                precio_unitario = precio_unitario_catalogo

            # Metadata traceability: log the quotation version when present.
            if data.cotizacion_version is not None:
                logger.info(
                    "Inscripcion atomica creada con cotizacion version=%s "
                    "(paquete=%s, cantidad=%s, precio=%s)",
                    data.cotizacion_version,
                    data.paquete_id,
                    data.cantidad,
                    precio_unitario,
                )

            # 4. Calculate total con el precio EFFECTIVO (cotizado o catalogo)
            total = Decimal(str(data.cantidad)) * precio_unitario

            # 5. Create Inscripcion
            try:
                inscripcion = Inscripcion.objects.create(
                    evento_id=data.evento_id,
                    responsable_id=responsable_id,
                    paquete_id=data.paquete_id,
                    promocion_id=data.promocion_id,
                    fusion_promocion_id=data.fusion_promocion_id,
                    delegado_id=data.delegado_id,
                    estado=data.estado,
                    observacion=data.observacion,
                )
            except IntegrityError as exc:
                # El modelo Inscripcion tiene UniqueConstraint en
                # (evento, responsable, paquete). Si el usuario intenta
                # crear una inscripcion duplicada, la BD la rechaza.
                # Traducimos esto a un error de dominio explicito en
                # lugar de un 500/IntegrityError raw.
                msg = str(exc).lower()
                if "unique_inscripcion_evento_responsable_paquete" in msg or (
                    "unique constraint failed" in msg
                    and "inscripciones" in msg
                ):
                    raise InscripcionUniqueConstraintError() from exc
                raise

            # 6. Create commerce.Compra (generic, no orden_pago yet)
            descripcion = f"Compra Inicial - {paquete.nombre}"
            referencia_externa = f"FEST-{str(inscripcion.id)[:8]}"

            commerce_compra = Compra.objects.create(
                responsable=inscripcion.responsable,
                descripcion=descripcion,
                referencia_externa=referencia_externa,
                total=total,
                estado=EstadoCompraChoices.PENDIENTE,
            )

            # 7. Create OrdenPago with descripcion and referencia_externa
            numero_orden = self._izipay_core.generar_numero_orden()
            orden_pago = self._izipay_core.crear_orden_pago(
                numero=numero_orden,
                monto_total=total,
                moneda="PEN",
            )
            orden_pago.descripcion = descripcion
            orden_pago.referencia_externa = referencia_externa
            orden_pago.save(update_fields=["descripcion", "referencia_externa", "updated_at"])

            # 8. Assign OrdenPago to commerce.Compra
            commerce_compra.orden_pago = orden_pago
            commerce_compra.save(update_fields=["orden_pago", "updated_at"])

            # 9. Create CompraInscripcion (FEST composition link)
            compra_inscripcion = CompraInscripcion.objects.create(
                compra=commerce_compra,
                inscripcion=inscripcion,
                tipo=TipoCompraChoices.INICIAL,
                cantidad=data.cantidad,
                precio_unitario=precio_unitario,
                total=total,
            )

            # 10. Create Equipos
            equipos_result = []
            for eq_data in data.equipos:
                eq = Equipo.objects.create(
                    inscripcion=inscripcion,
                    disciplina_id=eq_data.disciplina_id,
                    categoria_id=eq_data.categoria_id,
                    nombre=eq_data.nombre,
                    estado=eq_data.estado,
                )
                equipos_result.append(
                    EquipoResult(
                        id=str(eq.id),
                        inscripcion_id=str(inscripcion.id),
                        disciplina_id=str(eq.disciplina_id),
                        disciplina_nombre=eq.disciplina.nombre,
                        disciplina_sigla=eq.disciplina.sigla,
                        categoria_id=str(eq.categoria_id) if eq.categoria_id else None,
                        categoria_nombre=eq.categoria.nombre if eq.categoria_id else None,
                        nombre=eq.nombre,
                        estado=eq.estado,
                        created_at=eq.created_at,
                        participaciones=[],
                    )
                )

            return InscripcionCompletaResult(
                inscripcion_id=str(inscripcion.id),
                inscripcion_estado=inscripcion.estado,
                compra_id=str(commerce_compra.id),
                compra_inscripcion_id=str(compra_inscripcion.id),
                orden_pago_id=str(orden_pago.id),
                compra_estado=EstadoCompraChoices.PENDIENTE,
                cantidad=data.cantidad,
                precio_unitario=float(precio_unitario),
                total=float(total),
                equipos=equipos_result,
            )

    async def ejecutar(
        self, data: InscripcionCompletaCreateData, responsable_id: str
    ) -> InscripcionCompletaResult:
        """Execute the atomic inscription + compra + equipos flow."""
        return await self._crear_atomico(data, responsable_id)
