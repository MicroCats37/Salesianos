"""
Focused integration tests for the automatic commercial settlement.

The backend owns the commercial confirmation: once a payment is verified, the
backend settles the linked purchase and allocates its cup rights. The browser
never sends a commercial-confirmation request.

Covers:
- The `salesianos_fest` adapter (the port implementation) settles the purchase
  and allocates the rights, idempotently.
- An order with no purchase linked reports "nothing to settle" instead of
  failing.
- The full HTTP path: one browser relay to `POST /api/pagos/izipay/confirmar`
  produces `OrdenPago=PAGADA`, `Compra=PAGADA` and the cup allocation.
"""
import json
import pytest
from datetime import date
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

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
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus, SettlementStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def evento_fest(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Liquidacion 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def promocion_fest(db):
    return Promocion.objects.create(anio=2012, nombre="Junior Liquidacion", activa=True)


@pytest.fixture
def paquete_fest(db, evento_fest):
    paquete = Paquete.objects.create(
        evento=evento_fest,
        nombre="Reencuentro + Fiesta Liquidacion",
        descripcion="Pack de prueba para la liquidacion automatica",
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
def usuario_responsable(db, persona_fest):
    """The responsible of the inscripcion — the authenticated browser."""
    User = get_user_model()
    return User.objects.create_user(
        username="usuario_liquidacion",
        email="liquidacion@example.com",
        password="testpass123",
        persona_fk=persona_fest,
    )


@pytest.fixture
def orden_pago_pagada(db):
    """An order whose payment is already recorded, with a successful transaction."""
    orden = OrdenPago.objects.create(
        numero="OP-LIQ-001",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden,
        transaction_id="LIQTX001",
        order_number="LIQTN001",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    return orden


@pytest.fixture
def orden_pago_pendiente(db):
    """An order still waiting for the browser relay, with a pending transaction."""
    orden = OrdenPago.objects.create(
        numero="OP-LIQ-002",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PENDIENTE,
    )
    TransaccionPago.objects.create(
        orden_pago=orden,
        transaction_id="LIQTX002",
        order_number="LIQTN002",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.PENDIENTE,
    )
    return orden


def _crear_compra(inscripcion, orden_pago, referencia: str) -> Compra:
    """Create a PENDIENTE purchase linked to an order and an inscripcion."""
    compra = Compra.objects.create(
        responsable=inscripcion.responsable,
        descripcion=f"Compra {referencia}",
        referencia_externa=referencia,
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        total=Decimal("50.00"),
    )
    return compra


@pytest.fixture
def compra_pendiente(db, inscripcion_fest, orden_pago_pagada):
    """A PENDIENTE purchase whose order is already paid — the settlement gap."""
    return _crear_compra(inscripcion_fest, orden_pago_pagada, "LIQ-REF-1")


@pytest.fixture
def compra_pendiente_http(db, inscripcion_fest, orden_pago_pendiente):
    """A PENDIENTE purchase whose order is still waiting for the relay."""
    return _crear_compra(inscripcion_fest, orden_pago_pendiente, "LIQ-REF-2")


@pytest.fixture
def adaptador(db):
    """The port adapter wired to the real settlement flow."""
    return ConfirmadorOrdenPagoAdapter(
        confirmar_pago_flujo=ConfirmarPagoFlujo(
            asignacion_core=AsignacionCoreService(),
            acreditacion_core=AcreditacionCoreService(),
        )
    )


# ── Adapter: la liquidacion real ─────────────────────────────────────────────

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


# ── HTTP: una sola peticion del navegador ────────────────────────────────────

@pytest.mark.django_db
def test_confirmar_pago_por_http_liquida_compra_sin_segunda_peticion(
    db,
    api_client,
    usuario_responsable,
    compra_pendiente_http,
    inscripcion_fest,
    participante_preregistrado,
    orden_pago_pendiente,
):
    """
    GIVEN: A pending purchase, a pending order and a preregistered participant
    WHEN:  the browser relays the provider confirmation ONCE
    THEN:  the order is paid, the purchase is paid and the right is allocated
    AND    no second commercial-confirmation request was needed
    """
    token = AccessToken.for_user(usuario_responsable)
    response = api_client.post(
        "/api/pagos/izipay/confirmar",
        data=json.dumps(
            {
                "kr_answer": {
                    "code": "00",
                    "message": "Operación exitosa",
                    "transactionId": "LIQTX002",
                    "response": {"payMethod": "CARD"},
                }
            }
        ),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    body = response.json()

    assert body["success"] is True
    assert body["data"]["success"] is True
    assert body["data"]["settlement_status"] == SettlementStatus.SETTLED
    assert body["message"] == "Pago confirmado correctamente."

    orden_pago_pendiente.refresh_from_db()
    assert orden_pago_pendiente.estado == OrdenPagoStatus.PAGADA

    compra_pendiente_http.refresh_from_db()
    assert compra_pendiente_http.estado == EstadoCompraChoices.PAGADA

    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion_fest,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )
