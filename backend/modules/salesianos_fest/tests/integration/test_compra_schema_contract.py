"""
Focused integration tests for the Compra API schema contract (Batch 5).

Tests the stable FEST client contract:
- compra_id, orden_pago_id, tipo, cantidad, precio_unitario, total, estado
- metadata is NOT exposed in purchase endpoint responses (OrdenPagoOut, CompraDetailOut)

Also tests:
- CompraPresenter.present_detail output structure
- CompraCreateOut output structure
- IniciarPagoOut output structure
- the public self-settlement route has NO output schema anymore
- metadata NOT in OrdenPagoOut (pagos endpoint)
"""
import uuid
import json

import pytest
from decimal import Decimal

from django.test import Client
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    Inscripcion,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    EstadoInscripcionChoices,
    TipoCompraChoices,
    EstadoCompraChoices,
)
from modules.salesianos_fest.presentation.schemas.compra_schemas import (
    CompraCreateOut,
    CompraDetailOut,
    CompraListOut,
    IniciarPagoOut,
)
from modules.pagos.presentation.schemas.pago_schema import OrdenPagoOut


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client for async controllers."""
    return Client()


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=pytest.importorskip("datetime").date(2026, 11, 15),
        fecha_fin=pytest.importorskip("datetime").date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def promocion_junior(db):
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def paquete_reencuentro(db, evento, disciplina_futbol):
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=pytest.importorskip("datetime").date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion_base(db, evento, persona, paquete_reencuentro, promocion_junior):
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None, content_type="application/json"):
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=data,
        content_type=content_type,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


# ── Tests: Schema field contract ─────────────────────────────────────────────

@pytest.mark.django_db
def test_compra_create_out_has_stable_contract_fields(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user creates a Compra via POST /api/compras/
    WHEN:  Inspecting the response data
    THEN:  The response contains all stable FEST contract fields:
           compra_id, orden_pago_id, tipo, cantidad, precio_unitario, total, estado.
           metadata is NOT present.
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Stable FEST contract fields
    assert "compra_id" in data
    assert "orden_pago_id" in data
    assert data["tipo"] == "INICIAL"
    assert data["cantidad"] == 10
    assert Decimal(data["precio_unitario"]) == Decimal("50.00")
    assert Decimal(data["total"]) == Decimal("500.00")
    assert data["estado"] == "PENDIENTE"

    # metadata must NOT be in the response
    assert "metadata" not in data


@pytest.mark.django_db
def test_compra_detail_out_has_stable_contract_fields(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user retrieves a Compra via GET /api/compras/{id}/
    WHEN:  Inspecting the response data
    THEN:  The response contains all stable FEST contract fields.
           metadata is NOT present. orden_pago_id is present but not the full object.
    """
    # Create a Compra first
    create_payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    create_resp = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(create_payload),
    )
    assert create_resp.status_code == 200
    compra_id = create_resp.json()["data"]["compra_id"]

    # Get the detail
    response = _auth_get(api_client, f"/api/compras/{compra_id}", usuario_con_persona)
    assert response.status_code == 200
    data = response.json()["data"]

    # Stable FEST contract fields
    assert data["id"] == compra_id
    assert "orden_pago_id" in data
    assert data["tipo"] == "INICIAL"
    assert data["cantidad"] == 10
    assert Decimal(data["precio_unitario"]) == Decimal("50.00")
    assert Decimal(data["total"]) == Decimal("500.00")
    assert data["estado"] == "PENDIENTE"
    assert "created_at" in data

    # metadata must NOT be present
    assert "metadata" not in data


@pytest.mark.django_db
def test_compra_detail_out_orden_pago_id_is_scalar_not_object(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user retrieves a Compra detail
    WHEN:  Inspecting the orden_pago_id field
    THEN:  orden_pago_id is a string UUID, NOT a nested object.
           No 'metadata' key anywhere in the response.
    """
    create_payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    create_resp = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(create_payload),
    )
    assert create_resp.status_code == 200
    compra_id = create_resp.json()["data"]["compra_id"]

    response = _auth_get(api_client, f"/api/compras/{compra_id}", usuario_con_persona)
    data = response.json()["data"]

    # orden_pago_id is a string UUID, not a dict
    assert isinstance(data["orden_pago_id"], str)
    # Should be a valid UUID format
    uuid.UUID(data["orden_pago_id"])
    # Should NOT be a dict with metadata
    assert not isinstance(data["orden_pago_id"], dict)


@pytest.mark.django_db
def test_compra_list_out_compras_have_stable_contract(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user lists compras for an inscripcion
    WHEN:  Inspecting the response
    THEN:  Each compra in the list has stable contract fields.
           No metadata exposed.
    """
    # Create two compras
    for tipo, cantidad in [("INICIAL", 10), ("AMPLIACION", 5)]:
        payload = {
            "inscripcion_id": str(inscripcion_base.id),
            "tipo": tipo,
            "cantidad": cantidad,
        }
        resp = _auth_post(api_client, "/api/compras/", usuario_con_persona, data=json.dumps(payload))
        assert resp.status_code == 200

    response = _auth_get(
        api_client,
        f"/api/compras/inscripciones/{inscripcion_base.id}/compras",
        usuario_con_persona,
    )
    assert response.status_code == 200
    compras = response.json()["data"]["compras"]

    assert len(compras) == 2
    for compra in compras:
        # All stable contract fields present
        assert "id" in compra
        assert "orden_pago_id" in compra
        assert "tipo" in compra
        assert "cantidad" in compra
        assert "precio_unitario" in compra
        assert "total" in compra
        assert "estado" in compra
        # metadata NOT present
        assert "metadata" not in compra


# ── Tests: OrdenPagoOut — metadata NOT exposed ────────────────────────────────

def test_orden_pago_out_schema_excludes_metadata():
    """
    GIVEN: OrdenPagoOut schema definition
    WHEN:  Inspecting the schema fields
    THEN:  metadata is NOT a field in the schema.
    """
    fields = set(OrdenPagoOut.model_fields.keys())
    assert "metadata" not in fields
    # Expected fields: id, numero, monto_total, moneda, estado, pagada_en,
    # expires_at, descripcion, referencia_externa, created_at
    expected = {"id", "numero", "monto_total", "moneda", "estado",
                "pagada_en", "expires_at", "descripcion", "referencia_externa", "created_at"}
    assert fields == expected


def test_compra_create_out_schema_excludes_metadata():
    """
    GIVEN: CompraCreateOut schema definition
    WHEN:  Inspecting the schema fields
    THEN:  metadata is NOT a field in the schema.
    """
    fields = set(CompraCreateOut.model_fields.keys())
    assert "metadata" not in fields


def test_compra_detail_out_schema_excludes_metadata():
    """
    GIVEN: CompraDetailOut schema definition
    WHEN:  Inspecting the schema fields
    THEN:  metadata is NOT a field in the schema.
    """
    fields = set(CompraDetailOut.model_fields.keys())
    assert "metadata" not in fields


def test_iniciar_pago_out_schema_excludes_metadata():
    """
    GIVEN: IniciarPagoOut schema definition
    WHEN:  Inspecting the schema fields
    THEN:  metadata is NOT a field in the schema.
    """
    fields = set(IniciarPagoOut.model_fields.keys())
    assert "metadata" not in fields


def test_la_autoliquidacion_publica_no_tiene_esquema():
    """
    GIVEN: the purchase schemas of the module
    WHEN:  Inspecting the module of the presentation layer
    THEN:  there is NO `ConfirmarPagoOut`: the public self-settlement route
           was removed, so its wrapper does not exist anymore.
    """
    import modules.salesianos_fest.presentation.schemas.compra_schemas as esquema

    assert not hasattr(esquema, "ConfirmarPagoOut")


# ── Tests: Ampliacion contract ─────────────────────────────────────────────

@pytest.mark.django_db
def test_ampliacion_response_has_stable_contract(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user creates an AMPLIACION
    WHEN:  Inspecting the response
    THEN:  AMPLIACION response has same stable contract fields as INICIAL.
           metadata is NOT present.
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "AMPLIACION",
        "cantidad": 5,
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Same stable contract
    assert data["tipo"] == "AMPLIACION"
    assert data["cantidad"] == 5
    assert Decimal(data["precio_unitario"]) == Decimal("50.00")
    assert Decimal(data["total"]) == Decimal("250.00")
    assert data["estado"] == "PENDIENTE"
    assert "compra_id" in data
    assert "orden_pago_id" in data
    assert "metadata" not in data
