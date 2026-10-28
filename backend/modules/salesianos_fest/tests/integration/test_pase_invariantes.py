"""
Integration tests — the structural invariants of a party-pass purchase (Apply 5).

What this file proves: a pass purchase NEVER touches the sports domain. It
creates no inscription, no sports purchase line, no cupo, no participant, no
team and no pool row, and cancelling it does not touch the sports purchases of
other buyers.

These are the invariants that keep the two catalogues apart.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync
from ninja_jwt.tokens import AccessToken

from modules.pagos.domain.constants import IzipayStatus
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
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

RUTA_BENEFICIARIOS = "/api/pases/compras/{compra_id}/beneficiarios"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _auth_post(client, path, user, data):
    """POST with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _asignar(client, usuario, compra, personas):
    """Assign the given personas to the free slots of a purchase."""
    return _auth_post(
        client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra.id)),
        usuario,
        {"beneficiario_ids": [str(persona.id) for persona in personas]},
    )


def _objetos_deportivos():
    """Snapshot of every sports object a pass purchase must NOT touch."""
    return {
        "inscripcion": Inscripcion.objects.count(),
        "compra_inscripcion": CompraInscripcion.objects.count(),
        "asignacion_cupo": AsignacionCupo.objects.count(),
        "participacion": Participacion.objects.count(),
        "equipo": Equipo.objects.count(),
        "inscripcion_persona": InscripcionPersona.objects.count(),
    }


# ── Tests: the pass journey never touches the sports domain ─────────────────


@pytest.mark.django_db
def test_el_lote_de_pases_no_crea_objetos_deportivos(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a PAID pass purchase
    WHEN:  the buyer assigns a beneficiary
    THEN:  no inscription, sports line, cupo, participant, team nor pool row
           is created
    """
    settings.PASES_FIESTA_ENABLED = True
    antes = _objetos_deportivos()

    response = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    assert response.status_code == 200, response.content
    assert _objetos_deportivos() == antes
    assert Inscripcion.objects.count() == 0
    assert CompraInscripcion.objects.count() == 0
    assert AsignacionCupo.objects.count() == 0
    assert Participacion.objects.count() == 0
    assert Equipo.objects.count() == 0
    assert InscripcionPersona.objects.count() == 0


@pytest.mark.django_db
def test_la_cancelacion_de_pases_no_toca_las_compras_deportivas(
    api_client, usuario_admin_pases, usuario_comprador, compra_pase_pagada,
    persona_con_beneficio_deportivo, persona_beneficiaria_1, settings,
):
    """
    GIVEN: a sports purchase with its cupo and a pass purchase
    WHEN:  the administration cancels the pass purchase
    THEN:  the sports cupo of the other buyer stays ACTIVE and the sports
           objects are untouched
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    cupo_deportivo = AsignacionCupo.objects.filter(estado="ACTIVA").first()
    assert cupo_deportivo is not None
    assert cupo_deportivo.compra_id != compra_pase_pagada.id

    response = _auth_post(
        api_client,
        f"/api/administracion/pases/compras/{compra_pase_pagada.id}/cancelar",
        usuario_admin_pases,
        {"motivo": "Cancelación administrativa"},
    )

    assert response.status_code == 200, response.content
    cupo_deportivo.refresh_from_db()
    assert cupo_deportivo.estado == "ACTIVA"
    assert CompraInscripcion.objects.count() == 1
    assert Inscripcion.objects.count() == 1


@pytest.mark.django_db
def test_la_acreditacion_de_un_pase_no_modifica_los_saldos_deportivos(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_con_beneficio_deportivo, settings,
):
    """
    GIVEN: a sports buyer with its cupo and a pass beneficiary
    WHEN:  the pass is assigned and the access is recomputed
    THEN:  the sports cupo count does not change
    """
    settings.PASES_FIESTA_ENABLED = True
    cupos_antes = AsignacionCupo.objects.count()

    response = _asignar(
        api_client,
        usuario_comprador,
        compra_pase_pagada,
        [persona_con_beneficio_deportivo],
    )

    assert response.status_code == 200, response.content
    assert AsignacionCupo.objects.count() == cupos_antes


@pytest.mark.django_db
def test_la_liquidacion_de_pases_no_asigna_cupos(
    api_client, usuario_comprador, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase
    WHEN:  the settlement runs with the payment evidence
    THEN:  the purchase is paid and ZERO sports cupos are allocated
    """
    settings.PASES_FIESTA_ENABLED = True

    orden_pago = compra_pase_pendiente.orden_pago
    TransaccionPago.objects.create(
        orden_pago_id=orden_pago.id,
        transaction_id="PASINVX001",
        order_number="PASINVN001",
        amount=orden_pago.monto_total,
        currency="PEN",
        status=IzipayStatus.EXITO,
    )

    flujo = ConfirmarPagoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        evidencia_pago=EvidenciaPagoService(),
    )

    async_to_sync(flujo._confirmar_compra)(str(orden_pago.id))

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == "PAGADA"
    assert AsignacionCupo.objects.count() == 0
    assert CompraInscripcion.objects.count() == 0
    assert Decimal("50.00") == compra_pase_pendiente.total


@pytest.mark.django_db
def test_el_pase_no_crea_inscripcion_ni_equipo(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a PAID pass purchase
    WHEN:  the buyer assigns a beneficiary
    THEN:  the sports aggregates (inscription and team) stay empty
    """
    settings.PASES_FIESTA_ENABLED = True

    _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    assert Inscripcion.objects.count() == 0
    assert Equipo.objects.count() == 0
    assert Participacion.objects.count() == 0
