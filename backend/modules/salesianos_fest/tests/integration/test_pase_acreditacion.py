"""
Integration tests — the accreditation derived from a party pass (Apply 5).

What this file proves:

1. an ACTIVE pass entitlement of a PAID purchase grants fiesta access;
2. a beneficiary WITHOUT sports registration nor account gets the event
   accreditation too;
3. a pass of a purchase that is NOT paid grants nothing, and neither does a
   REVOKED entitlement;
4. the ADMIN OVERRIDES keep their precedence: BLOQUEADA always denies and
   AUTORIZADA always allows, even with an active pass;
5. the pass is ONLY a source of FIESTA access: `acceso_box` is never granted
   nor modified;
6. the pass and the sports benefit are INDEPENDENT sources: revoking one
   keeps the access granted by the other;
7. the gate (QR scan) stops enabling the access once the effective access is
   gone.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json

import pytest
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
)
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    PaseBeneficiario,
)

RUTA_BENEFICIARIOS = "/api/pases/compras/{compra_id}/beneficiarios"
RUTA_ACCESO = "/api/acceso/registrar"


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
    """Assign the given persons to the free slots of a purchase."""
    return _auth_post(
        client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra.id)),
        usuario,
        {"beneficiario_ids": [str(persona.id) for persona in personas]},
    )


def _revocar(client, usuario, compra, persona, motivo="Prueba"):
    """Revoke the pass of a person (permanent, audited)."""
    token = AccessToken.for_user(usuario)
    return client.delete(
        f"{RUTA_BENEFICIARIOS.format(compra_id=str(compra.id))}/{persona.id}",
        data=json.dumps({"motivo": motivo}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _acreditacion(persona, evento):
    """The accreditation of a person in an event, or None."""
    return AcreditacionEvento.objects.filter(
        persona=persona, evento=evento
    ).first()


# ── Tests: the pass as a source of fiesta access ────────────────────────────


@pytest.mark.django_db
def test_un_beneficiario_de_pase_recibe_acceso_a_fiesta(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a PAID pass purchase
    WHEN:  the buyer assigns a person to a slot
    THEN:  the person gets an ACTIVE accreditation with fiesta access
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert response.status_code == 200, response.content

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion is not None
    assert acreditacion.acceso_fiesta is True
    assert acreditacion.estado == EstadoAcreditacionChoices.ACTIVA
    assert acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.AUTOMATICA


@pytest.mark.django_db
def test_el_beneficiario_de_pase_no_necesita_inscripcion_ni_cuenta(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a beneficiary WITHOUT sports registration and WITHOUT an account
    WHEN:  the buyer assigns the pass
    THEN:  the event accreditation is created anyway
    """
    settings.PASES_FIESTA_ENABLED = True
    from modules.salesianos_fest.domain.models import Inscripcion
    from modules.usuarios.domain.models import Usuario

    assert not Inscripcion.objects.filter(responsable=persona_beneficiaria_1).exists()
    assert not Usuario.objects.filter(persona_fk=persona_beneficiaria_1).exists()

    _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion is not None
    assert acreditacion.acceso_fiesta is True


@pytest.mark.django_db
def test_el_pase_no_concede_box(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a beneficiary of a pass
    WHEN:  the accreditation is computed
    THEN:  `acceso_box` is NEVER granted nor modified by the pass
    """
    settings.PASES_FIESTA_ENABLED = True

    _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion.acceso_fiesta is True
    assert acreditacion.acceso_box is None


@pytest.mark.django_db
def test_un_pase_de_una_compra_no_pagada_no_da_acceso(
    api_client, usuario_comprador, compra_pase_pendiente, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a pass purchase that is NOT paid
    WHEN:  the buyer assigns a person
    THEN:  the assignment is refused — a right is only granted over a paid pass
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _asignar(
        api_client, usuario_comprador, compra_pase_pendiente, [persona_beneficiaria_1]
    )

    assert response.status_code == 409, response.content
    assert not PaseBeneficiario.objects.exists()


@pytest.mark.django_db
def test_un_beneficiario_revocado_no_da_acceso(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person whose pass was revoked
    WHEN:  the access is recomputed
    THEN:  the effective fiesta access is gone
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    revocada = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    )
    assert revocada.status_code == 200, revocada.content

    fila = PaseBeneficiario.objects.get(persona=persona_beneficiaria_1)
    assert fila.estado == "REVOCADA"

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion.acceso_fiesta is False


# ── Tests: the precedence of the administrative overrides ────────────────────


@pytest.mark.django_db
def test_el_override_bloqueada_prevalece_sobre_el_pase(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person with a BLOCKED override and an ACTIVE pass
    WHEN:  the access is computed
    THEN:  BLOQUEADA denies: the pass does not override it
    """
    settings.PASES_FIESTA_ENABLED = True
    evento = compra_pase_pagada.evento

    acreditacion = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_beneficiaria_1,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=False,
        autorizacion_fiesta=AutorizacionFiestaChoices.BLOQUEADA,
    )

    _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is False


@pytest.mark.django_db
def test_el_override_autorizada_mantiene_el_acceso(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person with an AUTHORIZED override
    WHEN:  the pass is revoked
    THEN:  the access is kept — the override is another source
    """
    settings.PASES_FIESTA_ENABLED = True
    evento = compra_pase_pagada.evento

    AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_beneficiaria_1,
        estado=EstadoAcreditacionChoices.ACTIVA,
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTORIZADA,
    )

    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    revocada = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    )
    assert revocada.status_code == 200, revocada.content

    acreditacion = _acreditacion(persona_beneficiaria_1, evento)
    assert acreditacion.acceso_fiesta is True


# ── Tests: the pass and the sports benefit are independent sources ──────────


@pytest.mark.django_db
def test_la_revocacion_del_pase_conserva_el_beneficio_deportivo(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_con_beneficio_deportivo, settings,
):
    """
    GIVEN: a person with a PAID sports FIESTA benefit AND a pass
    WHEN:  the pass is revoked
    THEN:  the access survives — only that source was removed
    """
    settings.PASES_FIESTA_ENABLED = True
    persona = persona_con_beneficio_deportivo
    evento = compra_pase_pagada.evento

    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona]
    )
    assert asignada.status_code == 200, asignada.content

    revocada = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona
    )
    assert revocada.status_code == 200, revocada.content

    acreditacion = _acreditacion(persona, evento)
    assert acreditacion is not None
    assert acreditacion.acceso_fiesta is True


@pytest.mark.django_db
def test_el_pase_habilita_el_acceso_que_el_deporte_no_daba(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person WITHOUT any sports right
    WHEN:  the buyer assigns a pass
    THEN:  the effective access exists thanks to the pass
    """
    settings.PASES_FIESTA_ENABLED = True

    _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion.acceso_fiesta is True


# ── Tests: the gate stops enabling the access ───────────────────────────────


@pytest.mark.django_db
def test_el_qr_deja_de_habilitar_el_acceso_al_revocar_el_pase(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person with a pass whose access was revoked
    WHEN:  the QR is scanned at the gate (the FIRST scan of the day)
    THEN:  the gate DENIES the access — the effective access is gone
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    qr_token = str(acreditacion.codigo_qr)

    revocada = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    )
    assert revocada.status_code == 200, revocada.content

    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is False

    denegado = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert denegado.status_code == 200, denegado.content
    assert denegado.json()["data"]["resultado"] == "DENEGADO"


@pytest.mark.django_db
def test_la_compra_de_pases_cancelada_no_da_acceso(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a person with a pass of a purchase that is CANCELLED
    WHEN:  the access is computed
    THEN:  the cancelled purchase grants nothing
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    compra_pase_pagada.estado = EstadoCompraChoices.CANCELADA
    compra_pase_pagada.save(update_fields=["estado", "updated_at"])

    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )

    AcreditacionCoreService().sync_acreditacion_desde_compras(
        evento_id=str(compra_pase_pagada.evento_id),
        persona_id=str(persona_beneficiaria_1.id),
    )

    acreditacion = _acreditacion(persona_beneficiaria_1, compra_pase_pagada.evento)
    assert acreditacion.acceso_fiesta is False
