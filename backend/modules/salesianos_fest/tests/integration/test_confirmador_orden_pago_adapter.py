"""
Focused integration tests for the commercial settlement adapter.

`ConfirmadorOrdenPagoAdapter` is the `salesianos_fest` implementation of the
`IConfirmadorOrdenPagoService` port declared in `modules.pagos`. It is the
backend side of the automatic commercial settlement: once an order is paid, the
purchase is settled and its cup rights are allocated — without any browser
request.

Covers:
- A paid order settles its purchase and allocates the rights.
- The settlement is idempotent — a replay creates no duplicate rights.
- An order with no purchase linked reports "nothing to settle" instead of
  failing.
"""
import pytest
from datetime import date
from decimal import Decimal

from asgiref.sync import async_to_sync

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaquetePrecio,
    Promocion,
)
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EtapaChoices,
    ModoDisciplinasChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
    ConfirmarPagoFlujo,
)
from modules.salesianos_fest.infrastructure.services import ConfirmadorOrdenPagoAdapter
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def evento_fest(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Adapter 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def promocion_fest(db):
    return Promocion.objects.create(anio=2012, nombre="Junior Adapter", activa=True)


@pytest.fixture
def paquete_fest(db, evento_fest):
    paquete = Paquete.objects.create(
        evento=evento_fest,
        nombre="Reencuentro + Fiesta Adapter",
        descripcion="Pack de prueba para el adaptador de liquidación",
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
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11111111",
        genero="F",
    )


@pytest.fixture
def persona_fest_2(db):
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Reyes",
        tipo_documento="DNI",
        numero_documento="22222222",
        genero="M",
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
def orden_pago_pagada(db):
    orden = OrdenPago.objects.create(
        numero="OP-ADAPTER-001",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PENDIENTE,
    )
    TransaccionPago.objects.create(
        orden_pago=orden,
        transaction_id="ADAPTERTX001",
        order_number="ADAPTERTN001",
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
        descripcion="Compra para liquidar",
        referencia_externa="ADAPTER-REF-1",
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
def participante_preregistrado(db, inscripcion_fest, persona_fest):
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_fest,
        persona=persona_fest,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def adaptador(db):
    """The port adapter wired to the real settlement flow."""
    return ConfirmadorOrdenPagoAdapter(
        confirmar_pago_flujo=ConfirmarPagoFlujo(
            asignacion_core=AsignacionCoreService(),
            acreditacion_core=AcreditacionCoreService(),
            evidencia_pago=EvidenciaPagoService(),
        )
    )


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_adapter_liquida_compra_y_asigna_cupos(
    db, adaptador, compra_pendiente, inscripcion_fest, participante_preregistrado
):
    """
    GIVEN: A paid order with a pending purchase and a preregistered participant
    WHEN:  the settlement is driven for that order
    THEN:  the purchase is paid and the right is allocated
    """
    result = async_to_sync(adaptador.confirmar_orden_pagada)(
        str(compra_pendiente.orden_pago_id)
    )

    assert result.settled is True
    assert result.already_settled is False

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA

    asignaciones = AsignacionCupo.objects.filter(
        inscripcion=inscripcion_fest,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    assert asignaciones.count() == 1
    assert asignaciones.first().inscripcion_persona_id == participante_preregistrado.id


@pytest.mark.django_db
def test_adapter_es_idempotente(
    db, adaptador, compra_pendiente, inscripcion_fest, participante_preregistrado
):
    """
    GIVEN: A purchase already settled by a previous call
    WHEN:  the settlement is driven again for the same order
    THEN:  it reports it was already settled and creates no duplicate rights
    """
    async_to_sync(adaptador.confirmar_orden_pagada)(str(compra_pendiente.orden_pago_id))

    segundo = async_to_sync(adaptador.confirmar_orden_pagada)(
        str(compra_pendiente.orden_pago_id)
    )

    assert segundo.settled is True
    assert segundo.already_settled is True

    asignaciones = AsignacionCupo.objects.filter(
        inscripcion=inscripcion_fest,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    assert asignaciones.count() == 1


@pytest.mark.django_db
def test_adapter_sin_compra_devuelve_no_liquidado(db, adaptador, orden_pago_pagada):
    """
    GIVEN: A paid order with no purchase linked to it
    WHEN:  the settlement is driven for that order
    THEN:  it reports that there was nothing to settle instead of failing
    """
    result = async_to_sync(adaptador.confirmar_orden_pagada)(
        str(orden_pago_pagada.id)
    )

    assert result.settled is False
    assert result.already_settled is False
