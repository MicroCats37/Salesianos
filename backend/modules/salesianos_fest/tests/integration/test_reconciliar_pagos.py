"""
Focused integration tests for the payment reconciliation.

The reconciliation repairs the paid/pending gap: an order that is PAGADA
while its linked purchase is still PENDIENTE. It must select the successful
attempt as the payment evidence, tolerate the older pending attempts, settle
the purchase idempotently and never duplicate cup rights.
"""
import pytest
from datetime import date
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.core.management import call_command

from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EstadoReconciliacionPagoChoices,
    EtapaChoices,
    ModoDisciplinasChoices,
    MotivoReconciliacionPagoChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaquetePrecio,
    Promocion,
)
from modules.salesianos_fest.domain.selectors import CompraSelector
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
    ConfirmarPagoFlujo,
)
from modules.salesianos_fest.domain.services.flujos.reconciliar_pagos_flujo import (
    ReconciliarPagosFlujo,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def evento_fest(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Reconciliación 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def promocion_fest(db):
    return Promocion.objects.create(anio=2012, nombre="Junior Reconciliación", activa=True)


@pytest.fixture
def paquete_fest(db, evento_fest):
    paquete = Paquete.objects.create(
        evento=evento_fest,
        nombre="Reencuentro + Fiesta Reconciliación",
        descripcion="Paquete de prueba para la reconciliación de pagos",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona_fest(db):
    from modules.usuarios.domain.models.persona import Persona

    return Persona.objects.create(
        nombres="Ana",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11111111",
        genero="F",
    )


@pytest.fixture
def inscripcion_fest(db, evento_fest, persona_fest, paquete_fest, promocion_fest):
    return Inscripcion.objects.create(
        evento=evento_fest,
        responsable=persona_fest,
        paquete=paquete_fest,
        promocion=promocion_fest,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def participante_preregistrado(db, inscripcion_fest, persona_fest):
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_fest,
        persona=persona_fest,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def orden_pago_pagada(db):
    """A paid order with its successful attempt."""
    orden = OrdenPago.objects.create(
        numero="OP-RECON-001",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden,
        transaction_id="RECONTX001",
        order_number="RECONTN001",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    return orden


@pytest.fixture
def compra_pendiente(db, inscripcion_fest, orden_pago_pagada):
    """A PENDIENTE purchase linked to the paid order."""
    compra = Compra.objects.create(
        responsable=inscripcion_fest.responsable,
        descripcion="Compra para reconciliar",
        referencia_externa="RECON-REF-1",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago_pagada
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_fest,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        total=Decimal("50.00"),
    )
    return compra


@pytest.fixture
def flujo_reconciliacion(db):
    """The reconciliation flow wired to the real settlement."""
    return ReconciliarPagosFlujo(
        izipay_core=IzipayCoreService(),
        compra_selector=CompraSelector(),
        confirmar_pago_flujo=ConfirmarPagoFlujo(
            asignacion_core=AsignacionCoreService(),
            acreditacion_core=AcreditacionCoreService(),
            evidencia_pago=EvidenciaPagoService(),
        ),
    )


def _asignaciones(inscripcion_fest):
    return AsignacionCupo.objects.filter(
        inscripcion=inscripcion_fest,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )


def _reconciliar(flujo_reconciliacion, **kwargs):
    """Run the reconciliation flow from a sync test."""
    return async_to_sync(flujo_reconciliacion._reconciliar)(**kwargs)


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_reconciliacion_liquida_la_compra_pendiente(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada, inscripcion_fest,
    participante_preregistrado,
):
    """
    GIVEN: A paid order whose linked purchase is still pending
    WHEN:  the reconciliation runs
    THEN:  the purchase is settled and its rights are allocated
    """
    resultado = _reconciliar(flujo_reconciliacion)

    assert resultado.revisadas == 1
    assert resultado.reconciliadas == 1
    assert resultado.errores == 0
    assert resultado.detalle[0].estado == EstadoReconciliacionPagoChoices.RECONCILIADA
    assert resultado.detalle[0].transaction_id == "RECONTX001"

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _asignaciones(inscripcion_fest).count() == 1


@pytest.mark.django_db
def test_reconciliacion_es_idempotente(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada, inscripcion_fest,
    participante_preregistrado,
):
    """
    GIVEN: A reconciliation that already settled the purchase
    WHEN:  the reconciliation runs again
    THEN:  nothing changes and no duplicate rights are created
    """
    _reconciliar(flujo_reconciliacion)
    segunda = _reconciliar(flujo_reconciliacion)

    assert segunda.revisadas == 0
    assert segunda.reconciliadas == 0

    assert _asignaciones(inscripcion_fest).count() == 1


@pytest.mark.django_db
def test_reconciliacion_sin_pago_verificado_no_liquida(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada,
):
    """
    GIVEN: A paid order without a successful attempt
    WHEN:  the reconciliation runs
    THEN:  the order is omitted and the purchase stays pending
    """
    TransaccionPago.objects.filter(orden_pago=orden_pago_pagada).delete()

    resultado = _reconciliar(flujo_reconciliacion)

    assert resultado.omitidas == 1
    assert resultado.reconciliadas == 0
    assert (
        resultado.detalle[0].motivo
        == MotivoReconciliacionPagoChoices.SIN_PAGO_VERIFICADO
    )

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_reconciliacion_con_monto_distinto_no_liquida(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada,
):
    """
    GIVEN: A paid order whose successful attempt carries another amount
    WHEN:  the reconciliation runs
    THEN:  the order is omitted and the purchase stays pending
    """
    TransaccionPago.objects.filter(transaction_id="RECONTX001").update(
        amount=Decimal("10.00")
    )

    resultado = _reconciliar(flujo_reconciliacion)

    assert resultado.omitidas == 1
    assert (
        resultado.detalle[0].motivo
        == MotivoReconciliacionPagoChoices.PAGO_NO_CORRELACIONADO
    )

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_reconciliacion_tolera_intentos_pendientes_antiguos(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada, inscripcion_fest,
    participante_preregistrado,
):
    """
    GIVEN: A paid order with several older pending attempts
    WHEN:  the reconciliation runs
    THEN:  the successful attempt is the one that settles the purchase
    AND    the stale pending attempts are expired
    """
    for indice in range(3):
        TransaccionPago.objects.create(
            orden_pago=orden_pago_pagada,
            transaction_id=f"RECONPEND{indice}",
            order_number=f"RECONPN{indice}",
            amount=Decimal("50.00"),
            currency="PEN",
            status=IzipayStatus.PENDIENTE,
        )

    resultado = _reconciliar(flujo_reconciliacion)

    assert resultado.reconciliadas == 1
    assert resultado.detalle[0].transaction_id == "RECONTX001"
    assert resultado.detalle[0].intentos_expirados == 3

    assert TransaccionPago.objects.filter(
        orden_pago=orden_pago_pagada, status=IzipayStatus.PENDIENTE
    ).count() == 0
    assert _asignaciones(inscripcion_fest).count() == 1


@pytest.mark.django_db
def test_reconciliacion_en_simulacion_no_modifica_nada(
    db, flujo_reconciliacion, compra_pendiente, orden_pago_pagada,
):
    """
    GIVEN: A dry run of the reconciliation
    WHEN:  it runs
    THEN:  it reports the order and changes nothing
    """
    resultado = _reconciliar(flujo_reconciliacion, dry_run=True)

    assert resultado.dry_run is True
    assert resultado.revisadas == 1
    assert resultado.reconciliadas == 0
    assert resultado.detalle[0].motivo == MotivoReconciliacionPagoChoices.SIMULACION

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_comando_reconciliar_pagos_liquida_la_compra(
    db, compra_pendiente, orden_pago_pagada, inscripcion_fest, participante_preregistrado,
):
    """
    GIVEN: The reviewed management command
    WHEN:  it runs against a paid order with a pending purchase
    THEN:  the purchase is settled and the rights are allocated
    """
    call_command("reconciliar_pagos", stdout=None, stderr=None)

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _asignaciones(inscripcion_fest).count() == 1


@pytest.mark.django_db
def test_comando_reconciliar_pagos_es_idempotente(
    db, compra_pendiente, orden_pago_pagada, inscripcion_fest, participante_preregistrado,
):
    """
    GIVEN: A reconciliation already executed by the command
    WHEN:  the command runs again
    THEN:  nothing changes and no duplicate rights are created
    """
    call_command("reconciliar_pagos", stdout=None, stderr=None)
    call_command("reconciliar_pagos", stdout=None, stderr=None)

    assert _asignaciones(inscripcion_fest).count() == 1


@pytest.mark.django_db
def test_comando_reconciliar_pagos_dry_run_no_modifica_nada(
    db, compra_pendiente, orden_pago_pagada,
):
    """
    GIVEN: The command executed in dry-run mode
    WHEN:  it runs
    THEN:  the purchase stays pending
    """
    call_command("reconciliar_pagos", "--dry-run", stdout=None, stderr=None)

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE
