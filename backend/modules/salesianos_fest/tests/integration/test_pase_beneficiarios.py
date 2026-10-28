"""
Integration tests — nominative rights of a party-pass purchase (Apply 4).

What this file proves:

1. the slots are IMMUTABLE: a revoked slot stays consumed forever and is
   never restored;
2. the assignment only happens on a PAID purchase;
3. a GROUP assignment materializes one right per person, with the audit of
   the actor and the date;
4. the assignment is OWNER-scoped: only the buyer (`Compra.responsable`)
   assigns, lists or revokes;
5. re-submitting the SAME list is IDEMPOTENT: the active rights of the batch
   are no-ops;
6. a person can hold at most ONE active pass per event, ACROSS purchases;
7. the capacity of the batch is never exceeded;
8. the beneficiary must be an EXISTING person — the API never creates one;
9. the revocation is PERMANENT and audited (actor, date, motive);
10. a right is NOT transferable: a revoked person cannot be reused in the
    same batch;
11. the database itself enforces the three guarantees (unique slot, unique
    person per batch, unique active person per event).

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json
import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.models import (
    CompraPase,
    PaseBeneficiario,
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


def _auth_delete(client, path, user, data):
    """DELETE with a JWT bearer token and a JSON body."""
    token = AccessToken.for_user(user)
    return client.delete(
        path,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    """GET with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _asignar(client, usuario, compra, personas):
    """POST the assignment of the given personas."""
    return _auth_post(
        client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra.id)),
        usuario,
        {"beneficiario_ids": [str(persona.id) for persona in personas]},
    )


def _revocar(client, usuario, compra, persona, motivo="Motivo de prueba"):
    """DELETE the right of the given persona."""
    return _auth_delete(
        client,
        f"{RUTA_BENEFICIARIOS.format(compra_id=str(compra.id))}/{persona.id}",
        usuario,
        {"motivo": motivo},
    )


def _beneficiarios(compra):
    """The beneficiary rows of a purchase, ordered by slot."""
    linea = CompraPase.objects.get(compra_id=compra.id)
    return list(
        PaseBeneficiario.objects
        .filter(compra_pase_id=linea.id)
        .select_related("persona")
        .order_by("slot")
    )


# ── Tests: asignación de grupo ───────────────────────────────────────────────


@pytest.mark.django_db
def test_asignar_beneficiarios_de_una_compra_pagada(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2,
    persona_beneficiaria_3, persona_beneficiaria_4, settings,
):
    """
    GIVEN: una compra de CUATRO pases pagada
    WHEN:  el comprador asigna cuatro personas
    THEN:  existen cuatro derechos ACTIVA, con slots 1..4 y la auditoría del
           actor y la fecha
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _asignar(
        api_client,
        usuario_comprador,
        compra_pase_pagada,
        [
            persona_beneficiaria_1,
            persona_beneficiaria_2,
            persona_beneficiaria_3,
            persona_beneficiaria_4,
        ],
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["asignados"] == 4
    assert data["ya_asignados"] == 0
    assert data["activos"] == 4
    assert data["revocados"] == 0
    assert data["slots_usados"] == 4
    assert data["slots_disponibles"] == 0
    assert len(data["beneficiarios"]) == 4

    filas = _beneficiarios(compra_pase_pagada)
    assert [fila.slot for fila in filas] == [1, 2, 3, 4]
    assert all(fila.estado == EstadoPaseBeneficiarioChoices.ACTIVA for fila in filas)
    assert all(
        fila.asignado_por_id == usuario_comprador.id for fila in filas
    )
    assert all(fila.asignado_en is not None for fila in filas)
    assert all(fila.revocado_en is None for fila in filas)


@pytest.mark.django_db
def test_asignar_beneficiarios_de_una_compra_no_pagada_es_rechazado(
    api_client, usuario_comprador, compra_pase_pendiente, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: una compra de pases que NO está pagada
    WHEN:  el comprador intenta asignar una persona
    THEN:  409 PASE_COMPRA_NO_PAGADA y ningún derecho creado
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _asignar(
        api_client, usuario_comprador, compra_pase_pendiente, [persona_beneficiaria_1]
    )

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "PASE_COMPRA_NO_PAGADA"
    assert PaseBeneficiario.objects.count() == 0


@pytest.mark.django_db
def test_asignar_beneficiarios_de_otra_compra_es_rechazado(
    api_client, usuario_comprador, usuario_ajeno, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: una compra de pases de OTRO comprador
    WHEN:  un tercero intenta asignar una persona
    THEN:  403 — la propiedad del lote NO se relaja
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _asignar(
        api_client, usuario_ajeno, compra_pase_pagada, [persona_beneficiaria_1]
    )

    assert response.status_code == 403, response.content
    assert PaseBeneficiario.objects.count() == 0


@pytest.mark.django_db
def test_asignar_beneficiarios_sin_autenticacion_es_rechazado(
    api_client, compra_pase_pagada, persona_beneficiaria_1, settings
):
    """
    GIVEN: un llamante anónimo
    WHEN:  POST /api/pases/compras/{id}/beneficiarios
    THEN:  401 y ningún derecho creado
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.post(
        RUTA_BENEFICIARIOS.format(compra_id=str(compra_pase_pagada.id)),
        data=json.dumps({"beneficiario_ids": [str(persona_beneficiaria_1.id)]}),
        content_type="application/json",
    )

    assert response.status_code == 401, response.content
    assert PaseBeneficiario.objects.count() == 0


@pytest.mark.django_db
def test_asignar_beneficiarios_con_una_persona_inexistente_es_rechazado(
    api_client, usuario_comprador, compra_pase_pagada, settings
):
    """
    GIVEN: un identificador que NO corresponde a una Persona existente
    WHEN:  el comprador intenta asignarlo
    THEN:  404 PASE_BENEFICIARIO_NO_ENCONTRADO y ningún derecho creado
            (la API nunca crea personas)
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra_pase_pagada.id)),
        usuario_comprador,
        {"beneficiario_ids": [str(uuid.uuid4())]},
    )

    assert response.status_code == 404, response.content
    assert response.json()["error"]["code"] == "PASE_BENEFICIARIO_NO_ENCONTRADO"
    assert PaseBeneficiario.objects.count() == 0


@pytest.mark.django_db
def test_asignar_beneficiarios_es_idempotente(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2, settings,
):
    """
    GIVEN: una compra con dos personas ya asignadas
    WHEN:  el comprador reenvía la MISMA lista
    THEN:  200 con ya_asignados=2, asignados=0 y las mismas dos filas
    """
    settings.PASES_FIESTA_ENABLED = True
    personas = [persona_beneficiaria_1, persona_beneficiaria_2]

    primera = _asignar(api_client, usuario_comprador, compra_pase_pagada, personas)
    assert primera.status_code == 200, primera.content

    segunda = _asignar(api_client, usuario_comprador, compra_pase_pagada, personas)

    assert segunda.status_code == 200, segunda.content
    data = segunda.json()["data"]
    assert data["asignados"] == 0
    assert data["ya_asignados"] == 2
    assert data["activos"] == 2
    assert PaseBeneficiario.objects.count() == 2


@pytest.mark.django_db
def test_asignar_beneficiarios_rechaza_a_una_persona_con_pase_activo_en_otra_compra(
    api_client, usuario_comprador, compra_pase_pagada, compra_pase_pagada_otro_lote,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: una persona que ya tiene un pase ACTIVO en OTRA compra del evento
    WHEN:  el comprador intenta asignarle un pase de este lote
    THEN:  409 PASE_BENEFICIARIO_DUPLICADO — como máximo un pase activo por
            persona y evento, entre todas las compras
    """
    settings.PASES_FIESTA_ENABLED = True

    primera = _asignar(
        api_client, usuario_comprador, compra_pase_pagada_otro_lote,
        [persona_beneficiaria_1],
    )
    assert primera.status_code == 200, primera.content

    segunda = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    assert segunda.status_code == 409, segunda.content
    assert segunda.json()["error"]["code"] == "PASE_BENEFICIARIO_DUPLICADO"
    assert PaseBeneficiario.objects.count() == 1


@pytest.mark.django_db
def test_asignar_beneficiarios_rechaza_exceso_de_slots(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2,
    persona_beneficiaria_3, persona_beneficiaria_4,
    persona_beneficiaria_5, settings,
):
    """
    GIVEN: un lote de CUATRO pases con tres personas ya asignadas
    WHEN:  se asignan DOS personas más
    THEN:  409 PASE_BENEFICIARIOS_EXCEDIDOS y no se excede la capacidad
    """
    settings.PASES_FIESTA_ENABLED = True

    primera = _asignar(
        api_client, usuario_comprador, compra_pase_pagada,
        [
            persona_beneficiaria_1,
            persona_beneficiaria_2,
            persona_beneficiaria_3,
        ],
    )
    assert primera.status_code == 200, primera.content

    segunda = _asignar(
        api_client, usuario_comprador, compra_pase_pagada,
        [persona_beneficiaria_4, persona_beneficiaria_5],
    )

    assert segunda.status_code == 409, segunda.content
    assert segunda.json()["error"]["code"] == "PASE_BENEFICIARIOS_EXCEDIDOS"
    assert PaseBeneficiario.objects.count() == 3


# ── Tests: revocación permanente ─────────────────────────────────────────────


@pytest.mark.django_db
def test_revocar_beneficiario_es_permanente_y_auditado(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: una persona con un pase ACTIVO
    WHEN:  el comprador revoca su pase con un motivo
    THEN:  el derecho queda REVOCADA con actor, fecha y motivo
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    response = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
        motivo="La persona no asistió",
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["estado"] == EstadoPaseBeneficiarioChoices.REVOCADA
    assert data["ya_revocado"] is False
    assert data["revocado_en"] is not None
    assert data["activos"] == 0
    assert data["revocados"] == 1
    # El slot queda CONSUMIDO: no se restaura.
    assert data["slots_usados"] == 1
    assert data["slots_disponibles"] == 3

    fila = PaseBeneficiario.objects.get(persona=persona_beneficiaria_1)
    assert fila.estado == EstadoPaseBeneficiarioChoices.REVOCADA
    assert fila.revocado_por_id == usuario_comprador.id
    assert fila.revocado_en is not None
    assert fila.motivo_revocacion == "La persona no asistió"


@pytest.mark.django_db
def test_revocar_beneficiario_es_idempotente(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: un derecho ya revocado
    WHEN:  el comprador lo revoca OTRA vez con otro motivo
    THEN:  200 con ya_revocado=True y el PRIMER motivo se conserva
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content
    assert _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
        motivo="Primer motivo",
    ).status_code == 200

    segunda = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
        motivo="Segundo motivo",
    )

    assert segunda.status_code == 200, segunda.content
    assert segunda.json()["data"]["ya_revocado"] is True

    fila = PaseBeneficiario.objects.get(persona=persona_beneficiaria_1)
    assert fila.motivo_revocacion == "Primer motivo"


@pytest.mark.django_db
def test_la_revocacion_no_libera_el_slot(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2,
    persona_beneficiaria_3, persona_beneficiaria_4,
    persona_beneficiaria_5, settings,
):
    """
    GIVEN: un lote de cuatro pases con las cuatro personas asignadas
    WHEN:  se revoca un pase y se intenta asignar otra persona
    THEN:  el slot revocado NO se restaura: no hay slots disponibles
    """
    settings.PASES_FIESTA_ENABLED = True
    personas = [
        persona_beneficiaria_1,
        persona_beneficiaria_2,
        persona_beneficiaria_3,
        persona_beneficiaria_4,
    ]
    asignada = _asignar(api_client, usuario_comprador, compra_pase_pagada, personas)
    assert asignada.status_code == 200, asignada.content

    assert _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    ).status_code == 200

    extra = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_5]
    )

    assert extra.status_code == 409, extra.content
    assert extra.json()["error"]["code"] == "PASE_BENEFICIARIOS_EXCEDIDOS"
    assert PaseBeneficiario.objects.count() == 4


@pytest.mark.django_db
def test_el_pase_revocado_no_se_reutiliza_en_el_mismo_lote(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    persona_beneficiaria_2, settings,
):
    """
    GIVEN: una persona cuyo pase fue revocado en este lote
    WHEN:  el comprador intenta asignarle OTRO pase del mismo lote
    THEN:  409 PASE_NO_TRANSFERIBLE — un pase pagado no se transfiere
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content
    assert _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    ).status_code == 200

    reuso = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )

    assert reuso.status_code == 409, reuso.content
    assert reuso.json()["error"]["code"] == "PASE_NO_TRANSFERIBLE"
    assert PaseBeneficiario.objects.count() == 1


@pytest.mark.django_db
def test_revocar_beneficiario_de_una_persona_sin_derecho_es_rechazado(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: una persona que NO tiene derecho en el lote
    WHEN:  el comprador intenta revocar su pase
    THEN:  404 PASE_BENEFICIARIO_NO_ENCONTRADO
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    )

    assert response.status_code == 404, response.content
    assert response.json()["error"]["code"] == "PASE_BENEFICIARIO_NO_ENCONTRADO"


@pytest.mark.django_db
def test_revocar_beneficiario_de_otra_compra_es_rechazado(
    api_client, usuario_comprador, usuario_ajeno, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: una compra de pases de OTRO comprador
    WHEN:  un tercero intenta revocar un pase
    THEN:  403 — la propiedad del lote NO se relaja
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    response = _revocar(
        api_client, usuario_ajeno, compra_pase_pagada, persona_beneficiaria_1
    )

    assert response.status_code == 403, response.content
    assert PaseBeneficiario.objects.filter(
        estado=EstadoPaseBeneficiarioChoices.ACTIVA
    ).count() == 1


# ── Tests: listado y conteos inmutables ──────────────────────────────────────


@pytest.mark.django_db
def test_listar_beneficiarios_devuelve_los_conteos_inmutables(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2, settings,
):
    """
    GIVEN: un lote con dos personas asignadas y una revocada
    WHEN:  el comprador lista los beneficiarios
    THEN:  los conteos separan activos y revocados, y los slots usados
            incluyen el revocado (nunca se restaura)
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada,
        [persona_beneficiaria_1, persona_beneficiaria_2],
    )
    assert asignada.status_code == 200, asignada.content
    assert _revocar(
        api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1
    ).status_code == 200

    response = _auth_get(
        api_client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra_pase_pagada.id)),
        usuario_comprador,
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["cantidad_pases"] == 4
    assert data["activos"] == 1
    assert data["revocados"] == 1
    assert data["slots_usados"] == 2
    assert data["slots_disponibles"] == 2
    assert len(data["beneficiarios"]) == 2
    assert data["beneficiarios"][0]["slot"] == 1
    assert data["beneficiarios"][0]["estado"] == EstadoPaseBeneficiarioChoices.REVOCADA
    assert data["beneficiarios"][0]["motivo_revocacion"]
    assert data["beneficiarios"][1]["slot"] == 2
    assert data["beneficiarios"][1]["estado"] == EstadoPaseBeneficiarioChoices.ACTIVA


@pytest.mark.django_db
def test_listar_beneficiarios_de_otra_compra_es_rechazado(
    api_client, usuario_comprador, usuario_ajeno, compra_pase_pagada, settings
):
    """
    GIVEN: una compra de pases de OTRO comprador
    WHEN:  un tercero intenta listar los beneficiarios
    THEN:  403
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_get(
        api_client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra_pase_pagada.id)),
        usuario_ajeno,
    )

    assert response.status_code == 403, response.content


@pytest.mark.django_db
def test_la_lectura_de_la_compra_refleja_los_beneficiarios(
    api_client, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, persona_beneficiaria_2, settings,
):
    """
    GIVEN: un lote con dos personas asignadas
    WHEN:  el comprador lee la compra
    THEN:  los conteos de beneficiarios reflejan la realidad
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada,
        [persona_beneficiaria_1, persona_beneficiaria_2],
    )
    assert asignada.status_code == 200, asignada.content

    response = _auth_get(
        api_client,
        f"/api/pases/compras/{compra_pase_pagada.id}",
        usuario_comprador,
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["beneficiarios_asignados"] == 2
    assert data["beneficiarios_pendientes"] == 2


# ── Tests: las garantías de la base de datos ─────────────────────────────────


@pytest.mark.django_db
def test_la_base_de_datos_no_permite_reutilizar_un_slot(
    db, usuario_comprador, pase_fiesta, persona_beneficiaria_1,
    persona_beneficiaria_2,
):
    """
    GIVEN: un lote con un beneficiario en el slot 1
    WHEN:  la base de datos recibe otro beneficiario en el MISMO slot
    THEN:  lo rechaza — el slot es inmutable, aunque el derecho se revoque
    """
    from modules.commerce.domain.models import Compra

    compra = Compra.objects.create(
        responsable=usuario_comprador.persona_fk,
        descripcion="Compra de pases - slot",
        referencia_externa="PASE-SLOT",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    linea = CompraPase.objects.create(
        compra=compra,
        pase=pase_fiesta,
        evento=pase_fiesta.evento,
        cantidad=2,
        precio_unitario=Decimal("25.00"),
        total=Decimal("50.00"),
    )
    PaseBeneficiario.objects.create(
        compra_pase=linea,
        evento=pase_fiesta.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaseBeneficiario.objects.create(
                compra_pase=linea,
                evento=pase_fiesta.evento,
                persona=persona_beneficiaria_2,
                slot=1,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                asignado_por=usuario_comprador,
            )


@pytest.mark.django_db
def test_la_base_de_datos_no_permite_reutilizar_una_persona_en_el_mismo_lote(
    db, usuario_comprador, pase_fiesta, persona_beneficiaria_1,
):
    """
    GIVEN: un lote con una persona en el slot 1
    WHEN:  la base de datos recibe esa MISMA persona en otro slot
    THEN:  lo rechaza — la persona no se reutiliza dentro del lote
    """
    from modules.commerce.domain.models import Compra

    compra = Compra.objects.create(
        responsable=usuario_comprador.persona_fk,
        descripcion="Compra de pases - persona",
        referencia_externa="PASE-PERSONA",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    linea = CompraPase.objects.create(
        compra=compra,
        pase=pase_fiesta,
        evento=pase_fiesta.evento,
        cantidad=2,
        precio_unitario=Decimal("25.00"),
        total=Decimal("50.00"),
    )
    PaseBeneficiario.objects.create(
        compra_pase=linea,
        evento=pase_fiesta.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaseBeneficiario.objects.create(
                compra_pase=linea,
                evento=pase_fiesta.evento,
                persona=persona_beneficiaria_1,
                slot=2,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                asignado_por=usuario_comprador,
            )


@pytest.mark.django_db
def test_la_base_de_datos_no_permite_dos_pases_activos_de_una_persona_en_el_evento(
    db, usuario_comprador, pase_fiesta, persona_beneficiaria_1,
):
    """
    GIVEN: una persona con un pase ACTIVO en un lote del evento
    WHEN:  la base de datos recibe otro pase ACTIVO de la misma persona en
           otro lote del MISMO evento
    THEN:  lo rechaza — como máximo un pase activo por persona y evento
    """
    from modules.commerce.domain.models import Compra

    compras = []
    for marca in ("A", "B"):
        compra = Compra.objects.create(
            responsable=usuario_comprador.persona_fk,
            descripcion=f"Compra de pases - {marca}",
            referencia_externa=f"PASE-{marca}",
            total=Decimal("25.00"),
            estado=EstadoCompraChoices.PAGADA,
        )
        compras.append(
            CompraPase.objects.create(
                compra=compra,
                pase=pase_fiesta,
                evento=pase_fiesta.evento,
                cantidad=1,
                precio_unitario=Decimal("25.00"),
                total=Decimal("25.00"),
            )
        )

    PaseBeneficiario.objects.create(
        compra_pase=compras[0],
        evento=pase_fiesta.evento,
        persona=persona_beneficiaria_1,
        slot=1,
        estado=EstadoPaseBeneficiarioChoices.ACTIVA,
        asignado_por=usuario_comprador,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            PaseBeneficiario.objects.create(
                compra_pase=compras[1],
                evento=pase_fiesta.evento,
                persona=persona_beneficiaria_1,
                slot=1,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                asignado_por=usuario_comprador,
            )
