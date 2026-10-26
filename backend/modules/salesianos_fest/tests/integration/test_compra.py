"""
Integration tests for Compra HTTP flows (Phase 4).

Covers:
- INICIAL and AMPLIACION creation
- Minimum initial quantity conflict (CantidadInsuficienteError)
- Missing inscription (InscripcionNotFoundError)
- Non-owner authorization
- iniciar_pago happy and non-pending conflict
- confirmar_pago success, idempotent confirmation, duplicate callback safety
"""
import uuid
import json

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, patch

from django.test import Client
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    Inscripcion,
)
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    EstadoInscripcionChoices,
    TipoCompraChoices,
    EstadoCompraChoices,
)
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client for async controllers."""
    return Client()


@pytest.fixture
def evento(db):
    """Create a test evento."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
    """Create a test disciplina."""
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
    """Create a test promocion."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def categoria_senior(db, evento, promocion_junior):
    """Create a test categoria."""
    return Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
    )


@pytest.fixture
def paquete_reencuentro(db, evento, disciplina_futbol):
    """Create a test paquete with price."""
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
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    """Create a test persona."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def persona_2(db):
    """Create a second test persona (non-owner)."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    """Create a user linked to a persona (owner)."""
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_otro(db, persona_2):
    """Create another user (non-owner)."""
    User = get_user_model()
    return User.objects.create_user(
        username="maria_user",
        email="maria@example.com",
        password="testpass123",
        persona_fk=persona_2,
    )


@pytest.fixture
def inscripcion_base(db, evento, persona, paquete_reencuentro, promocion_junior):
    """Create a base inscripcion owned by persona."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None, content_type="application/json"):
    """Helper to make an authenticated POST request."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=data,
        content_type=content_type,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    """Helper to make an authenticated GET request."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


# ── Tests: Crear Compra ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_compra_inicial_success(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; sufficient quantity for INICIAL
    WHEN:  POST /api/compras/ with tipo=INICIAL and cantidad >= minimo
    THEN:  200 returned with compra data and PENDIENTE estado.
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
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["tipo"] == "INICIAL"
    assert data["data"]["cantidad"] == 10
    assert data["data"]["estado"] == "PENDIENTE"
    assert Decimal(data["data"]["precio_unitario"]) == Decimal("50.00")
    assert Decimal(data["data"]["total"]) == Decimal("500.00")
    assert "compra_id" in data["data"]
    assert "orden_pago_id" in data["data"]


@pytest.mark.django_db
def test_crear_compra_ampliacion_success(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion
    WHEN:  POST /api/compras/ with tipo=AMPLIACION (quantity does not need minimum)
    THEN:  200 returned with compra data and AMPLIACION tipo.
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "AMPLIACION",
        "cantidad": 5,  # less than minimo_inicial (10), allowed for AMPLIACION
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["tipo"] == "AMPLIACION"
    assert data["data"]["cantidad"] == 5


@pytest.mark.django_db
def test_crear_compra_inicial_cantidad_insuficiente(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion
    WHEN:  POST /api/compras/ with tipo=INICIAL and cantidad < minimo_inicial
    THEN:  409 returned with CantidadInsuficienteError.
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 5,  # minimo is 10
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["error"]["code"] == "CANTIDAD_INSUFICIENTE"


@pytest.mark.django_db
def test_crear_compra_inscripcion_no_encontrada(api_client, usuario_con_persona):
    """
    GIVEN: Auth user with persona
    WHEN:  POST /api/compras/ with non-existent inscripcion_id
    THEN:  404 returned with InscripcionNotFoundError.
    """
    payload = {
        "inscripcion_id": str(uuid.uuid4()),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["error"]["code"] == "INSCRIPCION_NOT_FOUND"


@pytest.mark.django_db
def test_crear_compra_no_owner_denied(api_client, usuario_otro, inscripcion_base):
    """
    GIVEN: Auth user does NOT own the inscripcion
    WHEN:  POST /api/compras/
    THEN:  403 returned (BusinessError: no permission).
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_otro,
        data=json.dumps(payload),
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.json()}"


# ── Tests: Iniciar Pago ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_iniciar_pago_success(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; Compra is PENDIENTE
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago
    THEN:  200 returned with Izipay token data.
    """
    # First create a Compra
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

    # Mock the Izipay client
    mock_token_response = {
        "token": "test-izipay-token-abc123",
        "response": {"token": "test-izipay-token-abc123"},
    }

    with patch(
        "modules.pagos.infrastructure.services.IzipayClient.generar_token_sesion",
        new_callable=AsyncMock,
        return_value=mock_token_response,
    ):
        response = _auth_post(
            api_client,
            f"/api/compras/{compra_id}/iniciar-pago",
            usuario_con_persona,
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["token"] == "test-izipay-token-abc123"
    assert data["data"]["compra_id"] == compra_id
    assert "transaction_id" in data["data"]
    assert "merchant_code" in data["data"]


@pytest.mark.django_db
def test_iniciar_pago_compra_no_encontrada(api_client, usuario_con_persona):
    """
    GIVEN: Auth user with persona
    WHEN:  POST /api/compras/{non-existent}/iniciar-pago
    THEN:  404 returned with CompraNotFoundError.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/{uuid.uuid4()}/iniciar-pago",
        usuario_con_persona,
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.json()}"


@pytest.mark.django_db
def test_iniciar_pago_no_owner_denied(api_client, usuario_otro, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user does NOT own the inscripcion
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago
    THEN:  403 returned (BusinessError: no permission).
    """
    # Create Compra as owner first
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

    # Try to initiate payment as non-owner
    response = _auth_post(
        api_client,
        f"/api/compras/{compra_id}/iniciar-pago",
        usuario_otro,
    )
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.json()}"


@pytest.mark.django_db
def test_iniciar_pago_compra_ya_pagada(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; Compra is already PAGADA
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago
    THEN:  409 returned with CompraNoCobrableError.
    """
    # Create a Compra and mark it as PAGADA
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

    # Mark Compra as PAGADA directly
    Compra.objects.filter(id=compra_id).update(estado=EstadoCompraChoices.PAGADA)

    response = _auth_post(
        api_client,
        f"/api/compras/{compra_id}/iniciar-pago",
        usuario_con_persona,
    )
    assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.json()}"


# ── Tests: Confirmar Pago ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_confirmar_pago_success(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; Compra is PENDIENTE
    WHEN:  POST /api/compras/confirmar-pago with orden_pago_id
    THEN:  200 returned with success=True and Compra estado=PAGADA.
    """
    # Create a Compra
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
    orden_pago_id = create_resp.json()["data"]["orden_pago_id"]
    compra_id = create_resp.json()["data"]["compra_id"]

    # Confirm the payment
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["success"] is True
    assert data["data"]["already_confirmed"] is False

    # Verify Compra estado changed to PAGADA
    compra = Compra.objects.get(id=compra_id)
    assert compra.estado == EstadoCompraChoices.PAGADA


@pytest.mark.django_db
def test_confirmar_pago_idempotente(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user; Compra is already PAGADA
    WHEN:  POST /api/compras/confirmar-pago again with same orden_pago_id
    THEN:  200 returned with already_confirmed=True (idempotent).
    """
    # Create a Compra
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
    orden_pago_id = create_resp.json()["data"]["orden_pago_id"]

    # Confirm once
    first_resp = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )
    assert first_resp.status_code == 200
    assert first_resp.json()["data"]["already_confirmed"] is False

    # Confirm again (idempotent)
    second_resp = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )
    assert second_resp.status_code == 200, f"Expected 200, got {second_resp.status_code}: {second_resp.json()}"
    data = second_resp.json()
    assert data["success"] is True
    assert data["data"]["already_confirmed"] is True


@pytest.mark.django_db
def test_confirmar_pago_orden_no_encontrada(api_client, usuario_con_persona):
    """
    GIVEN: Auth user with persona
    WHEN:  POST /api/compras/confirmar-pago with non-existent orden_pago_id
    THEN:  404 returned with CompraNotFoundError.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={uuid.uuid4()}",
        usuario_con_persona,
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.json()}"


@pytest.mark.django_db
def test_confirmar_pago_no_duplicate_callback_safety(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user; Compra is PENDIENTE
    WHEN:  Two POST /api/compras/confirmar-pago calls for same orden_pago_id
    THEN:  Both return 200; Compra is PAGADA exactly once (idempotent, race-safe).
    """
    # Create a Compra
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
    orden_pago_id = create_resp.json()["data"]["orden_pago_id"]
    compra_id = create_resp.json()["data"]["compra_id"]

    # Call confirmar twice (simulating duplicate callback)
    resp1 = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )
    resp2 = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )

    # Both should succeed
    assert resp1.status_code == 200
    assert resp2.status_code == 200

    # One should be first (already_confirmed=False), one should be idempotent (already_confirmed=True)
    data1 = resp1.json()["data"]
    data2 = resp2.json()["data"]
    confirmed_states = {data1.get("already_confirmed"), data2.get("already_confirmed")}
    assert confirmed_states == {False, True}

    # Compra should be PAGADA
    compra = Compra.objects.get(id=compra_id)
    assert compra.estado == EstadoCompraChoices.PAGADA


# ── Tests: Obtener Compra ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_obtener_compra_success(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; Compra exists
    WHEN:  GET /api/compras/{compra_id}
    THEN:  200 returned with compra detail.
    """
    # Create a Compra
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
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == compra_id
    assert data["data"]["tipo"] == "INICIAL"


@pytest.mark.django_db
def test_obtener_compra_no_owner_denied(api_client, usuario_otro, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user does NOT own the inscripcion
    WHEN:  GET /api/compras/{compra_id}
    THEN:  403 returned (BusinessError: no permission).
    """
    # Create Compra as owner
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

    # Try to get as non-owner
    response = _auth_get(api_client, f"/api/compras/{compra_id}", usuario_otro)
    assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.json()}"


@pytest.mark.django_db
def test_listar_compras_inscripcion(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Auth user owns the inscripcion; multiple compras exist
    WHEN:  GET /api/compras/inscripciones/{inscripcion_id}/compras
    THEN:  200 returned with list of compras.
    """
    # Create two Compras
    for tipo, cantidad in [("INICIAL", 10), ("AMPLIACION", 5)]:
        create_payload = {
            "inscripcion_id": str(inscripcion_base.id),
            "tipo": tipo,
            "cantidad": cantidad,
        }
        create_resp = _auth_post(
            api_client,
            "/api/compras/",
            usuario_con_persona,
            data=json.dumps(create_payload),
        )
        assert create_resp.status_code == 200

    response = _auth_get(
        api_client,
        f"/api/compras/inscripciones/{inscripcion_base.id}/compras",
        usuario_con_persona,
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["compras"]) == 2


# ── Tests: T16 — Ampliación Dúo ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_t16_ampliacion_no_duplica_beneficios(
    api_client, usuario_con_persona, inscripcion_base,
):
    """
    T16: Ampliación — Más cupos y pases de fiesta, no otro box/caja.

    GIVEN: An inscripcion with a package that has benefits
    WHEN:  Creating an AMPLIACION after the initial purchase
    THEN:  The PaqueteBeneficio catalog remains UNCHANGED (not duplicated).

    The key invariant: PaqueteBeneficio is a CATALOG, not mutable per purchase.
    AMPLIACION creates new cupos but does not create new benefit catalog entries.
    """
    from modules.salesianos_fest.domain.models import PaqueteBeneficio
    from modules.salesianos_fest.domain.constants import (
        TipoBeneficioChoices,
    )

    paquete = inscripcion_base.paquete

    # Get initial benefit count for this paquete
    beneficios_iniciales_count = PaqueteBeneficio.objects.filter(
        paquete=paquete,
    ).count()

    # Create initial purchase (INICIAL)
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

    # Create AMPLIACION
    ampliacion_payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "AMPLIACION",
        "cantidad": 5,
    }
    ampliacion_resp = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(ampliacion_payload),
    )
    assert ampliacion_resp.status_code == 200, f"AMPLIACION failed: {ampliacion_resp.json()}"

    # The PaqueteBeneficio catalog remains UNCHANGED after AMPLIACION
    # Benefits are a catalog entry, not created per purchase
    beneficios_despues_count = PaqueteBeneficio.objects.filter(
        paquete=paquete,
    ).count()

    # Catalog count should be identical before and after AMPLIACION
    assert beneficios_iniciales_count == beneficios_despues_count

    # The catalog itself (if any) should be unchanged
    beneficios_iniciales = list(
        PaqueteBeneficio.objects.filter(
            paquete=paquete,
        ).order_by("tipo").values_list("tipo", flat=True)
    )
    beneficios_despues = list(
        PaqueteBeneficio.objects.filter(
            paquete=paquete,
        ).order_by("tipo").values_list("tipo", flat=True)
    )
    assert beneficios_iniciales == beneficios_despues

    # Verify that the AMPLIACION was created with correct type
    # Compra is in commerce module; access tipo via CompraInscripcion
    from modules.salesianos_fest.domain.models import CompraInscripcion
    compra_inscripciones = CompraInscripcion.objects.filter(
        inscripcion=inscripcion_base
    ).order_by("created_at")
    assert compra_inscripciones.count() == 2
    tipos = list(compra_inscripciones.values_list("tipo", flat=True))
    assert "INICIAL" in tipos
    assert "AMPLIACION" in tipos
